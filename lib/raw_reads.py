""" V-V for raw reads.

# TODO: add support for paired and single end inputs
"""
import glob
import logging
log = logging.getLogger(__name__)

def VV(input_path: str, paired_end: bool):
    """ Performs validation and verification for input of RNASeq datasets

    Args:
        input_path: path where the raw read files are location
        paried_end: True for paired end, False for single reads
    """
    log.debug(f"Processing Paired End: {paired_end}")

    # load files from input_path
    files = glob.glob(f"{input_path}/*fastq.gz")
    log.info(files)
