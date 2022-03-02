""" Tests for FastQC related checks in BulkRNASeq """
import os
from pathlib import Path

from gl4gl import VnV


try:
    TEST_ASSETS_DIR = os.environ["PYTEST_ASSETS"]
except KeyError as e:
    print(
        "Pytest user needs to set env variable: 'PYTEST_ASSETS' to indicate where test assets are stored"
    )
    raise e

EXPECTED_LOGGER = "Flagging.gl4gl.VnV.fastqc"


def test_fastqc_checks(caplog):
    test_data = f"{TEST_ASSETS_DIR}/GLDS-251"
    runsheet = f"{TEST_ASSETS_DIR}/GLDS-251/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-251_RNASeq_runsheet.csv"
    SAMPLES = 20

    with caplog.at_level(10, logger=EXPECTED_LOGGER):
        VnV.fastqc.main(Path(test_data), runsheet)

    flags = [r for r in caplog.records if r.name.startswith("Flagging.")]

    samplewise_flags_expected = SAMPLES * 2  # two sample wise path types
    dataset_flags_expected = 1  # one dataset path type
    assert len(flags) == samplewise_flags_expected + dataset_flags_expected
    for flag_record in flags:
        assert flag_record.flag_code == 30
        assert flag_record.message.startswith("Found expected number of")

