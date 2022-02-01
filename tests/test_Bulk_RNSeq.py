
from VV.microarray.file_search import main

def test_GLDS_123():
    config_fs_f = "/global/scratch/joribell/local_repos/JDO_V-V/VV/microarray/file_patterns.yaml" 
    runsheet = "/global/scratch/DP_Pipeline_Drafts/Microarray_dev_20220107/dev_version1_20220107/GLDS-123/Metadata/AST_autogen_template_Microarray_GLDS-123_a_e-mtab-3289_transcription_profiling_DNA_microarray_proto_run_sheet.csv"

    result = main(config_fs_f, runsheet, platform='agilent:two_channel')
    assert result == 1

def test_GLDS_1():
    ...

def test_GLDS_205():
    ...

def test_GLDS_271():
    ...

def test_GLDS_22():
    ...

def test_GLDS_28():
    ...
