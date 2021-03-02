""" V-V for raw reads.
"""
from collections import namedtuple
from typing import Tuple
import hashlib
import statistics
import glob
import os
import sys
import configparser
import argparse
from pathlib import Path
import gzip
import logging
log = logging.getLogger(__name__)

from VV.data import Dataset
from VV.multiqc import MultiQC
from VV.flagging import Flagger
Flagger = Flagger(script=Path(__file__).name)

# information extracted from raw reads V-V
# used to check against other sources of information including ISA file.
rawReadsInfo = namedtuple("rawReadsInfo", "sample_names")

def find_files(input_path: str,
                samples: list,
                paired_end: bool):
    """ Finds expected raw read files.

    Returns paths to files is successfully found.
    """
    paths = dict()
    for sample in samples:
        # create list of expected file paths
        expected_paths = list()
        expected_paths.append(Path(input_path) / Path(f"{sample}_R1_trimmed.fastq.gz"))
        if paired_end:
            expected_paths.append(Path(input_path) / Path(f"{sample}_R2_trimmed.fastq.gz"))

        for expected_path in expected_paths:
            if expected_path.exists():
                log.debug(f"Found {expected_path}")
            else:
                Flagger.flag(message = f"Could not find expected trimmed read file for {sample} (Expected file: {expected_path})",
                                severity=90,
                                checkID="T_0001")
        paths[sample] = expected_paths
    return paths



def validate_verify(input_paths: dict,
                    paired_end: bool,
                    count_lines_to_check: int,
                    md5sums: dict = {},
                    ):
    """Performs validation and verification for input of RNASeq datasets.
    Additionally checks for FastQC file existence.

    This assumes the following file format:

    |  ``Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R2_raw.fastq.gz``
    |  ``<SAMPLE NAME-----------------><READ->.fastq.gz``

    This also assumes that regardless of paired or single mode, there exists a file named:

    <SAMPLE NAME>_R1_raw.fastq.gz
    and <SAMPLE NAME> never includes "_R1_raw.fastq.gz"

    Performs the following checks:
    #. File name enumeration
    #. Sample name extraction
    #. Checks for appropriate number of raw read files (2x samples for Paired, 1x samples for Single)
    #. Check every identifier lines appear every four lines as expect TODO: parse identifier lines for UMI
    #. md5sum check (if expected md5sums are supplied)
    #. FastQC file count check
    #. File Size stats

    :param input_paths: samples, list(raw read paths)
    :param paired_end: True for paired end, False for single reads
    :param md5sums: dictionary of raw read file to md5sum, e.g. Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_raw.fastq.gz : b21ca61d56208d49b9422a1306d0a0f1
    :param count_lines_to_check: number of lines to check, takes around 10 min per file with GLDS-194 for 100% check.  Special values: -1 indicates to check all lines, 0 disables line checking completely
    """
    log.debug(f"Processing Paired End: {paired_end}")

    # load files from input_path
    files = list()
    [files.extend(paths) for paths in input_paths.values()]
    log.info(f"{len(files)} Raw Read Files, example: {files[0]}")
    log.debug(files)

    # get compressed files sizes and log max,min,median
    file_sizes = _size_check(files)
    log.info(f"Max    file size: {max(file_sizes.values()):.3} GB")
    log.info(f"Median file size: {statistics.median(file_sizes.values()):.3} GB")
    log.info(f"Min    file size: {min(file_sizes.values()):.3} GB")
    log.debug(f"All file sizes (in GB): {file_sizes}")

    # check lines of files
    if count_lines_to_check:
        for file in files:
            _check_fastq_content(file, count_lines_to_check=count_lines_to_check)
    else:
        log.warning(f"WARNING: Line checking disabled.  Make sure this was intentional!")


    # calculate md5sum of files and check against known md5sums
    if md5sums:
        log.info(f"Checking md5sum against supplied values")
        for file in files:
            try:
                expected = md5sum[os.path.basename(file)]
            except KeyError:
                log.error(f"expected md5sum not supplied for {os.path.basename(file)}, skipping")
                continue
            match = _md5_check(file, expected_md5=expected)
            if match:
                log.debug(f"md5sum for {os.path.basename(file)} matches")
            elif not match:
                log.error(f"MISMATCH: md5sum does not match expected for {os.path.basename(file)}")
    else:
        log.warning(f"No expected md5sums supplied, cannot verify raw read files")

