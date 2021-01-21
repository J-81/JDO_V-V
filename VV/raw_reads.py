""" V-V for raw reads.
"""
from collections import namedtuple
from typing import Tuple
import hashlib
import statistics
import glob
import os
import gzip
import logging
log = logging.getLogger(__name__)

# information extracted from raw reads V-V
# used to check against other sources of information including ISA file.
rawReadsInfo = namedtuple("rawReadsInfo", "sample_names")

def validate_verify(input_path: str, paired_end: bool, md5sums: dict = {}):
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

    :param input_path: path where the raw read files are location
    :param paired_end: True for paired end, False for single reads
    :param md5sums: dictionary of raw read file to md5sum, e.g. Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_raw.fastq.gz : b21ca61d56208d49b9422a1306d0a0f1
    """
    log.debug(f"Processing Paired End: {paired_end}")

    # load files from input_path
    files = glob.glob(os.path.join(input_path, "Fastq", "*fastq.gz"))
    log.info(f"{len(files)} Raw Read Files, example: {files[0]}")
    log.debug(files)

    # get compressed files sizes and log max,min,median
    file_sizes = _size_check(files)
    log.info(f"Max    file size: {max(file_sizes.values()):.3} GB")
    log.info(f"Median file size: {statistics.median(file_sizes.values()):.3} GB")
    log.info(f"Min    file size: {min(file_sizes.values()):.3} GB")
    log.debug(f"All file sizes (in GB): {file_sizes}")


    # extract sample names
    sample_names = _parse_samples(files, paired_end)
    log.info(f"{len(sample_names)} Samples, example: {sample_names[0]}")
    log.debug(f"Samples: {sample_names}")

    #  check if number of raw files is appropriate
    check_name = "Raw Read File Number Check"
    for sample in sample_names:
        R1_count, R2_count = _file_counts_check(files, sample)
        if (paired_end and R1_count == 1 and R2_count == 1):
            log.info(f"PASS: {check_name}:"
                     f"Found both forward and reverse read files for {sample}")
        elif (not paired_end and R1_count == 1 and R2_count == 0):
            log.info(f"PASS: {check_name}:"
                     f"Found R1 read file for {sample}")
        else:
            log.error(f"FAIL: {check_name}:"
                      f"Incorrect number of files, R1:{R1_count}, R2:{R2_count} for {sample}")

    # check lines of files
    for file in files:
        _check_fastq_content(file)


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

    # count fastqc files
    if paired_end:
        expected_count = 2
    else:
        expected_count = 1

    log.info(f"Checking expected FastQC files counts")
    for sample in sample_names:
        html_count, zip_count = _count_fastqc_files_by_sample(sample,
                                                              path=f"{input_path}/FastQC_Reports")
        if html_count != expected_count:
            log.error(f"Expected {expected_count} html files for {sample}, found {html_count}")
        if zip_count != expected_count:
            log.error(f"Expected {expected_count} zip  files for {sample}, found {zip_count}")
    log.info(f"Finished checking expected FastQC files counts")

    return rawReadsInfo(sample_names = set(sample_names))

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

def _check_fastq_content(file: str) -> int:
    """ Checks fastq lines for expected header content

    Note: Example of header from GLDS-194

    |  ``@J00113:376:HMJMYBBXX:3:1101:26666:1244 1:N:0:NCGCTCGA\n``

    This also assumes the fastq file does NOT split sequence or quality lines
    for any read

    :param file: compressed fastq file to check
    """
    #SKIP_INTERVAL = 2

    checkname = "FastQ Lines Check"
    expected_length = None
    with gzip.open(file, "rb") as f:
        for i, line in enumerate(f):
            # only check every fifth line to save time checking
            #if i % SKIP_INTERVAL != 0:
            #    continue

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
    return

def _parse_samples(files: [str], paired_end: bool) -> [str]:
    """ Parses file names from raw read files

    :param files: compressed raw read files
    :param paired_end: flag indicating whether the data is paired ended or single
    """
    # extract basename from full paths
    fnames = [os.path.basename(f) for f in files]

    # extract sample names
    unique_samples = list(set([fname.replace("_R1_raw.fastq.gz","").replace("_R2_raw.fastq.gz","")
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

def _count_fastqc_files_by_sample(sample: str, path: str) -> Tuple[int, int]:
    """ Counts the fastqc output files for a given sample

    Args:
        sample: unique sample name
        path: directory to search for fastqc files

    Returns:
        (html_count, zip_count)
    """
    html_count = len(glob.glob(os.path.join(path, f"{sample}*.html")))
    zip_count = len(glob.glob(os.path.join(path, f"{sample}*.zip")))
    return (html_count, zip_count)
