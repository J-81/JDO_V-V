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
import logging
import datetime


from VV import raw_reads, parse_isa, fastqc, multiqc
from VV.star import StarAlignments
from VV.data import Dataset
# ISA TOOLS Causes an issue with logging level


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

# Set up logging
if config['Logging']["LoggingConsole"] in ["INFO","DEBUG","WARNING","ERROR","CRITICAL"]:
    log_levels = {"INFO":20,"DEBUG":10,"WARNING":30, "ERROR":40, "CRITICAL":50}
    logging_level = log_levels[config['Logging']['LoggingConsole']]
else:
    print("Logging level must be one of the following: <DEBUG,INFO,WARNING,ERROR,CRITICAL>")
    sys.exit()
# Fixes ISA logging but needs a much better fix
log = logging.getLogger("VV")
log.setLevel(logging_level)


run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

# set up file logging (warning)
fh = logging.FileHandler(f"log/{run_timestamp}_issues.log")
fh.setLevel(logging.WARNING)
fh_formatter = logging.Formatter('%(levelname)s: %(message)s')
fh.setFormatter(fh_formatter)
log.addHandler(fh)

# full debug log (debug level)
fh = logging.FileHandler(f"debug/{run_timestamp}_debug.log")
fh.setLevel(logging.DEBUG)
fh_formatter = logging.Formatter('%(asctime)s:%(levelname)s:<%(filename)s:Line:%(lineno)s>: %(message)s')
fh.setFormatter(fh_formatter)
log.addHandler(fh)

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
    samples_dict = parse_isa.get_sample_names(
            config["Paths"].get("ISAZip"))
    isa_raw_sample_names = set([sample
                                for study in samples_dict.values()
                                for assay_samples in study.values()
                                for sample in assay_samples])

    isa = Dataset(config["Paths"].get("ISAZip"))

    ########################################################################
    # Raw Read VV
    ########################################################################
    raw_results = raw_reads.validate_verify(
                    input_path=config["Paths"].get("RawReadDir"),
                    paired_end=config["GLDS"].getboolean("PairedEnd"),
                    count_lines_to_check=config["Options"].getint("MaxFastQLinesToCheck"),
                    expected_suffix=config["Naming"].get("RawReadsSuffix"))

    fastqc.validate_verify(
        samples=isa_raw_sample_names,
        input_path=config["Paths"].get("RawFastQCDir"),
        paired_end=config["GLDS"].getboolean("PairedEnd"),
        expected_suffix=config["Naming"].get("RawFastQCSuffix"))


    thresholds = dict()
    thresholds['avg_sequence_length'] = config['Raw'].getfloat("SequenceLengthVariationTolerance")
    thresholds['percent_gc'] = config['Raw'].getfloat("PercentGCVariationTolerance")
    thresholds['total_sequences'] = config['Raw'].getfloat("TotalSequencesVariationTolerance")
    thresholds['percent_duplicates'] = config['Raw'].getfloat("PercentDuplicatesVariationTolerance")

    raw_mqc = multiqc.MultiQC(
            multiQC_zip_path=config["Paths"].get("RawMultiQCZip"),
            samples=isa.assays['transcription profiling by RNASeq'].samples,
            paired_end=config["GLDS"].getboolean("PairedEnd"),
            outlier_thresholds=thresholds)

    ########################################################################
    # Trimmed Read VV
    ########################################################################
    trimmed_results = raw_reads.validate_verify(
                    input_path=config["Paths"].get("TrimmedReadDir"),
                    paired_end=config["GLDS"].getboolean("PairedEnd"),
                    count_lines_to_check=config["Options"].getint("MaxFastQLinesToCheck"),
                    expected_suffix=config["Naming"].get("TrimmedReadsSuffix"))

    fastqc.validate_verify(
        samples=isa_raw_sample_names,
        input_path=config["Paths"].get("TrimmedFastQCDir"),
        paired_end=config["GLDS"].getboolean("PairedEnd"),
        expected_suffix=config["Naming"].get("TrimmedFastQCSuffix"))

    thresholds = dict()
    thresholds['avg_sequence_length'] = config['Trimmed'].getfloat("SequenceLengthVariationTolerance")
    thresholds['percent_gc'] = config['Trimmed'].getfloat("PercentGCVariationTolerance")
    thresholds['total_sequences'] = config['Trimmed'].getfloat("TotalSequencesVariationTolerance")
    thresholds['percent_duplicates'] = config['Trimmed'].getfloat("PercentDuplicatesVariationTolerance")

    trimmed_mqc = multiqc.MultiQC(
            multiQC_zip_path=config["Paths"].get("TrimmedMultiQCZip"),
            samples=isa.assays['transcription profiling by RNASeq'].samples,
            paired_end=config["GLDS"].getboolean("PairedEnd"),
            outlier_thresholds=thresholds)

    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    StarAlignments(samples=isa.assays['transcription profiling by RNASeq'].samples,
                   dir_path=config['Paths'].get("StarParentDir"))


    ###########################################################################
    # Filename Checking
    ###########################################################################
    sample_names_match = raw_results.sample_names == \
                         set(isa.assays['transcription profiling by RNASeq'].samples) ==\
                         trimmed_results.sample_names

    checkname = "ISA sample names should match both raw reads"\
                "and trimmed reads folder"
    if sample_names_match:
        log.info(f"PASS: {checkname}")
    else:
        log.error(f"FAIL: {checkname}: "
                  f"ISA: {isa.assays['transcription profiling by RNASeq'].samples}"
                  f"RawReads Folder: {raw_results.sample_names} "
                  f"TrimmedReads Folder: {trimmed_results.sample_names} ")



if __name__ == '__main__':
    main(config)
