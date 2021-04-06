""" utility functions common to a number of operations to validation and
verification
"""
from __future__ import annotations
import sys
import os
from typing import Tuple, Callable
import statistics
import configparser
from pathlib import Path
import gzip

from VV.flagging import Flagger
from VV.multiqc import MultiQC

FLAG_LEVELS = {
    20:"Info-Only",
    30:"Passed-Green",
    50:"Warning-Yellow",
    60:"Warning-Red",
    70:"Issue-Terminate_Process"
    }

MIDDLEPOINT_FUNC = {
    "median":statistics.median,
    "mean":statistics.mean
    }

def load_config(config_files: list[str]):
    missing_config = False
    for config_file in config_files:
        if not Path(config_file).is_file():
            print(f"ERROR: Config file does not exist: {config_file}")
            missing_config = True

    if missing_config:
        # exit with errror if any config files missing
        print(f"Missing config files, exiting program")
        sys.exit(1)
    else:
        # read in config files
        config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        print(f"Loading the following config files: {config_files}")
        config.read(config_files)
    return config

def load_cutoffs(cutoffs_file: Path = None, cutoffs_set: str = None):
    """ if cutoffs_set is None, return all cutoffs sets as dictionary.

    By default loads the module packaged cutoffs file and DEFAULT cutoffs set from the file.

    """
    if cutoffs_file:
        from importlib import import_module
        custom_cutoffs_module = str(Path(cutoffs_file).name)[:-3] # remove .py
        sys.path.append(os.getcwd())
        CUSTOM_CUTOFFS = import_module(custom_cutoffs_module)
        CUTOFFS = CUSTOM_CUTOFFS.CUTOFFS
        print(f"Loaded custom cutoffs file located at {cutoffs_file}")
    else:
        from VV import cutoffs
        CUTOFFS = cutoffs.CUTOFFS
        print(f"Using module's cutoffs file located at {cutoffs.__file__}")

    if not cutoffs_set:
        return CUTOFFS
    else:
        print(f"Loading cutoffs set '{cutoffs_set}'")
        try:
            cutoffs = CUTOFFS[cutoffs_set]
        except KeyError:
            print(f"Could not load! Check if {cutoffs_set} is in {cutoffs_file}")
            sys.exit(-1)
        return cutoffs

def label_file(filename: str, file_substring_mapping: dict):
    """ Given a filename.  Return the file label based on a unique substring.

    Substrings to file label mapping should be provided at init.
    """
    matched = False
    for substring, filelabel in file_substring_mapping.items():
        if substring in filename:
            if not matched:
                matched = filelabel
            else:
                raise ValueError(f"File name {filename} matched multiple substrings in provided mapping {file_substring_mapping}")
    if matched:
        return matched
    else:
        # no matches
        raise ValueError(f"File name {filename} did not match any substrings in provided mapping {file_substring_mapping}")


def outlier_check(value: float, against: list) -> [str]:
    """ For a dictionary of entity and a value.  Flag outliers with that are beyond a specified
        standard deviation threshold.

    :param value: Value to compute deviations for compared to full list of values
    :param against: Values to check for an outlier against
    """
    _median = statistics.median(against)
    _stdev = statistics.stdev(against)

    # account for zero _stdev,
    # in these cases there should be no outliers (all values are the same)
    # deviation should be computed as zero
    if _stdev == 0:
        return 0
    return  abs(value - _median) / _stdev

def filevalues_from_mapping(file_mapping: dict,
                            file_func: Callable):
    """ Returns outliers from the typical file mapping structure.
    Example:
        file_mapping = {
            sample1: {
                filelabel1 : file,
                filelabel2 : file
                }
            sample2: {
                filelabel1 : file,
                filelabel2 : file
                }
            }
    :param file_mapping: two depth nested dictionary (see example above)
    :param file_func: a function to be applied to each file, must return a numeric value
    """
    # first, iterate to get all values as a list
    # and map values in same nested dictionary format
    # (with the value replacing the filepath)
    all_values = list()
    file_value_mapping = dict()
    for sample, sample_mapping in file_mapping.items():
        file_value_mapping[sample] = dict()
        for filelabel, file in sample_mapping.items():
            try:
                file_value = float(file_func(file))
            except TypeError:
                raise TypeError(f"Error: {file_func} MUST return a numeric value.  Value returned: {file_value}. File: {file}")
            all_values.append(file_value)
            file_value_mapping[sample][filelabel] = file_value

    return file_value_mapping, all_values

