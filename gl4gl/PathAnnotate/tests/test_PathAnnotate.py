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
    caplog.set_level(logging.INFO)
    from gl4gl import PathAnnotate
    from pathlib import Path

    df = PathAnnotate.get_paths_df(root_dir=Path(f"{TEST_ASSETS_DIR}/GLDS-173"))
    assert len(df) == 458  # based on dev_version2 for RNASeq pipeline output
