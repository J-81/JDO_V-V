""" Validation and Verification Program For RNASeq Consenus Pipeline
"""
##############################################################
# Imports
##############################################################

import os
import sys
import configparser
import argparse
import datetime
from pathlib import Path


from VV import raw_reads
from VV import trimmed_reads
from VV import fastqc
from VV.star import StarAlignments
from VV.data import Dataset
from VV.parameters import DEFAULT_PARAMS as PARAMS
from VV.rsem import RsemCounts
from VV.deseq2 import Deseq2NormalizedCounts
from VV.flagging import Flagger

##############################################################
# Utility Functions To Handle Logging, Config and CLI Arguments
##############################################################

def _parse_args():
    """ Parse command line args.
    """
    parser = argparse.ArgumentParser(description='Perform Automated V&V on '
                                                 'raw and processed RNASeq Data.')
    parser.add_argument('--config', metavar='c', nargs='+', required=True,
                        help='INI format configuration file')

    args = parser.parse_args()
    return args


args = _parse_args()
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)
flagger = Flagger(__file__,
                  halt_level = config["Logging"].getint("HaltSeverity"))

########################################################################
# Log Folder Setup
########################################################################
os.makedirs(name = "log", exist_ok = True)
os.makedirs(name = "debug", exist_ok = True)


##############################################################
# Main Function To Call Each V&V Function
##############################################################

def main(config: dict()):
    """ Calls raw and processed data V-V functions

    :param config: configuration object
    """
    ########################################################################
    # ISA File parsing
    ########################################################################
    isa_zip_path = Path(config["Paths"].get("ISAZip"))
    isa = Dataset(isa_zip_path = isa_zip_path,
                  flagger = flagger,
                  entity = f"GLDS-{config['GLDS'].get('Number')}")
    isa.validate_verify(vv_for = "RNASeq")
    samples = isa.get_sample_names(assay_name = "transcription profiling by RNASeq")
    ########################################################################
    # Raw Read VV
    ########################################################################
    raw_reads.validate_verify(raw_reads_dir = Path(config["Paths"].get("RawReadDir")),
                              samples = samples,
                              flagger = flagger,
                              params = PARAMS
                              )
    raw_reads.validate_verify_multiqc(multiqc_json = Path(config["Paths"].get("RawMultiQCDir")) / "multiqc_data.json",
                                      samples = samples,
                                      flagger = flagger,
                                      params = PARAMS,
                                      outlier_comparision_point = "median")


    ########################################################################
    # Trimmed Read VV
    ########################################################################
    trimmed_reads.validate_verify(raw_reads_dir = Path(config["Paths"].get("TrimmedReadDir")),
                              samples = samples,
                              flagger = flagger,
                              params = PARAMS
                              )
    trimmed_reads.validate_verify_multiqc(multiqc_json = Path(config["Paths"].get("TrimmedMultiQCDir")) / "multiqc_data.json",
                                      samples = samples,
                                      flagger = flagger,
                                      params = PARAMS,
                                      outlier_comparision_point = "median")
    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    StarAlignments(samples=samples,
                   dir_path=config['Paths'].get("StarParentDir"),
                   flagger = flagger,
                   params = PARAMS)
    ###########################################################################
    # RSEM Counts VV
    ###########################################################################
    RsemCounts(samples= samples,
               dir_path=config['Paths'].get("RsemParentDir"),
               flagger = flagger,
               params = PARAMS)
    ###########################################################################
    # Deseq2 Normalized Counts VV
    ###########################################################################
    Deseq2NormalizedCounts(samples = samples,
                           dir_path = config['Paths'].get("Deseq2ParentDir"),
                           flagger = flagger,
                           params = PARAMS)
    print(f"{'='*40}")
    print(f"VV complete: Full Results Saved To {flagger._log_file}")


if __name__ == '__main__':
    main(config)
