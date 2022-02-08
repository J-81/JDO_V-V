""" Validation and Verification for FastQC files generated through the RNASeq
pipeline.
"""
from __future__ import annotations
import os

from VV.flagging import Flagger

def validate_verify(samples: [str],
                    input_path: str,
                    flagger: Flagger,
                    file_mapping_substrings: dict[str, str] = {"_R1_":"forward", "_R2_":"reverse"},
                    ):
    """ Checks fastqc files match what is expected given a set of samples.

    :param samples: sample names, should be extracted from ISA file
    :param input_path: directory containing output from fastQC
    :param file_mapping_substrings: Added by fastQC (e.g. '_raw_fastqc')
    """
    # check if html and zip files exists
    check_id = "FastQC file existence check"
    for sample in samples:
        expected_html_file = os.path.join(input_path, f"{prefix}{expected_suffix}.html")
        expected_zip_file = os.path.join(input_path, f"{prefix}{expected_suffix}.html")
        html_file_exists = os.path.isfile(expected_html_file)
        zip_file_exists = os.path.isfile(expected_zip_file)
        if not html_file_exists or not zip_file_exists:
            Flagger.flag(debug_message=f"Missing {expected_html_file} and/or {expected_zip_file}",
                         entity=sample,
                         severity=90,
                         check_id="F_0001")
        else:
            Flagger.flag(debug_message=f"Missing {expected_html_file} and/or {expected_zip_file}",
                         entity=sample,
                         severity=30,
                         check_id="F_0001")
