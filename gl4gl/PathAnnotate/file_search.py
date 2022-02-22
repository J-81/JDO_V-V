""" Functions for generating dataframes of annotated paths """
from pathlib import Path
import re
import logging
from typing import List

import yaml
import pandas as pd


SAMPLE_NAME_COL = "sample_name"


def _load_meta(runsheet: Path) -> dict:
    """Load metadata from runsheet

    :param runsheet: A csv file containing each sample and associated metadata
    :type runsheet: Path
    :return: A nested dict with {sample_name:meta} where meta is a dictionary of meta values (e.g. paired end bool)
    :rtype: dict
    """
    logging.info(
        f"Loading runsheet (looking for '{SAMPLE_NAME_COL}' column), other columns loaded as dict 'meta': {runsheet}"
    )
    df = pd.read_csv(runsheet)
    df = df.set_index(SAMPLE_NAME_COL)
    return df.to_dict(orient="index")


def get_paths_df(
    root_dir: Path, ignore_dvc: bool = True, ignore_hidden: bool = True
) -> pd.DataFrame:
    """ Generate unannotated dataframe with all paths in the root_dir 

    :param root_dir: The directory to catalog as a dataframe
    :type root_dir: Path
    :param ignore_dvc: Filter out files ending in ".dvc" (i.e. marker files associated with the dvc tool)
    :type ignore_dvc: bool
    :param ignore_hidden: Filter out hidden directories and files
    :type ignore_hidden: bool
    :return: A dataframe with all paths, includes an empty annotations column
    :rtype: pd.DataFrame
    """
    listings = list()

    def _handle(handle: Path):
        """ Returns the necessary data about the file handle if the handle is for a file.  Otherwise recursivel iterate """
        if handle.is_file():
            listings.append(
                {
                    "fullPath": str(handle),
                    "relativePath": str(handle.relative_to(root_dir)),
                    "pathObj": handle,
                    "isDir": False,
                    "annotations": dict(),
                }
            )
        elif handle.is_dir():
            listings.append(
                {
                    "fullPath": str(handle),
                    "relativePath": str(handle.relative_to(root_dir)),
                    "pathObj": handle,
                    "isDir": True,
                    "annotations": dict(),
                }
            )
            for dir in handle.iterdir():
                _handle(dir)

    assert root_dir.is_dir(), f"root_dir: '{root_dir}' must exist and be a directory"
    _handle(root_dir)

    df = pd.DataFrame(listings)

    # filters
    if ignore_dvc:
        dvc_filter = df["pathObj"].apply(lambda path: path.suffix) == ".dvc"
        logging.info(f"Removing {sum(dvc_filter)} files ending in '.dvc'")
        df = df.loc[~dvc_filter]

    if ignore_hidden:
        hidden_filter = df["pathObj"].apply(lambda path: path.name).str.startswith(".")
        logging.info(f"Removing {sum(hidden_filter)} hidden files")
        df = df.loc[~hidden_filter]

    # reset index
    df = df.reset_index(drop=True)
    logging.info(
        f"Final unannotated dataframe has {len(df)} paths (file and directories)"
    )
    return df


def _return_updated_dict(d: dict, payload: dict) -> dict:
    """Helper function to update a copy of the dict and return the updated copy

    :param d: input dict
    :type d: dict
    :param payload: argument for updating the dict
    :type payload: dict
    :return: updated dict
    :rtype: dict
    """
    logging.debug(f"Updating {d} with {payload}")
    updated = d.copy()
    updated.update(payload)
    logging.debug(f"Updated: {updated}")
    return updated


def _get_annotations_by_key_set(config: dict, annotation_keys: List[str]) -> dict:
    """Fetches an annotation set by searching down the annotation_keys provided.
    If the key is not found, any empty annotation is returned (hence, default annotations are left as is)

    :param config: The file type specific config containing multiple annotation keys
    :type config: dict
    :param annotation_keys: The list of annotation keys to use, in order of priority
    :type annotation_keys: List[str]
    :return: a dict of the annotations pertaining to the highest priority annotation key (or an empty dict if none of the keys exist for the path_type)
    :rtype: dict
    """
    for query_key in annotation_keys:
        annotations = config.get(query_key)
        if annotations:
            logging.debug(
                f"Found matching key: {query_key} with annotations: {annotations}"
            )
            return annotations.copy()  # to ensure we don't modify the original
    # only return this is no key found
    logging.debug(f"Found no matching key, returning no annotations")
    return dict()


