# tests to check if packages configuration files and scripts are correctly accessed
from VV import protocol

def test_finds_configs():
    found = protocol.get_configs()

    assert found["checks"]["RNASeq_Concensus_Pipeline_checks.yml"].is_file()
    assert found["sp"]["RNASeq_sp.yml"].is_file()
