import os
from pathlib import Path

try:
    TEST_ASSETS_DIR = os.environ["PTW_TEST_ASSETS"]
except KeyError as e:
    print("PTW user needs to set env variable: 'PTW_TEST_ASSETS' to indicate where test assets are stored")
    raise e

import pytest

from VV.protocol import list_check_configs, list_sp_configs
from VV.test_protocol import TProtocol, TProtocol2

def test_list_check_configs():
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()

    assert check_confs[0].name == "Test_checks.yml"
    assert sp_confs[0].name  == "RNASeq_sp.yml"

def test_test_protocol_with_bad_config():
    """ Print list of protocols found packaged with the codebase """
    with pytest.raises(AssertionError):
        proto = TProtocol(check_config="s", sp_config="s", vv_dir="s")

def test_test_protocol_with_good_config():
    """ Print list of protocols found packaged with the codebase """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")

    desc = proto.describe()
    print(desc)
    assert len(desc) == 764
    proto.run()

def test_test_protocol_filesearching_bad_analysis_dir():
    """ Print list of protocols found packaged with the codebase """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-19fds")
    
    proto.extract_data()
    for file_type, files in proto.files.items():
        assert len(files) == 0
        assert file_type

def test_test_protocol_filesearching():
    """ Print list of protocols found packaged with the codebase """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    print(TEST_ASSETS_DIR)
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")
    

    proto.extract_data()
    assert set(proto.files.keys()) == {"raw_fastq","software_versions","trimmed_fastq"}
    assert proto.files['raw_fastq'] == 1

def test_test_protocol_filesearching():
    """ Print list of protocols found packaged with the codebase """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    print(TEST_ASSETS_DIR)
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")

def test_test_protocol_to_log():
    """ Test a full dummy protocol with included test data from a truncated RNASeq processing run """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    print(TEST_ASSETS_DIR)
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")

    proto.extract_data()
    proto.run()
    expected_output_f = proto.check_config['Flagging']['output_tsv']
    # a log should be created in the pwd
    assert Path(expected_output_f).is_file()
    with open(expected_output_f, "r") as f:
        lines = f.readlines()
    assert len(lines) == 14
    assert lines[0].startswith("# Next rows")
    
   
def test_test_protocol_append_to_log():
    """ Test a full dummy protocol with included test data from a truncated RNASeq processing run """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    print(TEST_ASSETS_DIR)
    proto = TProtocol2(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")

    proto.extract_data()
    proto.run(append_to_log=True)
    expected_output_f = proto.check_config['Flagging']['output_tsv']
    # a log should be created in the pwd
    assert Path(expected_output_f).is_file()
    with open(expected_output_f, "r") as f:
        lines = f.readlines()
    assert len(lines) == 20
    assert lines[0].startswith("# Next rows")
    assert lines[14].startswith("# Next rows")

def test_autodoc_generation():
    """ Without running, a protocol should be able to generate a summary of what it will run, i.e. what it will do to V&V """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0], vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")

    out_f = proto.document()
    assert str(out_f) == f"TestProtocol_Conf-{Path(proto.check_config_f).name.replace('.yml','')}_Documentation.txt"



    
