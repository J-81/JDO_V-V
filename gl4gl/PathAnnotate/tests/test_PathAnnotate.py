import os
import logging

try:
    TEST_ASSETS_DIR = os.environ["PYTEST_ASSETS"]
except KeyError as e:
    print(
        "Pytest user needs to set env variable: 'PYTEST_ASSETS' to indicate where test assets are stored"
    )
    raise e


def tests_unannotated_df(caplog):
    caplog.set_level(logging.DEBUG)
    from gl4gl import PathAnnotate
    from pathlib import Path

    df = PathAnnotate.get_paths_df(root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-251"))
    assert len(df) == 1110  # based on dev_version3 for RNASeq pipeline output


######################################################

from gl4gl import PathAnnotate
from pathlib import Path

config_fs_f = [
    c for c in PathAnnotate.get_configs() if c.name == "Bulk_Search_Patterns.yaml"
][0]

template = [
    t for t in PathAnnotate.get_templates(config_fs_f) if t == "Bulk_RNASeq:PairedEnd"
][0]


def tests_annotated_df_default_keys(caplog):
    caplog.set_level(logging.DEBUG)

    df = PathAnnotate.get_annotated_paths_df(
        root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-251"),
        config_fs_f=config_fs_f,
        template=template,
        runsheet=Path(
            f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
        ),
    )
    assert df.shape == (1110, 10)  # based on dev_version3 for RNASeq pipeline output

    assert (
        len(df["annotations"].apply(str).unique()) > 100
    )  # this changes as the config is updated, but at least 100 unique annotations strings is a decent sign it works as expected


def tests_annotated_df_PI_annot_key_leading_list(caplog):
    caplog.set_level(logging.DEBUG)
    # and with another annotation key set
    df = PathAnnotate.get_annotated_paths_df(
        root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-251"),
        config_fs_f=config_fs_f,
        template=template,
        runsheet=Path(
            f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
        ),
        annotations_keys=[
            "PI_annotations",
            "dummy_test_annotations",
            "GLDS_annotations",
        ],
    )
    # this has an extra annotation value
    assert df.shape == (1110, 11)  # based on dev_version2 for RNASeq pipeline output
    assert (
        len(df["annotations"].apply(str).unique()) > 100
    )  # this changes as the config is updated, but at least 100 unique annotations strings is a decent sign it works as expected


def tests_annotated_df_dummy_key(caplog):
    caplog.set_level(logging.DEBUG)
    # now all 'bad' keys, this should result
    df = PathAnnotate.get_annotated_paths_df(
        root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-251"),
        config_fs_f=config_fs_f,
        template=template,
        runsheet=Path(
            f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
        ),
        annotations_keys=["dummy_test_annotations"],
    )

    # this has an extra annotation value
    assert df.shape == (1110, 8)  # based on dev_version2 for RNASeq pipeline output
    assert df["annotations"].apply(lambda annot: annot.get("Happy")).unique() == [
        "Birthday"
    ]


def test_attributed_df(caplog):
    """ This test is a proxy for md5sum table generation """
    caplog.set_level(logging.DEBUG)
    from random import randint
    import pandas as pd

    def wrap_randint(f: Path, a, b):
        return randint(a, b)

    def get_chars_in_name(f: Path, char: str, tooManyThresh: int):
        """Find {char} characters in the filename and flags if the number exceeds {tooManyThresh}

        :param f: [description]
        :type f: Path
        :param char: [description]
        :type char: str
        :param tooManyThresh: [description]
        :type tooManyThresh: int
        :return: [description]
        :rtype: [type]
        """
        num_chars = str(f).count(char)
        tooMany = num_chars > tooManyThresh
        return num_chars, tooMany

    def filter_function(df) -> pd.DataFrame:
        return df.loc[~df["isDir"]]

    compute_these = (
        filter_function,
        [
            (
                (get_chars_in_name, {"char": "a", "tooManyThresh": 10}),
                ("num_char_{char}", "char_{char}_over_{tooManyThresh}"),
            ),
            ((wrap_randint, {"a": 0, "b": 100}), ("randNum_from_{a}-{b}"),),
        ],
    )

    df = PathAnnotate.get_annotated_paths_df(
        root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-251"),
        runsheet=Path(
            f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
        ),
        template=template,
        config_fs_f=config_fs_f,
        drop_annotations=True,
        compute_these=compute_these,
    )

    assert "num_char_a" in df.columns
    assert "char_a_over_10" in df.columns
    assert "randNum_from_0-100" in df.columns

    df.to_csv("TMP_CHECK.tsv", sep="\t", index=None)
