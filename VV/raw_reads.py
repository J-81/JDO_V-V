""" V-V for raw reads.

# TODO: add support for paired and single end inputs
"""
import statistics
import glob
import os
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



def _parse_samples(files: [str], paired_end: bool) -> [str]:
    """ Parses file names from raw read files

    This assumes the following file format:
        Mmus_BAL-TAL_LRTN_FLT_Rep5_F10_R2_raw.fastq.gz
        [SAMPLE NAME*****************][READ*].fastq.gz

    This also assumes that regardless of paired or single mode, there exists a
        file named: <SAMPLE NAME>_R1_raw.fastq.gz
        and <SAMPLE NAME> never includes "_R1_raw.fastq.gz"

    Args:
        files: compressed raw read files
        paired_end: flag indicating whether the data is paired ended or single

    Returns:

    """
    # extract basename from full paths
    fnames = [os.path.basename(f) for f in files]

    # extract sample names
    unique_samples = list(set([fname.replace("_R1_raw.fastq.gz","").replace("_R2_raw.fastq.gz","")
                               for fname in fnames]))

    return unique_samples

def _size_check(files: [str]) -> dict:
    """ Gets file size for input files.

    Args:
        files: compressed raw read files

    Returns:
        Dict: file:float(filesize in bytes)
    """
    return {f:_bytes_to_gb(os.path.getsize(f)) for f in files}

def _bytes_to_gb(bytes: int):
    """ utility function, converts bytes to gb
    """
    return bytes/float(1<<30)
