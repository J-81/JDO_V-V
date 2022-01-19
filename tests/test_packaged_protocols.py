import os
from pathlib import Path

from VV.packaged_protocols import RNASeq_Concensus_Pipeline_Protocol as RCCP

try:
    TEST_ASSETS_DIR = os.environ["PTW_TEST_ASSETS"]
except KeyError as e:
    print("PTW user needs to set env variable: 'PTW_TEST_ASSETS' to indicate where test assets are stored")
    raise e

def test_R0001(monkeypatch):
    sample = "Mmus_BAL-TAL_LRTN_GC_Rep3_G9"
    files = [
            Path("somepath/somewhere/Mmus_BAL-TAL_LRTN_GC_Rep3_G9_R1_raw.fastq.gz"),
            Path("somepath/somewhere/NONMATCH_Rep3_G9_R1_raw.fastq.gz"),
            Path("somepath/somewhere/Mmus_BAL-TAL_LRTN_GC_Rep3_G9_R2_raw.fastq.gz"),
            ]
    
    check = RCCP.R_0001(config = {'R_0001':{'expected_number_read_files':2,'match_num_fcode':30,'bad_num_fcode':90}})


    flag = check.perform_function(sample = sample, raw_fastqs = files)
    
    # this should pass
    assert flag.code == 30

def test_R0002():
    sample = "Mmus_BAL-TAL_LRTN_GC_Rep3_G9"
    file = f"{TEST_ASSETS_DIR}/GLDS-194/00-RawData/Fastq/Mmus_BAL-TAL_LRTN_FLT_Rep3_F8_R2_raw.fastq.gz"
    
    check = RCCP.R_0002(config = {'R_0002':{'issues_fcode':90,'no_issues_fcode':30,'corrupt_fcode':90,'lines_to_check':100}})

    flag = check.perform_function(sample = sample, read_file = 'reverse_read' ,raw_fastq = file)
    
    # this should pass
    assert flag.code == 30


def test_RNASeq_Concensus_Pipeline_Protocol():
    with open(f"{TEST_ASSETS_DIR}/GLDS-194/Metadata/samples.txt","r") as f:
        samples = [s.strip() for s in f.readlines()]
    output_f, flag_df = RCCP.start_protocol(samples = samples, vv_dir=f"{TEST_ASSETS_DIR}/GLDS-194")

    # check expected results by each check
    r_0001_flags = flag_df.loc[flag_df['check_id'] == 'R_0001']
    assert len(r_0001_flags) == len(samples) # for now only one check per file
    assert sum(r_0001_flags['severity'])/len(samples) == 30 # all samples should get a pass

    # check expected results by each check
    r_0002_forward_flags = flag_df.loc[(flag_df['check_id'] == 'R_0002') & (flag_df['sub_entity'] == 'forward_reads')]
    assert len(r_0002_forward_flags) == len(samples) # for now only one check per file
    assert sum(r_0002_forward_flags['severity'])/len(samples) == 30 # all samples should get a pass

    r_0002_reverse_flags = flag_df.loc[(flag_df['check_id'] == 'R_0002') & (flag_df['sub_entity'] == 'reverse_reads')]
    assert len(r_0002_reverse_flags) == len(samples) # for now only one check per file
    assert sum(r_0002_reverse_flags['severity'])/len(samples) == 30 # all samples should get a pass

    assert output_f == 'RNASeq_Consensus_Pipeline_VV_Log.tsv'
    
    
