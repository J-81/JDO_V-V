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
"""
##############################################################
# Imports
##############################################################

import os
import sys
import configparser
import argparse
import logging


from VV import raw_reads, parse_isa, fastqc, multiqc
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


##############################################################
# Main Function To Call Each V&V Function
##############################################################

def main(config: dict()):
    """ Calls raw and processed data V-V functions

    :param config: configuration object
    """
    #log.debug("Parsing ISA and Extracting Sample Names")
    samples_dict = parse_isa.get_sample_names(config["Paths"].get("ISAZip"))
    isa_raw_sample_names = set([sample
                                for study in samples_dict.values()
                                for assay_samples in study.values()
                                for sample in assay_samples])
    #log.debug(f"Full Sample Name Dict: {samples_dict}")
    #log.info(f"{len(isa_raw_sample_names)} "
    #         f"Total Unique Samples Found: {isa_raw_sample_names}")

    #log.info("Starting Raw Data V-V")
    #log.debug(f"raw_path: {raw_path}")
    raw_results = raw_reads.validate_verify(
                    input_path=config["Paths"].get("RawReadDir"),
                    paired_end=config["GLDS"].getboolean("PairedEnd"),
                    count_lines_to_check=config["Options"].getint("MaxFastQLinesToCheck"))
    #log.info("Finished Raw Data V-V")

    #log.info("Starting Check Raw FastQC and MultiQC files")
    #log.debug(f"fastQC_path: {fastqc_path}")
    fastqc.validate_verify(
        samples=isa_raw_sample_names,
        input_path=config["Paths"].get("RawFastQCDir"),
        paired_end=config["GLDS"].getboolean("PairedEnd"),
        expected_suffix=config["Naming"].get("FastQCSuffix"))

    multiqc.validate_verify(
        multiQC_zip_path=config["Paths"].get("RawMultiQCZip"),
        paired_end=config["GLDS"].getboolean("PairedEnd"),
        sequence_length_tolerance=config["Options"].getfloat("SequenceLengthVariationTolerance"))
    #log.info("Finished Check Raw FastQC and MultiQC files")

    #log.debug(f"Results from Raw VV: {raw_results}")

    #log.info(f"Checking if sample names from raw reads folder match ISA file")
    sample_names_match = raw_results.sample_names == isa_raw_sample_names
    checkname = "ISA sample names should match raw reads folder"
    if sample_names_match:
        log.info(f"PASS: {checkname}")
    else:
        log.error(f"FAIL: {checkname}: "
                  f"ISA: {isa_raw_sample_names}"
                  f"RawReads Folder: {raw_results.sample_names}")


if __name__ == '__main__':
    main(config)
