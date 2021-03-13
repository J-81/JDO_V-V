""" Validation and Verification Program For RNASeq Consenus Pipeline

Terminology:
- SampleWise: Describes metric based on entire sample
- ReadsWise: Describes metrics based on a read file (forward and reverse reads
    for the same samples are distinct entities in when this term is used)
- DatasetWise: Describes metric based on all samples in set
- PASS: Indicates the data has passed a V&V condition
- FAIL: Indicates the data has failed a V&V condition and will need further manually assessment
- WARN: Indicates the data has an anomoly.  In aggregate, this may indicate
    further manual assessment but by taken itself should not require such measures

- Logging Level Notes
    - Debug: start of check
    - Info: Check passes
    - Warning: Anomoly found, but did not failing a hard check
    - Error: Hard Check Failed
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
from VV import parse_isa
from VV import fastqc
from VV import multiqc
#from VV.star import StarAlignments
from VV.data import Dataset
#from VV.rsem import RsemCounts
#from VV.deseq2 import Deseq2NormalizedCounts
# ISA TOOLS Causes an issue with logging level
from VV.flagging import Flagger
flagger = Flagger(__file__)


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
    print(args)
    return args


args = _parse_args()
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)

run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

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
    samples= parse_isa.get_sample_names(
                            config["Paths"].get("ISAZip"),
                            samples_only = True)


    ########################################################################
    # Raw Read VV
    ########################################################################
    flagger.set_step("Raw Reads")
    raw_reads.validate_verify(raw_reads_dir = Path(config["Paths"].get("RawReadDir")),
                              samples = samples,
                              flagger = flagger
                              )

    thresholds = dict()
    thresholds['avg_sequence_length'] = config['Raw'].getfloat("SequenceLengthVariationTolerance")
    thresholds['percent_gc'] = config['Raw'].getfloat("PercentGCVariationTolerance")
    thresholds['total_sequences'] = config['Raw'].getfloat("TotalSequencesVariationTolerance")
    thresholds['percent_duplicates'] = config['Raw'].getfloat("PercentDuplicatesVariationTolerance")

    raw_mqc = multiqc.MultiQC(
            multiQC_out_path=config["Paths"].get("RawMultiQCDir"),
            samples=isa.assays['transcription profiling by RNASeq'].samples,
            paired_end=config["GLDS"].getboolean("PairedEnd"),
            outlier_thresholds=thresholds)

    ########################################################################
    # Trimmed Read VV
    ########################################################################
    input_paths = trimmed_reads.find_files(input_path = config["Paths"].get("TrimmedReadDir"),
                                   paired_end = config["GLDS"].getboolean("PairedEnd"),
                                   samples = isa.assays['transcription profiling by RNASeq'].samples)

    trimmed_reads.validate_verify(input_paths = input_paths,
                              paired_end = config["GLDS"].getboolean("PairedEnd"),
                              count_lines_to_check = config["Options"].getint("MaxFastQLinesToCheck"))

    thresholds = dict()
    thresholds['avg_sequence_length'] = config['Trimmed'].getfloat("SequenceLengthVariationTolerance")
    thresholds['percent_gc'] = config['Trimmed'].getfloat("PercentGCVariationTolerance")
    thresholds['total_sequences'] = config['Trimmed'].getfloat("TotalSequencesVariationTolerance")
    thresholds['percent_duplicates'] = config['Trimmed'].getfloat("PercentDuplicatesVariationTolerance")

    trimmed_mqc = multiqc.MultiQC(
            multiQC_out_path=config["Paths"].get("TrimmedMultiQCDir"),
            samples=isa.assays['transcription profiling by RNASeq'].samples,
            paired_end=config["GLDS"].getboolean("PairedEnd"),
            outlier_thresholds=thresholds)

    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    StarAlignments(samples=isa.assays['transcription profiling by RNASeq'].samples,
                   dir_path=config['Paths'].get("StarParentDir"))

    ###########################################################################
    # RSEM Counts VV
    ###########################################################################
    RsemCounts(samples=isa.assays['transcription profiling by RNASeq'].samples,
               dir_path=config['Paths'].get("RsemParentDir"),
               outlier_stdev_threshold=config["Rsem"].getfloat('CountsVariationTolerance'))

    ###########################################################################
    # Deseq2 Normalized Counts VV
    ###########################################################################
    Deseq2NormalizedCounts(samples=isa.assays['transcription profiling by RNASeq'].samples,
                            dir_path=config['Paths'].get("Deseq2ParentDir"),
                            has_ERCC=config['Deseq2'].getboolean("HasERCC"))

if __name__ == '__main__':
    main(config)
