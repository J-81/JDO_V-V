import os
import logging

from gl4gl.PostProcessing import generate_files_reports, generate_md5sum_table

try:
    TEST_ASSETS_DIR = os.environ["PYTEST_ASSETS"]
except KeyError as e:
    print(
        "Pytest user needs to set env variable: 'PYTEST_ASSETS' to indicate where test assets are stored"
    )
    raise e

###########################################################################

from gl4gl import PathAnnotate
from pathlib import Path

config_fs_f = [
    c for c in PathAnnotate.get_configs() if c.name == "Bulk_Search_Patterns.yaml"
][0]

template = [
    t for t in PathAnnotate.get_templates(config_fs_f) if t == "Bulk_RNASeq:PairedEnd"
][0]

import os


def test_generate_GLDS_excels(caplog, tmpdir):
    """This tests that excel reports are generated and are roughly at the expected size (+- 20 bytes).
    Failures in this test may reflect desired changes to the excel output and need to be revalidated manually.

    """
    os.chdir(tmpdir)
    caplog.set_level(logging.DEBUG)

    processed_path, raw_path, unpublished_path = generate_files_reports(
        root_path=Path(f"{TEST_ASSETS_DIR}/GLDS-251"),
        runsheet_path=Path(
            f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
        ),
        template=template,
        config_fs_f=config_fs_f,
    )

    assert processed_path.name == "processed_file_names.xlsx"
    assert (
        56680 > processed_path.stat().st_size > 56660
    )  # determined after manual validation, some SMALL variation should be allowed
    assert raw_path.name == "raw_file_names.xlsx"
    assert (
        5793 > raw_path.stat().st_size > 5773
    )  # determined after manual validation, some SMALL variation should be allowed
    assert unpublished_path.name == "unpublished_file_names.xlsx"
    assert (
        15375 > unpublished_path.stat().st_size > 15355
    )  # determined after manual validation, some SMALL variation should be allowed

    # if the above fails, manual revalidation should be performed
    # assert (
    #     0
    # ), f"Since checking the excel files programmatically can be tricky, these should be manually validated. Output dir: {tmpdir}"


def test_generate_md5sum_excels(caplog, tmpdir):
    """This tests that excel reports are generated and are roughly at the expected size (+- 20 bytes).
    Failures in this test may reflect desired changes to the excel output and need to be revalidated manually.

    """
    os.chdir(tmpdir)
    caplog.set_level(logging.DEBUG)

    md5sum_path = generate_md5sum_table.general_excel(
        root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-251"),
        runsheet=Path(
            f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
        ),
        template=template,
        config_fs_f=config_fs_f,
        annotations_keys=[
            "PI_annotations",
            "dummy_test_annotations",
            "GLDS_annotations",
        ],
    )

    assert md5sum_path.name == "GLDS-251_md5sum_table.xlsx"
    assert (
        146922 > md5sum_path.stat().st_size > 146902
    )  # manually validated and 'rough' byte size noted.