# TODO: fix docstring
def _compute_attributes(df: pd.DataFrame, compute_these) -> pd.DataFrame:
    filter_df_func = compute_these[0]
    # filter dataframe to requested compute target rows
    logging.debug(
        f"Running attribute compute: Filtering dataframe with {filter_df_func}"
    )
    df_filtered = filter_df_func(df)
    logging.debug(f"Targetting {len(df_filtered)} rows of total {len(df)}")

    # compute attributes with apply
    for c in compute_these[1]:
        logging.debug(
            f"Running function: {c[0][0]} with args {c[0][1]} to get columns (unformated): {c[1]}"
        )
        intermediate_result = df_filtered["pathObj"].apply(c[0][0], **c[0][1])
        logging.debug(f"Generated results: (head) {intermediate_result.head()}")

        # ensure proper column iteration (special case one column)
        target_cols = c[1] if isinstance(c[1], tuple) else tuple([c[1]])
        for i_col, unformatted_col in enumerate(target_cols):
            # set a single column attribute at a time
            # format if needed:
            if c[0][1]:
                formatted_colname = unformatted_col.format(**c[0][1])
            else:
                formatted_colname = unformatted_col
            logging.debug(f"Setting attribute column: {formatted_colname}")
            df_filtered[formatted_colname] = intermediate_result.apply(
                lambda results: results[i_col]
                if isinstance(results, tuple)
                else results
            )

    # merge results into original dataframe
    JOIN_KEY = "fullPath"
    df_only_res_plus_join_key = df_filtered[
        [c for c in df_filtered.columns if any((c not in df.columns, c == JOIN_KEY))]
    ]
    logging.debug(
        f"Merging results into main dataframe: {df_only_res_plus_join_key.columns}"
    )
    return df.merge(df_only_res_plus_join_key, on=JOIN_KEY, how="left")


# TODO: unify arguments across this and report excel generation
# TODO: make template a list of strings and load config in merged chunks to allow config mix and matching from a single file
def get_annotated_paths_df(
    config_fs_f: Path,
    runsheet: Path,
    template: str,
    root_dir: Path,
    expand_annotations: bool = True,
    drop_annotations: bool = False,
    compute_these: dict = {},
    annotations_keys: List[str] = ["GLDS_annotations"],
) -> pd.DataFrame:
    """ Generates a dataframe with each path (files and directories) as a row.  Annotations are added based on search patterns
    in a yaml configuration file.

    :param config_fs_f: A yaml file denoting the annotations to place based on regex patterns
    :type config_fs_f: Path
    :param runsheet: A csv file denoting the samples in the experiment in a column 'sample_name'
    :type runsheet: Path
    :param template: The specific sections of the yaml file to use.
    :type template: str
    :param root_dir: The directory whose contents will be cataloged
    :type root_dir: Path
    :param expand_annotations: Expands annotations from a single dict {annot_name:annot_value,...} into distinct columns [{col_name:col_value}...], defaults to True
    :type expand_annotations: bool, optional
    :param drop_annotations: Removes annotation columns before return, often used in combination with compute_these argument, defaults to False
    :type drop_annotations: bool, optional
    :param compute_these: Dictionary of additional computations to generate {"filter_df_func":{(func, args):("val1","val2")}}
    :type compute_these: bool, optional
    :param annotations_key: The annotations key names to use from the yaml file, This is an ordered list, if an annotation key does not exist the next used, defaults to ['GLDS_annotations']
    :type annotations_key: List[str], optional
    :return: A dataframe denoting all paths in the root_dir and attached annotations
    :rtype: pd.DataFrame
    """
    logging.info(f"Loading config yaml file: {config_fs_f}")
    with open(config_fs_f, "r") as f:
        config_fs = yaml.safe_load(f)

    # extract only the relevant config
    template_manufact, template_channels = template.split(":")
    config_fs = config_fs[template_manufact][template_channels]
    logging.info(f"Loaded config: {len(config_fs)} annotation keys found")

    metas = _load_meta(runsheet)

    # get file and directory dataframe
    df = get_paths_df(root_dir)

    default_annot_key = annotations_keys[0]
    # add default annotation for all files, to be merged with matching annotation
    df["annotations"] = df["annotations"].apply(
        lambda _: config_fs["DEFAULT"][
            default_annot_key
        ].copy()  # copy to make sure this isn't overwritten!
    )

    # iterate through listing and annotate based on config
    for sample_name, meta in metas.items():
        logging.info(f"Searching for files for {sample_name} with meta: {meta}")
        # search for each file pattern
        for file_type, config_specific in config_fs.items():
            pattern = config_specific["pattern"]
            annotations = _get_annotations_by_key_set(config_specific, annotations_keys)
            meta_kwargs = {key: meta.get(key) for key in meta.keys()}
            search_path = pattern.format(sample=sample_name, **meta_kwargs)

            # add annotations based on file search
            annotations["search_pattern"] = search_path
            annotations["path_type"] = file_type

            logging.info(
                f"Searching for type: {file_type} with search pattern: {search_path}"
            )
            # find matches
            try:
                df_matches = df["relativePath"].str.match(search_path)
            except re.error as e:
                raise ValueError(f"Bad re_pattern. Failing pattern: {search_path}")
            logging.info(
                f"Found {sum(df_matches)} matches with pattern '{search_path}'"
            )
            # set annotations from config for all matching cases
            if sum(df_matches):
                logging.debug(
                    f"Updating indices: {df_matches[df_matches].index.values} with annotation: {annotations}"
                )
                # note: Apply here is not assigned since dict update is inplace by nature and the return is 'None'
                df.loc[df_matches, "annotations"] = df.loc[
                    df_matches, "annotations"
                ].apply(_return_updated_dict, args=[annotations])
            elif config_specific.get("optional"):
                logging.warning(f"No matches for {file_type}")
            else:
                raise ValueError(
                    f"No files matched when file type {file_type} set as NOT optional"
                )

    if expand_annotations:
        # expand annotations into their own columns
        df_annot = pd.json_normalize(df["annotations"])
        # concat columns
        df = pd.concat([df, df_annot], axis="columns")

    # compute additional columns
    if compute_these:
        df = _compute_attributes(df, compute_these)

    return df
