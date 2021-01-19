""" V-V for raw reads.
"""
from typing import Tuple
import hashlib
import statistics
import glob
import os
import logging
log = logging.getLogger(__name__)

def validate_verify(input_path: str, paired_end: bool, md5sums: dict = {}):
    """Performs validation and verification for input of RNASeq datasets.
    Additionally checks for FastQC file existence.

    This assumes the following file format:

    |  ``Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R2_raw.fastq.gz``
    |  ``<SAMPLE NAME-----------------><READ->.fastq.gz``

    This also assumes that regardless of paired or single mode, there exists a file named:

    <SAMPLE NAME>_R1_raw.fastq.gz
    and <SAMPLE NAME> never includes "_R1_raw.fastq.gz"

    :param input_path: path where the raw read files are location
    :param paired_end: True for paired end, False for single reads
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
