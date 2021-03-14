#! /usr/bin/env python
""" Validation/Verification for raw reads in RNASeq Concensus Pipeline
"""
from __future__ import annotations
from collections import namedtuple, defaultdict
from pathlib import Path
import gzip
import statistics

from VV.utils import outlier_check, label_file, filevalues_from_mapping, MIDDLEPOINT_FUNC
from VV.flagging import Flagger
from seqpy import multiqc

def validate_verify(samples: list[str],
                    raw_reads_dir: Path,
                    params: dict,
                    flagger: Flagger,
                    file_mapping_substrings: dict[str, str] = {"_R1_":"forward", "_R2_":"reverse"},
                    ):
    """ Performs VV for raw reads for checks involving raw reads files directly
    """
    ##############################################################
    # SET FLAGGING OUTPUT ATTRIBUTES
    ##############################################################
    flagger.set_script(__name__)
    flagger.set_step("Raw Reads")
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
    lines_to_check = params["raw_reads"]["fastq_lines_to_check"]
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
    checkID = "R_0003"
    file_size_params = params["raw_reads"]["file_size"]
    value_alias = "Filesize (units:GB)"
    middlepoint_alias = params["middlepoint"]
    middlepoint_function = MIDDLEPOINT_FUNC[middlepoint_alias]
    def file_size(file: Path):
        """ Returns filesize for a Path object
        """
        return file.stat().st_size/float(1<<30)
    # compute file sizes
    filesize_mapping, all_filesizes = filevalues_from_mapping(file_mapping, file_size)

    # calculate middlepoint and standard deviation
    stdev = statistics.stdev(all_filesizes)
    middlepoint = middlepoint_function(all_filesizes)

    for sample in samples:
        for filelabel, value in filesize_mapping[sample].items():
            entity = f"{sample}:{filelabel}"
            flagged = False
            # global maximum threshold checks
            if file_size_params["max_thresholds"]:
                for threshold in sorted(file_size_params["max_thresholds"], reverse=True):
                    if value > threshold:
                        flagger.flag(   entity = entity,
                                        message = (f"{value_alias} is over threshold of {threshold}. "
                                                   f"[value: {value:.7f}][threshold: {threshold}]"
                                                   ),
                                        severity = file_size_params["max_thresholds"][threshold],
                                        checkID = checkID)
                        flagged = True
                        break # end check for this sample's filelabel (note: break here exists the threshold checks)

            # global minimum threshold checks
            if file_size_params["min_thresholds"]:
                for threshold in sorted(file_size_params["min_thresholds"]).items():
                    if value < threshold:
                        flagger.flag(   entity = entity,
                                        message = (f"{value_alias} is under threshold of {threshold}. "
                                                   f"[value: {value:.7f}][threshold: {threshold}]"
                                                   ),
                                        severity = file_size_params["min_thresholds"][threshold],
                                        checkID = checkID)
                        flagged = True
                        break # end check for this sample's filelabel (note: break here exists the threshold checks, most severe flag is caught)

            # outlier by standard deviation threshold checks
            if file_size_params["outlier_thresholds"]:
                if stdev == 0:
                    deviation = 0
                else:
                    deviation = abs(value - middlepoint)/stdev
                for threshold in sorted(file_size_params["outlier_thresholds"], reverse=True):
                    if deviation > threshold:
                        flagger.flag(   entity = entity,
                                        message = (f"{value_alias} flagged as outlier. "\
                                                  f"Exceeds {middlepoint_alias} by {threshold} standard deviations. "\
                                                  f"[value: {value:.7f}][deviation: {deviation:.7f}][threshold: {threshold}]"
                                                  ),
                                        severity = file_size_params["outlier_thresholds"][threshold],
                                        checkID = checkID)
                        flagged = True
                        break # end check for this sample's filelabel (note: break here exists the threshold checks, most severe flag is caught)

            if not flagged:
                flagger.flag(entity = entity,
                             message = f"No issues with {value_alias}. [value: {value:.7f}]",
                             severity = 30,
                             checkID = checkID)
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

def validate_verify_multiqc(samples: list[str],
                            multiqc_json: Path,
                            params: dict,
                            flagger: Flagger,
                            file_mapping_substrings: dict[str, str] = {"_R1_":"forward", "_R2_":"reverse"},
                            outlier_comparision_point: str = "median",
                            ):
    """ Performs VV for raw reads for checks involving multiqc json generated
            by raw reads fastqc aggregation
    """
    ##############################################################
    # SET FLAGGING OUTPUT ATTRIBUTES
    ##############################################################
    flagger.set_script(__name__)
    flagger.set_step("Raw Reads [MultiQC]")
    ##############################################################
    # STAGE MULTIQC DATA FROM JSON
    ##############################################################
    mqc = multiqc.MultiQC(multiQC_json = multiqc_json,
                          samples = samples,
                          file_mapping_substrings = file_mapping_substrings,
                          outlier_comparision_point = outlier_comparision_point)

    ### START R_1001 ##################################################
    # TODO: add paired read length match check (R_1001)
    checkID = "R_1001"
    for sample in samples:
        entity = sample
        # I.E: if the study is paired end
        if set(("forward", "reverse")) == set(mqc.file_labels):
            print(mqc.data[sample]["forward-avg_sequence_length"])
            print(mqc.data[sample]["reverse-avg_sequence_length"])
            pairs_match = mqc.data[sample]["forward-avg_sequence_length"].value == mqc.data[sample]["reverse-avg_sequence_length"].value
            if pairs_match:
                flagger.flag(entity = entity,
                             message = f"Average sequence lengths match between pairs",
                             severity = 30,
                             checkID = checkID)
            else:
                flagger.flag(entity = entity,
                             message = f"Average sequence lengths DO NOT match between pairs",
                             severity = 90,
                             checkID = checkID)
    ### DONE R_1001 ###################################################
