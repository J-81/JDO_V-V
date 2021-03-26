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

def main(config, sample_sheet_path, cutoffs):
    """ Calls raw and processed data V-V functions

    :param config: configuration object
    """
    program_header = "STARTING VV for Data Processed by RNASeq Consenus Pipeline"
    print(f"{'┅'*(len(program_header)+4)}")
    print(f"┇ {program_header} ┇")
    print(f"{'┅'*(len(program_header)+4)}")
    # set up flagger
    flagger = Flagger(__file__,
                      halt_level = config["Logging"].getint("HaltSeverity"))
    ########################################################################
    # RNASeqSampleSheet Parsing
    ########################################################################
    cross_checks = dict()
    sample_sheet = RNASeqSampleSheet(sample_sheet = sample_sheet_path)
    cross_checks["SampleSheet"] = sample_sheet
    # switch working directory to where data is located
    if config["Paths"].get("DataPath"):
        print(f"Changing working directory to {config['Paths'].get('DataPath')}")
        os.chdir(Path(config["Paths"].get("DataPath")))
    ########################################################################
    # Raw Read VV
    ########################################################################
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


    ########################################################################
    # Trimmed Read VV
    ########################################################################
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
    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    StarAlignments(samples=sample_sheet.samples,
                   dir_path= sample_sheet.STAR_Alignment_dir,
                   flagger = flagger,
                   cutoffs = cutoffs)
    ###########################################################################
    # RSEM Counts VV
    ###########################################################################
    rsem_cross_check =   RsemCounts(samples= sample_sheet.samples,
                                   dir_path= sample_sheet.RSEM_Counts_dir,
                                   flagger = flagger,
                                   cutoffs = cutoffs).cross_check
    cross_checks["RSEM"] = rsem_cross_check
    ###########################################################################
    # Deseq2 Normalized Counts VV
    ###########################################################################
    Deseq2ScriptOutput(samples = sample_sheet.samples,
                       counts_dir_path = sample_sheet.DESeq2_NormCount,
                       dge_dir_path = sample_sheet.DESeq2_DGE,
                       flagger = flagger,
                       cutoffs = cutoffs,
                       cross_checks = cross_checks)

    print(f"{'='*40}")
    print(f"VV complete: Full Results Saved To {flagger._log_file}")

    ###########################################################################
    # Generate derivative log files
    ###########################################################################
    for log_type in ["only-issues", "by-sample", "by-step"]:
        flagger.generate_derivative_log(log_type = log_type,
                                        samples = sample_sheet.samples)
    # Return flagger at successful completion
    return flagger
