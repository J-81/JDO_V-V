import os
from pathlib import Path

import pytest

from VV import RNASeq_VV, Microarray_VV
from VV.runsheets import MicroarrayRunsheet
from VV.utils import load_cutoffs

# MUST BE SUPPLIED AS TEST ASSETS ARE NOT PACKAGED WITH VV CODEBASE
ASSETS_LOCATION = Path("/opt/gl_test_assets")

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
        '121':ASSETS_LOCATION / Path('GLDS-121'), # microarray
        '194':ASSETS_LOCATION / Path('GLDS-194'), # rnaseq
        '373':ASSETS_LOCATION / Path('GLDS-373'), # rnaseq
        }

@pytest.fixture(scope='module')
def local_runsheets():
    yield {
        '121':ASSETS_LOCATION / Path('GLDS-121/Metadata/AST_autogen_template_Microarray_GLDS-121_a_bric-16_transcription_profiling_DNA_microarray_proto_run_sheet.csv'), # microarray
        '194':ASSETS_LOCATION / Path('GLDS-194/Metadata/AST_autogen_GLDS-194_RNASeq_runsheet.csv'), # rnaseq
        '373':ASSETS_LOCATION / Path('GLDS-373/Metadata/AST_autogen_GLDS-373_RNASeq_runsheet.csv'), # rnaseq
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
              accession='373',
              halt_severity=90,
              expected_flag_count=966,
              ),
        ],
        "test_RNASeq_VV_with_skip": [
            dict(
              accession='373',
              halt_severity=90,
              expected_flag_count=616,
              skip_these=["raw_reads"],
              ),
            dict(
              accession='373',
              halt_severity=90,
              expected_flag_count=242,
              skip_these=["raw_reads","trimmed_reads"],
              ),
            dict(
              accession='373',
              halt_severity=90,
              expected_flag_count=942,
              skip_these=["deseq2"],
              ),
        ],
        "test_Microarray_Runsheet_Parse": [
            dict(
              accession='121',
              expected_flag_count=966,
              ),
        ],
        "test_Microarray_VV": [
            dict(
              accession='121',
              halt_severity=90,
              expected_flag_count=14,
              ),
        ],
    }

    def test_RNASeq_VV(self, accession, halt_severity, expected_flag_count, local_processed, local_runsheets, tmp_path):
        """ Checks that expected number of flags against test dataset
        is raised.
        """
        os.chdir(tmp_path)
        RNASEQ_STEPS =  ("raw_reads", "trimmed_reads", "star_align", "rsem_count", "deseq2")
        skip = {step:False for step in RNASEQ_STEPS}
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

    def test_RNASeq_VV_with_skip(self, accession, halt_severity, expected_flag_count, local_processed, local_runsheets, skip_these, tmp_path):
        """ Checks that expected number of flags against test dataset
        is raised.
        """
        os.chdir(tmp_path)
        RNASEQ_STEPS =  ("raw_reads", "trimmed_reads", "star_align", "rsem_count", "deseq2")
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

    def test_Microarray_Runsheet_Parse(self, accession, expected_flag_count, local_runsheets):
        """ Checks that expected number of flags against test dataset
        is raised.
        """
        runsheet =  MicroarrayRunsheet(local_runsheets[accession])
        assert runsheet.samples == ["Atha_Ler-0_sShoots_FLT_Rep1","Atha_Ler-0_sShoots_FLT_Rep2","Atha_Ler-0_sShoots_FLT_Rep3","Atha_Ler-0_sShoots_GC_Rep1","Atha_Ler-0_sShoots_GC_Rep2","Atha_Ler-0_sShoots_GC_Rep3"]
        assert runsheet.Normalized_Data_Dir == Path("01-NormalizedData")
        assert runsheet.Limma_DGE_Dir == Path("02-Limma_DGE")

    def test_Microarray_VV(self, accession, halt_severity, expected_flag_count, local_processed, local_runsheets, tmp_path):
        """ Checks that expected number of flags against test dataset
        is raised.
        """
        os.chdir(tmp_path)
        MICROARRAY_STEPS =  ("raw_files", "normalized_data", "limma_dge")
        skip = {step:False for step in MICROARRAY_STEPS}
        flagger =    Microarray_VV.main(data_dir = local_processed[accession],
                                        halt_severity = halt_severity,
                                        output_path = Path.cwd() / Path("test_out.tsv"),
                                        sample_sheet_path = local_runsheets[accession],
                                        cutoffs = load_cutoffs(cutoffs_set="DEFAULT_MICROARRAY"),
                                        skip = skip)
        assert flagger._flag_count == expected_flag_count
