#! /usr/bin/env python
""" Validation/Verification for raw reads in RNASeq Concensus Pipeline
"""
from __future__ import annotations
from collections import namedtuple, defaultdict
from pathlib import Path
import gzip
import statistics

from VV.utils import outlier_check, label_file, filevalues_from_mapping, value_based_checks
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
    def file_size(file: Path):
        """ Returns filesize for a Path object
        """
        return file.stat().st_size/float(1<<30)
    # compute file sizes
    filesize_mapping, all_filesizes = filevalues_from_mapping(file_mapping, file_size)

    metric = "file_size"
    value_based_checks(check_params = params["raw_reads"][metric],
                       value_mapping = filesize_mapping,
                       all_values = all_filesizes,
                       flagger = flagger,
                       checkID = checkID,
                       value_alias = metric,
                       middlepoint = params["middlepoint"]
                       )
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
            forward_count = mqc.data[sample]["forward-total_sequences"].value
            reverse_count = mqc.data[sample]["reverse-total_sequences"].value
            pairs_match = forward_count == reverse_count
            if pairs_match:
                flagger.flag(entity = entity,
                             message = f"Total Count of reads matches between pairs.",
                             severity = 30,
                             checkID = checkID)
            else:
                flagger.flag(entity = entity,
                             message = f"Total Count of reads does NOT matches between pairs.",
                             severity = 90,
                             checkID = checkID)
    ### DONE R_1001 ###################################################

    ### START R_1002 ##################################################
    checkID = "R_1002"
    key = "fastqc_sequence_length_distribution_plot"
    try:
        mqc.data[samples[0]][f"{mqc.file_labels[0]}-{key}"]
        print(mqc.data[samples[0]][f"{mqc.file_labels[0]}-{key}"])
        1/0
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
    except KeyError:
        # this indicates the plot was not generated.
        # this happens when all average sequences are the same.
        # therefore this is a pass condition for the check
        for sample in samples:
            entity = sample
            flagger.flag(entity = entity,
                         message = ("Average sequence lengths across all samples matches. "\
                                   "Reason: MultiQC did not graph average sequence "\
                                   "lengths.  This happens when the graph is replace "\
                                   "with a message indicating 'All samples have "\
                                   "sequences of a single length'"),
                         severity = 30,
                         checkID = checkID)

    ### DONE R_1002 ###################################################
