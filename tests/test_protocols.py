import pytest

from VV.protocol import list_check_configs, list_sp_configs
from VV.test_protocol import TProtocol

def test_list_check_configs():
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()

    assert check_confs[0].name == "Test_checks.yml"
    assert sp_confs[0].name  == "RNASeq_sp.yml"

def test_test_protocol_with_bad_config():
    """ Print list of protocols found packaged with the codebase """
    with pytest.raises(AssertionError):
        proto = TProtocol(check_config="s", sp_config="s")

def test_test_protocol_with_good_config():
    """ Print list of protocols found packaged with the codebase """
    check_confs = list_check_configs()
    sp_confs = list_sp_configs()
    proto = TProtocol(check_config=check_confs[0], sp_config=sp_confs[0])

    desc = proto.describe()
    print(desc)
    assert len(desc) == 605
    proto.run()


