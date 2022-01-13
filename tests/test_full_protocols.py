import os
from pathlib import Path

import pytest

from VV import RNASeq_VV, Microarray_VV
from VV.runsheets import MicroarrayRunsheet
from VV.utils import load_cutoffs


try:
    TEST_ASSETS_DIR = Path(os.environ["PTW_TEST_ASSETS"])
except KeyError as e:
    print("PTW user needs to set env variable: 'PTW_TEST_ASSETS' to indicate where test assets are stored")
    raise e

def pytest_generate_tests(metafunc):
    # called once per each test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = sorted(funcarglist[0])
    metafunc.parametrize(
        argnames, [[funcargs[name] for name in argnames] for funcargs in funcarglist]
    )

@pytest.fixture(scope='module')
def local_processed():
    yield {
        '194':TEST_ASSETS_DIR / Path('GLDS-194'), # rnaseq
        '48':TEST_ASSETS_DIR / Path('GLDS-48'), # rnaseq
        }

@pytest.fixture(scope='module')
def local_runsheets():
    yield {
        '194':TEST_ASSETS_DIR / Path('GLDS-194/Metadata/AST_autogen_RNASeq_RCP_GLDS-194_RNASeq_runsheet.csv'), # rnaseq
        '48':TEST_ASSETS_DIR / Path('GLDS-48/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-48_RNASeq_runsheet.csv'), # rnaseq
        }

class TestClass:
    # a map specifying multiple argument sets for a test method
    params = {
        "test_RNASeq_VV": [
            # 194 has a missing column in the visualization table
            #dict(
            #  accession='194',
            #  halt_severity=90,
            #  expected_flag_count=1066,
            #  ),
            dict(
              accession='48',
              halt_severity=91,
              expected_flag_count=966,
              ),
        ],
        "test_RNASeq_VV_with_skip": [
            dict(
              accession='48',
              halt_severity=91,
              expected_flag_count=492,
              skip_these=["raw_reads","rseqc"],
              ),
            dict(
              accession='48',
              halt_severity=91,
              expected_flag_count=280,
              skip_these=["raw_reads","trimmed_reads","rseqc"],
              ),
            dict(
              accession='48',
              halt_severity=91,
              expected_flag_count=665,
              skip_these=["deseq2","rseqc"],
              ),
        ],
    }


    def test_RNASeq_VV_with_skip(self, accession, halt_severity, expected_flag_count, local_processed, local_runsheets, skip_these, tmp_path):
        """ Checks that expected number of flags against test dataset
        is raised.
        """
        os.chdir(tmp_path)
        RNASEQ_STEPS =  ("raw_reads", "trimmed_reads", "star_align", "rseqc", "rsem_count", "deseq2")
        skip = {step:False for step in RNASEQ_STEPS}
        for step in skip_these:
            skip[step] = True
        cutoffs = load_cutoffs(cutoffs_set="DEFAULT_RNASEQ")
        cutoffs["raw_reads"]["fastq_lines_to_check"] = 300
        cutoffs["trimmed_reads"]["fastq_lines_to_check"] = 300
        flagger =    RNASeq_VV.main(data_dir = local_processed[accession],
                                    halt_severity = halt_severity,
                                    output_path = Path.cwd() / Path("test_out.tsv"),
                                    sample_sheet_path = local_runsheets[accession],
                                    cutoffs = cutoffs,
                                    skip = skip)
        assert flagger._flag_count == expected_flag_count

