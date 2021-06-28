#! /usr/bin/env python
""" Validation and Verification Program For Microarray Processing

Called by V-V_Program.  Not intended for direct use.
"""
from pathlib import Path
import os

from VV.flagging import Flagger
from VV.runsheets import MicroarrayRunsheet
from VV.microarray.raw_files import RawFilesVV
from VV.microarray.normalized_files import NormalizedFilesVV
from VV.microarray.dge_files import DGEFilesVV

def main(data_dir: Path,
         halt_severity: int,
         output_path: Path,
         sample_sheet_path: Path,
         cutoffs: dict,
         skip: dict):
    """ Calls raw and processed data V-V functions

    :params skip: a dictionary denoting steps to VV
    """
    program_header = "STARTING VV for Microarray Raw and Processed Data"
    print(f"{'┅'*(len(program_header)+4)}")
    print(f"┇ {program_header} ┇")
    print(f"{'┅'*(len(program_header)+4)}")
    # set up flagger
    flagger = Flagger(script = __file__,
                      log_to = output_path,
                      halt_level = halt_severity,
                      force_new_flagger = True)
    ########################################################################
    # RNASeqSampleSheet Parsing
    ########################################################################
    cross_checks = dict()
    print(cutoffs)
    sample_sheet = MicroarrayRunsheet(sample_sheet = sample_sheet_path)
    #cross_checks["SampleSheet"] = sample_sheet
    # switch working directory to where data is located
    if data_dir != Path(os.getcwd()):
        print(f"Changing working directory to {data_dir}")
        os.chdir(data_dir)
    ########################################################################
    # Raw Read VV
    ########################################################################
    if not skip['raw_files']:
        print("Running VV for Raw Files")
        RawFilesVV(file_mapping = sample_sheet.raw_files,
                   raw_file_dir = sample_sheet.Raw_Data_Dir,
                   cutoffs = cutoffs,
                   flagger = flagger)
    else:
        print(f"Skipping VV for Raw Files")

    ########################################################################
    # Trimmed Read VV
    ########################################################################
    if not skip['normalized_data']:
        print("Running VV for Normalized Data Files")
        NormalizedFilesVV(normalized_file_dir = sample_sheet.Normalized_Data_Dir,
                          cutoffs = cutoffs,
                          flagger = flagger)
    else:
        print(f"Skipping VV for Normalized Data Files")
    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    if not skip['limma_dge']:
        print("Running VV for LIMMA DGE")
        DGEFilesVV(samples = sample_sheet.samples,
                   expected_contrasts = sample_sheet.expected_contrasts,
                   dge_file_dir = sample_sheet.Limma_DGE_Dir,
                   cutoffs = cutoffs,
                   flagger = flagger)
    else:
        print(f"Skipping VV for LIMMA DGE")

    ###########################################################################
    # Generate derivative log files
    ###########################################################################
    print(f"{'='*40}")
    for log_type in ["only-issues", "by-sample", "by-step","all-by-entity"]:
        flagger.generate_derivative_log(log_type = log_type,
                                        samples = sample_sheet.samples)
    # Return flagger at successful completion
    return flagger
