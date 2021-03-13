#! /usr/bin/env python
""" Validation/Verification for raw reads in RNASeq Concensus Pipeline
"""
from __future__ import annotations
from collections import namedtuple, defaultdict
from pathlib import Path
import gzip

from VV.utils import outlier_check, label_file
from VV.flagging import Flagger

def validate_verify(samples: list[str],
                    raw_reads_dir: Path,
                    params: dict,
                    file_mapping_substrings: dict[str, str] = {"_R1_":"forward", "_R2_":"reverse"},
                    flagger: Flagger = Flagger(script=__name__),
                    ):
    """ Performs VV for raw reads for checks involving raw reads files directly
    """
    ##############################################################
    # SET FLAGGING OUTPUT ATTRIBUTES
    ##############################################################
    flagger.set_script(__name__)

    ##############################################################
    # GENERATE SAMPLE TO FILE MAPPING
    ##############################################################
    file_mapping = dict()
    for sample in samples:

        # set up each sample entry as a dictionary
        file_mapping[sample] = dict()

        for filename in raw_reads_dir.glob(f"{sample}*.fastq.gz"):
            file_label = label_file(str(filename), file_mapping_substrings)
            # file patterns for paired end studies
            # note: this may be replaced in the future using expected filenames specified in the ISA
            file_mapping[sample][file_label] = filename

    ###################################################################
    # PERFROM CHECKS
    ###################################################################

    ### START R_0001 ##################################################
    checkID = "R_0001"
    expected_file_lables = list(file_mapping_substrings.values())
    for sample in samples:
        missing_files = list()
        for file_label in expected_file_lables:
            if not file_label in file_mapping[sample].keys():
                missing_file.append(file_label)
        if len(missing_files) != 0:
            flagger.flag(entity = sample,
                         message = f"Missing expected files for {missing_files}",
                         severity = 90,
                         checkID = checkID)
        else:
            flagger.flag(entity = sample,
                         message = f"All expected files present: {expected_file_lables}",
                         severity = 30,
                         checkID = checkID)
    ### DONE R_0001 ###################################################

    ### START R_0002 ##################################################
    # TODO: add header check (R_0002)
    checkID = "R_0002"
    lines_to_check = params["fastq_lines_to_check"]
    for sample in samples:
        for filelabel, filename in file_mapping[sample].items():
            entity = f"{sample}:{filelabel}"
            passed, details = _check_headers(filename,
                                             count_lines_to_check = lines_to_check)
            if passed:
                flagger.flag(entity = entity,
                             message = f"File headers appear fine up to line {lines_to_check}",
                             severity = 30,
                             checkID = checkID)
            else:
                flagger.flag(entity = entity,
                             message = f"File headers not detected for {details}",
                             severity = 60,
                             checkID = checkID)
    ### DONE R_0002 ###################################################

    ### START R_0003 ##################################################
    # TODO: add file size checks (R_0003)
    ### DONE R_0003 ###################################################


def _check_headers(file, count_lines_to_check: int) -> int:
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

    # TODO: add expected length check
    expected_length = None

    lines_with_issues = list()

    passes = True
    message = ""
    with gzip.open(file, "rb") as f:
        for i, line in enumerate(f):
            # checks if lines counted equals the limit input
            if i+1 == count_lines_to_check:
                print(f"Reached {count_lines_to_check} lines, ending line check")
                break

            line = line.decode()
            # every fourth line should be an identifier
            expected_identifier_line = (i % 4 == 0)
            # check if line is actually an identifier line
            if (expected_identifier_line and line[0] != "@"):
                lines_with_issues.append(i+1)
                print(f"FAIL: {checkname}: "
                      f"Line {i+1} of {file} was not an identifier line as expected "
                      f"LINE {i+1}: {line}")
            # update every 20,000,000 reads
            if i % 20000000 == 0:
                print(f"Checked {i} lines for {file}")
    if len(lines_with_issues) != 0:
        passes = False
        message += f"for {file}, first ten lines with header issues: {lines_with_issues[0:10]} of {len(lines_with_issues)} header lines with issues: "
    else:
        message += f"for {file}, No issues with headers checked up to line {count_lines_to_check}: "
    return (passes, message)
