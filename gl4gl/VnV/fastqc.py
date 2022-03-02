""" Checks related to output from fastQC
"""
from pathlib import Path
import logging
import sys
from typing import List

import yaml
import pandas as pd

from .custom_logging import Flag, flag_exceptions
from gl4gl import PathAnnotate
from gl4gl import VnV

# load module specific logger
log = logging.getLogger(__name__)
# load in module specific data with an adaptor that also handles kwargs and default
flag = Flag(log, {"module_info": "FastQC"})


# @flag_exceptions(flag)
def __check_expected_files_exist(
    df_paths, path_type_spec: List[tuple], meta_samples: dict = {"": None}
):
    filter_to_sample = (
        lambda sample: df_paths["pathObj"].apply(lambda p: p.name).str.contains(sample)
    )
    filter_to_path_type = lambda path_type: df_paths["path_type"] == path_type

    for path_type, expected_per_sample, sub_checkID in path_type_spec:
        flag.check = (
            f"0001-{sub_checkID}",
            f"Confirm that {path_type} files exist",
        )
        for sample in meta_samples.keys():
            # use AllSamples as entity if sample is empty
            flag.entity = (sample if sample else "AllSamples", "", "")
            # get fastq belonging to sample
            samplewise_files = df_paths.loc[
                filter_to_sample(sample) & filter_to_path_type(path_type)
            ]["pathObj"]
            flag.filepaths = set(samplewise_files)
            # flag based on number of files found
            actual_samplewise_files = len(samplewise_files)
            if actual_samplewise_files == expected_per_sample:
                flag.info(
                    f"Found expected number of {path_type} files ({expected_per_sample})",
                    extra={"flag_code": 30},
                )
            else:
                flag.info(
                    f"Improper {path_type} file count. Expected: ({expected_per_sample}). Found: ({actual_samplewise_files})",
                    extra={"flag_code": 90},
                )


def __load(root_dir: Path, runsheet: Path):
    # load Path Annotate configs from package
    config_fs_f = [
        c for c in PathAnnotate.get_configs() if c.name == "Bulk_Search_Patterns.yaml"
    ][0]

    template = [
        t
        for t in PathAnnotate.get_templates(config_fs_f)
        if t == "Bulk_RNASeq:PairedEnd"
    ][0]

    # load meta
    meta = dict()
    df_meta = pd.read_csv(runsheet)
    df_meta = df_meta.set_index("sample_name")
    log.debug(f"Columns in runsheet dataframe: {df_meta.columns}")
    for meta_value in ["paired_end", "has_ERCC", "organism"]:
        meta[meta_value] = df_meta[meta_value].unique()
        assert len(
            meta[meta_value]
        ), f"Expected constant value in runsheet column {meta_value}"
        meta[meta_value] = meta[meta_value][0]
    log.info(f"Loaded meta for dataset from runsheet: {meta}")

    # load samplewise meta
    meta_samples = df_meta.to_dict(orient="index")
    log.info(f"Loaded meta for samples")
    log.debug(f"Contents: {meta_samples}")

    # get annotated df of paths
    df_paths = PathAnnotate.get_annotated_paths_df(
        config_fs_f=config_fs_f, template=template, runsheet=runsheet, root_dir=root_dir
    )

    # get multiqc dataframe
    # note: the 00-RawData dir is appended here to limit search scope
    df_mqc = VnV.use_multiqc.get_parsed_data(
        input_f=[str(root_dir / "00-RawData")], modules=["fastqc"]
    )

    # load VnV configs from package
    config_vnv_f = [c for c in VnV.get_configs() if c.name == "Bulk_RNASeq.yaml"][0]
    with open(config_vnv_f) as f:
        vnv_config = yaml.safe_load(f)

    return meta, meta_samples, df_paths, df_mqc


# @flag_exceptions(flag)
def main(root_dir: Path, runsheet: Path):
    """ Runs VnV protocol for RNASeq 00-RawData Directory """
    meta, meta_samples, df_paths, df_mqc = __load(root_dir, runsheet)

    # set up iterable with tuples of path_type and expected number of files
    two_if_paired = 2 if meta["paired_end"] else 1

    # for general file existence checks
    # for sample wise (note supplying meta_samples)
    path_type_spec = [
        ("raw_reads", two_if_paired, "0001"),
        ("raw_reads_FastQC", two_if_paired * 2, "0002"),  # html and zip files
    ]

    __check_expected_files_exist(df_paths, path_type_spec, meta_samples)
    flag.reset()

    # now dataset wide files
    path_type_spec = [
        ("raw_read_MultiQC_Zip", 1, "0003"),
    ]

    __check_expected_files_exist(df_paths, path_type_spec)
    flag.reset()


#  __checks_on_multiqc_data(df_paths, df_mqc, meta, meta_samples)


if __name__ == "__main__":
    # TODO: convert to argparse
    main(Path(sys.argv[1]), Path(sys.argv[2]))

'''
def validate_verify(
    samples: [str],
    input_path: str,
    flagger: Flagger,
    file_mapping_substrings: dict[str, str] = {"_R1_": "forward", "_R2_": "reverse"},
):
    """ Checks fastqc files match what is expected given a set of samples.

    :param samples: sample names, should be extracted from ISA file
    :param input_path: directory containing output from fastQC
    :param file_mapping_substrings: Added by fastQC (e.g. '_raw_fastqc')
    """
    # check if html and zip files exists
    check_id = "FastQC file existence check"
    for sample in samples:
        expected_html_file = os.path.join(input_path, f"{prefix}{expected_suffix}.html")
        expected_zip_file = os.path.join(input_path, f"{prefix}{expected_suffix}.html")
        html_file_exists = os.path.isfile(expected_html_file)
        zip_file_exists = os.path.isfile(expected_zip_file)
        if not html_file_exists or not zip_file_exists:
            Flagger.flag(
                debug_message=f"Missing {expected_html_file} and/or {expected_zip_file}",
                entity=sample,
                severity=90,
                check_id="F_0001",
            )
        else:
            Flagger.flag(
                debug_message=f"Missing {expected_html_file} and/or {expected_zip_file}",
                entity=sample,
                severity=30,
                check_id="F_0001",
            )
'''
