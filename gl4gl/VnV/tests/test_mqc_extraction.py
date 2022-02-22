import os
from pathlib import Path
import logging

from gl4gl import VnV

try:
    TEST_ASSETS_DIR = os.environ["PYTEST_ASSETS"]
except KeyError as e:
    print(
        "Pytest user needs to set env variable: 'PYTEST_ASSETS' to indicate where test assets are stored"
    )
    raise e


def test_00_mqc_to_dataframe(caplog):
    # ~11 sec
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/00-RawData"]

    mqc_ret = VnV.use_multiqc.get_parsed_data(test_dataset, as_dataframe=True)

    assert len(mqc_ret) == 40  # 20 samples times two due to paired end

    unique_top_two_level_cols = set(
        c[0:2] for c in mqc_ret.loc[:, (slice(None), slice(None))].columns
    )
    assert (
        len(unique_top_two_level_cols) == 10
    )  # check number of unique top level two level columns


def test_01_mqc_to_dataframe(caplog):
    # ~11 sec
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/01-TG_Preproc"]

    mqc_ret = VnV.use_multiqc.get_parsed_data(test_dataset, as_dataframe=True)

    assert (
        len(mqc_ret) == 80
    )  # 20 samples times two due to paired end times two again due to raw being trimmed and trimmed being fastQC'ed
    unique_top_two_level_cols = set(
        c[0:2] for c in mqc_ret.loc[:, (slice(None), slice(None))].columns
    )
    assert len(unique_top_two_level_cols) == 13


def test_02_mqc_to_dataframe(caplog):
    #
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/02-STAR_Alignment"]
    modules = [
        "star"
    ]  # modules doesn't need to be specified; however, this greatly increases speed if the module is known
    # in this case, the 02-STAR_Alignment directory gets parsed about 100x slower without limiting to just the star module!

    mqc_ret = VnV.use_multiqc.get_parsed_data(
        test_dataset, modules=modules, as_dataframe=True
    )

    assert (
        len(mqc_ret) == 40
    )  # 20 samples times two due to paired end times two again due to raw being trimmed and trimmed being fastQC'ed
    unique_top_two_level_cols = set(
        c[0:2] for c in mqc_ret.loc[:, (slice(None), slice(None))].columns
    )
    assert len(unique_top_two_level_cols) == 3


def test_03_mqc_to_dataframe(caplog):
    # expensive test, runs in ~
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/03-RSEM_Counts"]
    modules = [
        "rsem"
    ]  # modules doesn't need to be specified; however, this greatly increases speed if the module is known
    # in this case, the 02-STAR_Alignment directory gets parsed about 100x slower without limiting to just the star module!

    mqc_ret = VnV.use_multiqc.get_parsed_data(
        test_dataset, modules=modules, as_dataframe=True
    )

    assert len(mqc_ret) == 20  # 20 samples
    unique_top_two_level_cols = set(
        c[0:2] for c in mqc_ret.loc[:, (slice(None), slice(None))].columns
    )
    assert len(unique_top_two_level_cols) == 4


def test_04_mqc_to_dataframe(caplog):
    # expensive test, runs in ~
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/04-DESeq2_NormCounts"]

    mqc_ret = VnV.use_multiqc.get_parsed_data(test_dataset, as_dataframe=True)

    assert mqc_ret == None  # nothing in these directories are covered by multiqc


def test_05_mqc_to_dataframe(caplog):
    # expensive test, runs in ~
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/05-DESeq2_DGE"]

    mqc_ret = VnV.use_multiqc.get_parsed_data(test_dataset, as_dataframe=True)

    assert mqc_ret == None  # nothing in these directories are covered by multiqc


def test_RSEQC_mqc_to_dataframe(caplog):
    # expensive test, runs in ~
    caplog.set_level(logging.DEBUG)

    test_dataset = [f"{TEST_ASSETS_DIR}/GLDS-251/RSeQC_Analyses"]

    mqc_ret = VnV.use_multiqc.get_parsed_data(test_dataset, as_dataframe=True)

    assert len(mqc_ret) == 20  # 20 samples
    unique_top_two_level_cols = set(
        c[0:2] for c in mqc_ret.loc[:, (slice(None), slice(None))].columns
    )
    assert len(unique_top_two_level_cols) == 6

