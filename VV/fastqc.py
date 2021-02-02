""" Validation and Verification for FastQC files generated through the RNASeq
pipeline.
"""
import os
import logging
log = logging.getLogger(__name__)

def validate_verify(samples: [str],
                    input_path: str,
                    paired_end: bool,
                    expected_suffix: str):
    """ Checks fastqc files match what is expected given a set of samples.

    :param samples: sample names, should be extracted from ISA file
    :param input_path: directory containing output from fastQC
    :param paired_end: True if paired end, False if single end reads
    :param expected_suffix: Added by fastQC (e.g. '_raw_fastqc')
    """
    # check if html files exists
    read_prefixes = [f"{sample}_R1" for sample in samples]
    if paired_end:
        read_prefixes.extend([f"{sample}_R2" for sample in samples])

    checkname = "FastQC file existence check"
    for prefix in read_prefixes:
        log.debug(f"Checking {prefix} FastQC files")
        expected_html_file = os.path.join(input_path, f"{prefix}{expected_suffix}.html")
        expected_zip_file = os.path.join(input_path, f"{prefix}{expected_suffix}.html")
        html_file_exists = os.path.isfile(expected_html_file)
        zip_file_exists = os.path.isfile(expected_zip_file)
        if not html_file_exists or not zip_file_exists:
           log.error(f"FAIL: {checkname}: "
                     f"html file: {expected_html_file}: {html_file_exists}: "
                     f"zip file: {expected_zip_file}: {zip_file_exists}"
                     )
        else:
            log.info(f"PASS: {checkname}")