def _file_counts_check(files: [str], sample: str) -> Tuple[int,int]:
    """ Returns the number of R1 and R2 files found for each sample

    Note: the replace ensures the 'R1' and 'R2' substrings from the sample name
    are not detected for counting Forward and Reverse read files.

    :param files: compressed raw read files
    :param sample: sample name
    """
    filenames = [os.path.basename(file) for file in files]
    R1_count = 0
    R2_count = 0
    for filename in filenames:
        cleaned_filename = filename.replace(sample, "")
        # skip filenames that do not contain sample
        if sample not in filename:
            continue
        elif "R1" in cleaned_filename:
            R1_count += 1
        elif "R2" in cleaned_filename:
            R2_count += 1
        else:
            log.warning(f"ANOMOLY: Unexpected filename format for {filename}")
    return (R1_count, R2_count)

def _check_fastq_content(file: str, count_lines_to_check: int) -> int:
    """ Checks fastq lines for expected header content

    Note: Example of header from GLDS-194

    |  ``@J00113:376:HMJMYBBXX:3:1101:26666:1244 1:N:0:NCGCTCGA\n``

    This also assumes the fastq file does NOT split sequence or quality lines
    for any read

    :param file: compressed fastq file to check
    :param count_lines_to_check: number of lines to check. Special value: -1 means no limit, check all lines.
    """
    if count_lines_to_check == -1:
        count_lines_to_check = float("inf")

    checkname = "FastQ Lines Check"
    expected_length = None
    with gzip.open(file, "rb") as f:
        for i, line in enumerate(f):
            # only check every fifth line to save time checking
            if i+1 == count_lines_to_check:
                log.debug(f"Reached {count_lines_to_check} lines, ending line check")
                return

            line = line.decode()
            # every fourth line should be an identifier
            expected_identifier_line = (i % 4 == 0)
            # check if line is actually an identifier line
            if (expected_identifier_line and line[0] != "@"):
                log.error(f"FAIL: {checkname}: "
                          f"Line {i} of {file} was not an identifier line as expected "
                          f"LINE {i}: {line}")
            # update every 20,000,000 reads
            if i % 20000000 == 0:
                log.debug(f"Checked {i} lines for {file}")
    log.info(f"Reached end of read file at {i+1} lines, ending line check")
    return

def _parse_samples(files: [str], paired_end: bool, expected_suffix: str) -> [str]:
    """ Parses file names from raw read files

    :param files: compressed raw read files
    :param paired_end: flag indicating whether the data is paired ended or single
    """
    # extract basename from full paths
    fnames = [os.path.basename(f) for f in files]

    # extract sample names
    unique_samples = list(set([fname.replace(f"_R1{expected_suffix}.fastq.gz","")\
                                    .replace(f"_R2{expected_suffix}.fastq.gz","")
                               for fname in fnames]))

    return unique_samples

def _size_check(files: [str]) -> dict:
    """ Gets file size for input files.

    :param files: compressed raw read files
    """
    return {f:_bytes_to_gb(os.path.getsize(f)) for f in files}

def _bytes_to_gb(bytes: int):
    """ utility function, converts bytes to gb

    :param bytes: bytes to convert
    """
    return bytes/float(1<<30)

def _md5_check(file: str, expected_md5: str) -> bool:
    """ Checks md5 hex digest of the file against an expected md5 hex digest

    :param file: compressed raw read file
    :param expected_md5: expected md5 hex digest, supplied by GeneLab
    """
    return expected_md5 == hashlib.md5(open(file,'rb').read()).hexdigest()

if __name__ == '__main__':
    def _parse_args():
        """ Parse command line args.
        """
        parser = argparse.ArgumentParser(description='Perform Automated V&V on '
                                                     'raw reads.')
        parser.add_argument('--config', metavar='c', nargs='+', required=True,
                            help='INI format configuration file')

        args = parser.parse_args()
        print(args)
        return args


    args = _parse_args()
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(args.config)


    isa = Dataset(config["Paths"].get("ISAZip"))
    samples = isa.assays['transcription profiling by RNASeq'].samples

    input_paths = find_files(   input_path = config["Paths"].get("RawReadDir"),
                                paired_end = config["GLDS"].getboolean("PairedEnd"),
                                samples = samples)

    validate_verify(input_paths = input_paths,
                    paired_end = config["GLDS"].getboolean("PairedEnd"),
                    count_lines_to_check = config["Options"].getint("MaxFastQLinesToCheck"))

    thresholds = dict()
    thresholds['avg_sequence_length'] = config['Raw'].getfloat("SequenceLengthVariationTolerance")
    thresholds['percent_gc'] = config['Raw'].getfloat("PercentGCVariationTolerance")
    thresholds['total_sequences'] = config['Raw'].getfloat("TotalSequencesVariationTolerance")
    thresholds['percent_duplicates'] = config['Raw'].getfloat("PercentDuplicatesVariationTolerance")

    raw_mqc = MultiQC(
            multiQC_out_path=config["Paths"].get("RawMultiQCDir"),
            samples=samples,
            paired_end=config["GLDS"].getboolean("PairedEnd"),
            outlier_thresholds=thresholds)
