#! /usr/bin/env python
""" Validation and Verification Program For RNASeq Consenus Pipeline

Called by V-V_Program.  Not intended for direct use.
"""
from pathlib import Path
import os

from VV import raw_reads
from VV import trimmed_reads
from VV import fastqc
from VV.cutoffs import CUTOFFS as MODULECUTOFFS
from VV.star import StarAlignments
from VV.data import Dataset
from VV.rnaseq_samplesheet import RNASeqSampleSheet
from VV.rsem import RsemCounts
from VV.deseq2 import Deseq2ScriptOutput
from VV.flagging import Flagger

def main(data_dir: Path,
         halt_severity: int,
         output_path: Path,
         sample_sheet_path: Path,
         cutoffs: dict,
         skip: dict):
    """ Calls raw and processed data V-V functions

    :params skip: a dictionary denoting steps to VV
    """
    program_header = "STARTING VV for Data Processed by RNASeq Consenus Pipeline"
    print(f"{'┅'*(len(program_header)+4)}")
    print(f"┇ {program_header} ┇")
    print(f"{'┅'*(len(program_header)+4)}")
    # set up flagger
    flagger = Flagger(script = __file__,
                      log_to = output_path,
                      halt_level = halt_severity)
    ########################################################################
    # RNASeqSampleSheet Parsing
    ########################################################################
    cross_checks = dict()
    sample_sheet = RNASeqSampleSheet(sample_sheet = sample_sheet_path)
    cross_checks["SampleSheet"] = sample_sheet
    # switch working directory to where data is located
    if data_dir != Path(os.getcwd()):
        print(f"Changing working directory to {data_dir}")
        os.chdir(data_dir)
    ########################################################################
    # Raw Read VV
    ########################################################################
    if not skip['raw_reads']:
        raw_reads.validate_verify(file_mapping = sample_sheet.raw_reads,
                                  flagger = flagger,
                                  cutoffs = cutoffs
                                  )
        raw_reads.validate_verify_multiqc(multiqc_json = sample_sheet.raw_read_multiqc,
                                          file_mapping = sample_sheet.raw_reads,
                                          flagger = flagger,
                                          cutoffs = cutoffs,
                                          outlier_comparision_point = "median",
                                          paired_end = sample_sheet.paired_end)
    else:
        print(f"Skipping VV for Raw Reads")

    ########################################################################
    # Trimmed Read VV
    ########################################################################
    if not skip['trimmed_reads']:
        trimmed_reads.validate_verify(file_mapping = sample_sheet.trimmed_reads,
                                      flagger = flagger,
                                      cutoffs = cutoffs
                                      )
        trimmed_reads.validate_verify_multiqc(multiqc_json = sample_sheet.trimmed_read_multiqc,
                                              file_mapping = sample_sheet.trimmed_reads,
                                              flagger = flagger,
                                              cutoffs = cutoffs,
                                              outlier_comparision_point = "median",
                                              paired_end = sample_sheet.paired_end)
    else:
        print(f"Skipping VV for Trimmed Reads")
    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    if not skip['star_align']:
        StarAlignments(dir_mapping = sample_sheet.STAR_Alignment_dir_mapping,
                       flagger = flagger,
                       cutoffs = cutoffs)
    else:
        print(f"Skipping VV for Star Alignments")
    ###########################################################################
    # RSEM Counts VV
    ###########################################################################
    if not skip['rsem_count']:
        rsem_cross_check =   RsemCounts(dir_mapping = sample_sheet.RSEM_Counts_dir_mapping,
                                        flagger = flagger,
                                        has_ERCC = sample_sheet.has_ERCC,
                                        cutoffs = cutoffs).cross_check
        cross_checks["RSEM"] = rsem_cross_check
    else:
        print(f"Skipping VV for RSEM Counts")
    ###########################################################################
    # Deseq2 Normalized Counts VV
    ###########################################################################
    if not skip['deseq2']:
        Deseq2ScriptOutput(samples = sample_sheet.samples,
                           counts_dir_path = sample_sheet.DESeq2_NormCount,
                           dge_dir_path = sample_sheet.DESeq2_DGE,
                           flagger = flagger,
                           cutoffs = cutoffs,
                           has_ERCC = sample_sheet.has_ERCC,
                           cross_checks = cross_checks)
    else:
        print(f"Skipping VV for DESeq2")
    ###########################################################################
    # Generate derivative log files
    ###########################################################################
    print(f"{'='*40}")
    for log_type in ["only-issues", "by-sample", "by-step","all-by-entity"]:
        flagger.generate_derivative_log(log_type = log_type,
                                        samples = sample_sheet.samples)
    # Return flagger at successful completion
    return flagger