def get_stdev_middle(all_values, middlepoint):
    """ calculate middlepoint and standard deviation """
    stdev = statistics.stdev(all_values)
    try:
        middlepoint_function = MIDDLEPOINT_FUNC[middlepoint]
    except KeyError:
        raise KeyError(f"Middlepoint named {middlepoint} not valid. Try from {list(MIDDLEPOINT_FUNC.keys())}")
    middlepoint = middlepoint_function(all_values)
    return stdev, middlepoint

def value_based_checks(partial_check_args: dict,
                       check_cutoffs: dict,
                       value_mapping: dict,
                       all_values: list,
                       flagger: Flagger,
                       value_alias: str,
                       middlepoint: str):
    """ Performs checks and sends appropriate flag calls for a value.
    """
    for sample in value_mapping.keys():
        partial_check_args["entity"] = sample
        for filelabel, value in value_mapping[sample].items():
            partial_check_args["sub_entity"] = filelabel
            value_check_direct(value = value,
                               all_values = all_values,
                               check_cutoffs = check_cutoffs[value_alias],
                               flagger = flagger,
                               partial_check_args = partial_check_args,
                               value_alias = value_alias,
                               middlepoint = check_cutoffs["middlepoint"]
                               )

def check_fastq_headers(file, count_lines_to_check: int) -> int:
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
    debug_message = ""
    # truncated files raise EOFError
    try:
        with gzip.open(file, "rb") as f:
            for i, line in enumerate(f):
                # checks if lines counted equals the limit input
                if i+1 == count_lines_to_check:
                    #print(f"Reached {count_lines_to_check} lines, ending line check")
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
                    #print(f"Checked {i} lines for {file}")
                    pass
        if len(lines_with_issues) != 0:
            passes = False
            debug_message += f"for {file}, first ten lines with header issues: {lines_with_issues[0:10]} of {len(lines_with_issues)} header lines with issues: "
        else:
            debug_message += f"for {file}, No issues with headers checked up to line {count_lines_to_check}: "
        return (passes, debug_message)
    except EOFError:
        return (-1, "EOFError raised, this indicates files may be corrupted")

def general_mqc_based_check(flagger: Flagger,
                            samples: list,
                            mqc: MultiQC,
                            cutoffs: dict,
                            check_id: str,
                            mqc_base_key: str,
                            aggregation_function: Callable = None,
                            cutoffs_subkey: str = None, # usually a string that references aggregation function
                            by_indice: bool = False,
                            allow_missing_base_key: bool = False # this can happen in the case of plots like the fastqc adaptor and length dist plot.  Typically a missing key indicates the plot was not needed due to some positive reason. e.g. all sequence lengths were the same
                            ):
    try:
        check_cutoffs = cutoffs[mqc_base_key][cutoffs_subkey] if cutoffs_subkey else cutoffs[mqc_base_key]
    except KeyError:
        raise ValueError("ERROR: Could not find {mqc_base_key} in cutoffs! Ensure this exists")
    check_args = dict()
    check_args["check_id"] = check_id
    # handle allow missing base keys
    if allow_missing_base_key and not mqc.data[samples[0]].get(f"{mqc.file_labels[0]}-{mqc_base_key}"):
        # this block indicates a special pass case
        for sample in samples:
            check_args["entity"] = sample
            check_args["severity"] = 30
            check_args["debug_message"] = f"Missing plot under {mqc_base_key}.  This check automatically passes in this case as this means the plot was replaced with a message indicating no issues in multiQC"
            check_args["user_message"] = f"No issues for {mqc_base_key}."
            flagger.flag(**check_args)
            return # exit function
    # iterate through each sample:file_label
    # test against all values from all file-labels
    for sample in samples:
        check_args["entity"] = sample
        for file_label in mqc.file_labels:
            check_args["sub_entity"] = file_label
            check_args["outlier_comparison_type"] = "Across-Samples:By-File_Label"
            # used to access the label wise values
            full_key = f"{file_label}-{mqc_base_key}"
            if not by_indice:
                # note: this is just the sample to check for outliers!
                value = mqc.compile_subset(samples_subset = [sample], key = full_key, aggregator = aggregation_function)
                # additional unpacking if aggregator used
                if isinstance(value,list):
                    assert len(value) == 1, "Aggregation should return more than one value!"
                     # an error here may indicate an issue generating a single value from the compile subset arg
                    value = float(value[0])
                # this is all values from all samples and the same filelabel
                all_values = mqc.compile_subset(samples_subset = samples, key = full_key, aggregator = aggregation_function)
                check_args["entity_value"] = value
                value_check_direct(value = value,
                                   all_values = all_values,
                                   check_cutoffs = check_cutoffs,
                                   flagger = flagger,
                                   partial_check_args = check_args,
                                   value_alias = mqc_base_key,
                                   middlepoint = cutoffs["middlepoint"])
            elif by_indice:
                flagged = False
                bin_units = mqc.data[sample][full_key].bin_units
                check_args["outlier_comparison_type"] = "Across-Samples:By-File_Label:By-Bin"
                # iterate through thresholds in descending order (more severe first)
                thresholds = sorted(check_cutoffs["outlier_thresholds"], reverse=True)
                check_args["outlier_thresholds"] = check_cutoffs["outlier_thresholds"]
                for threshold in thresholds:
                    outliers = mqc.detect_outliers(key = full_key,
                                                   deviation = threshold
                                                  )
                    check_args["flagged_positions"] = [str(index) for _sample,index,_ in outliers if _sample == sample]
                    # check if any outliers actually found for this sample
                    if len(check_args["flagged_positions"]) != 0:
                        check_args["debug_message"] = f"Outliers detected by {bin_units}"
                        check_args["severity"] = check_cutoffs["outlier_thresholds"][threshold]
                        flagger.flag(**check_args)
                        flagged = True
                        # if one threshold is flagged
                        # the rest will flagged (because descending order)
                        # so we break out of checks
                        break
                # log passes
                if not flagged:
                    check_args["debug_message"] = f"All {bin_units} bins pass max, min, and outliers checks"
                    check_args["severity"] = 30
                    flagger.flag(**check_args)

