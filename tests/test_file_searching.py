# Tests for file searching module
import os

try:
    TEST_ASSETS_DIR = os.environ["PTW_TEST_ASSETS"]
except KeyError as e:
    print("PTW user needs to set env variable: 'PTW_TEST_ASSETS' to indicate where test assets are stored")
    raise e

from VV.file_search import FileSearcher

def test_init_FileSearcher():
    """ init a FileSearcher object """
    fs = FileSearcher(sp_config="RNASeq_sp.yml")


def test_loads_config():
    """ init a FileSearcher object """
    fs = FileSearcher(sp_config="RNASeq_sp.yml")
    assert fs.search_patterns["raw_fastq"] == {'dir_fn_re': '.*/00-RawData/Fastq/.*R._raw\.fastq\.gz'}
    assert fs.search_patterns["trimmed_fastq"] == {'dir_fn_re': '.*/01-TG_Preproc/Fastq/.*R._trimmed\.fastq\.gz'}

def test_finds_raw_files():
    fs = FileSearcher(sp_config="RNASeq_sp.yml", analysis_dir=[f"{TEST_ASSETS_DIR}/GLDS-194"])
    fs.get_files()
    raw_files = [f['fn'] for f in fs.files["raw_fastq"]]
    assert raw_files == ['Mmus_BAL-TAL_LRTN_GC_Rep3_G9_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep2_F7_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep3_F8_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep2_G8_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep1_G6_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep2_G8_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep1_F6_R2_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_GC_Rep4_G10_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep1_G6_R2_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_GC_Rep4_G10_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R2_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep3_B9_R2_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep4_B10_R1_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep3_B9_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep3_F8_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep1_F6_R1_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep2_F7_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R1_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep2_B8_R1_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep4_B10_R2_raw.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep2_B8_R2_raw.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep3_G9_R2_raw.fastq.gz']

def test_finds_trimmed_files():
    fs = FileSearcher(sp_config="RNASeq_sp.yml", analysis_dir=[f"{TEST_ASSETS_DIR}/GLDS-194"])
    fs.get_files(["trimmed_fastq"])
    files = [f['fn'] for f in fs.files["trimmed_fastq"]]
    assert set(files) == set(['Mmus_BAL-TAL_LRTN_GC_Rep3_G9_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep2_F7_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep3_F8_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep2_G8_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep1_G6_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep2_G8_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep1_F6_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_GC_Rep4_G10_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep1_G6_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_GC_Rep4_G10_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep3_B9_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep4_B10_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep3_B9_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep3_F8_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep1_F6_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep2_F7_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep2_B8_R1_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep4_B10_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_RRTN_BSL_Rep2_B8_R2_trimmed.fastq.gz', 'Mmus_BAL-TAL_LRTN_GC_Rep3_G9_R2_trimmed.fastq.gz'])

