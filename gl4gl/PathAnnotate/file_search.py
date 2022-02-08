""" Functions for generating dataframes of annotated paths """
from pathlib import Path
import re
import logging

logging.basicConfig(level="debug")

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
    return df


# TODO: make template a list of strings and load config in merged chunks to allow config mix and matching from a single file
def get_annotated_paths_df(
    config_fs_f: Path,
    runsheet: Path,
    template: str,
    root_dir: Path,
    expand_annotations: bool = True,
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

    logging.info(
        f"Loading runsheet (looking for '{SAMPLE_NAME_COL}' column): {runsheet}"
    )
    metas = _load_meta(runsheet)

    # get file and directory dataframe
    df = get_paths_df(root_dir)

    # iterate through listing and annotate based on config
    file_mapping = dict()
    for sample_name, meta in metas.items():
        print(sample_name)
        # search for each file pattern
        for file_type, config_specific in config_fs.items():
            print(f"Searching for type: {file_type}")
            pattern = config_specific["pattern"]
            annotations = config_specific["annotations"]
            search_path = pattern.format(
                sample_name=sample_name,
                sample=sample_name,
                source_name=meta.get("Source Name"),
                hybridization_assay=meta.get("Hybridization Assay Name"),
            )
            annotations["search_pattern"] = search_path
            # find matches
            try:
                df_matches = df.loc[df["relativePath"].str.match(search_path)]
            except re.error as e:
                raise ValueError(f"Bad re_pattern. Failing pattern: {search_path}")
            print(f"Found {len(df_matches)} matches with pattern '{search_path}'")
            # set annotations from config for all matching cases
            if len(df_matches):
                df.loc[df["relativePath"].str.match(search_path), "annotations"] = [
                    annotations for _ in range(len(df_matches))
                ]  # assign the annotation with a list of appropriate length
            elif config_specific.get("optional"):
                print(f"Note: no matches for {file_type}")
            else:
                raise ValueError(
                    f"No files matched when file type {file_type} set as NOT optional"
                )
    # add default annotation for all other files
    df.loc[df["annotations"] == {}, "annotations"] = [
        config_fs["DEFAULT"]["annotations"]
        for _ in range(len(df.loc[df["annotations"] == {}]))
    ]  # assign the annotation with a list of appropriate length

    if expand_annotations:
        # expand annotations into their own columns
        df_annot = pd.json_normalize(df["annotations"])
        # concat columns
        df = pd.concat([df, df_annot], axis="columns")
    return df