def value_check_direct(partial_check_args: dict,
                       check_cutoffs: dict,
                       value: float,
                       all_values: list,
                       flagger: Flagger,
                       value_alias: str,
                       middlepoint: str
                       ):
    """ Performs checks and sends appropriate flag calls for a value.
    """
    stdev, middlepoint = get_stdev_middle(all_values, middlepoint)
    ####################################################
    # populate template check args with cutoffs
    template_check_args = partial_check_args.copy()
    if check_cutoffs["max_thresholds"]:
        template_check_args["max_thresholds"] = check_cutoffs["max_thresholds"]

    if check_cutoffs["min_thresholds"]:
        template_check_args["min_thresholds"] = check_cutoffs["min_thresholds"]

    if check_cutoffs["outlier_thresholds"]:
        template_check_args["outlier_thresholds"] = check_cutoffs["outlier_thresholds"]
    # TEMPLATE READY
    ####################################################
    flagged = False
    # global maximum threshold checks
    if check_cutoffs["max_thresholds"]:
        check_args = template_check_args.copy()
        for threshold in sorted(check_cutoffs["max_thresholds"], reverse=True):
            if value > threshold:
                check_args["debug_message"] = f"{value_alias} exceeds max threshold"
                check_args["severity"] = check_cutoffs["max_thresholds"][threshold]
                flagger.flag(**check_args)
                flagged = True
                break # end all checks for this value

    # global minimum threshold checks
    if check_cutoffs["min_thresholds"]:
        check_args = template_check_args.copy()
        ascending_thresholds = sorted(check_cutoffs["min_thresholds"])
        for threshold in ascending_thresholds:
            if value < threshold:
                check_args["debug_message"] = f"{value_alias} is under min threshold"
                check_args["severity"] = check_cutoffs["min_thresholds"][threshold]
                flagger.flag(**check_args)
                flagged = True
                break # end all checks for this value

    # global minimum thres
    # outlier by standard deviation threshold checks
    if check_cutoffs["outlier_thresholds"]:
        check_args = template_check_args.copy()
        if stdev == 0:
            deviation = 0
        else:
            deviation = abs(value - middlepoint)/stdev
        for threshold in sorted(check_cutoffs["outlier_thresholds"], reverse=True):
            if deviation > threshold:
                check_args["debug_message"] = f"{value_alias} outlier"
                check_args["severity"] = check_cutoffs["outlier_thresholds"][threshold]
                flagger.flag(**check_args)
                flagged = True
                break # end all checks for this value

    if not flagged:
        check_args = template_check_args.copy()
        check_args["debug_message"] = f"{value_alias} passes max, min, and outliers checks"
        check_args["severity"] = 30
        flagger.flag(**check_args)

def bytes_to_gb(bytes: int) -> float:
    """ utility function, converts bytes to gb

    :param bytes: bytes to convert
    """
    return bytes/float(1<<30)
