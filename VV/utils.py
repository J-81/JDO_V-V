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

from VV.flagging import Flagger
from VV import parameters
DEFAULT_PARAMS_FILE = parameters.__file__

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

def load_params(parameter_file: Path, parameter_set: str = None):
    """ if parameter_set is None, return all parameter sets as dictionary
    """
    if parameter_file != DEFAULT_PARAMS_FILE:
        from importlib import import_module
        custom_params_module = str(Path(parameter_file).name)[:-3] # remove .py
        sys.path.append(os.getcwd())
        CUSTOM_PARAMS = import_module(custom_params_module)
        PARAMS = CUSTOM_PARAMS.PARAMS
        print(f"Loaded custom parameter file located at {parameter_file}")
    else:
        from VV.parameters import PARAMS
        print(f"Using module's parameter file located at {parameter_file}")

    if not parameter_set:
        return PARAMS
    else:
        print(f"Loading parameter set '{parameter_set}'")
        try:
            params = PARAMS[parameter_set]
        except KeyError:
            print(f"Could not load! Check if {parameter_set} is in {parameter_file}")
            sys.exit(-1)
        return params

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

def value_based_checks(check_params: dict,
                       value_mapping: dict,
                       all_values: list,
                       flagger: Flagger,
                       checkID: str,
                       value_alias: str,
                       middlepoint: str):
    """ Performs checks and sends appropriate flag calls for a value.
    """
    # calculate middlepoint and standard deviation
    stdev = statistics.stdev(all_values)
    try:
        middlepoint_function = MIDDLEPOINT_FUNC[middlepoint]
    except KeyError:
        raise KeyError(f"Middlepoint named {middlepoint} not valid. Try from {list(MIDDLEPOINT_FUNC.keys())}")
    middlepoint = middlepoint_function(all_values)

    for sample in value_mapping.keys():
        for filelabel, value in value_mapping[sample].items():
            entity = f"{sample}:{filelabel}"
            flagged = False
            # global maximum threshold checks
            if check_params["max_thresholds"]:
                for threshold in sorted(check_params["max_thresholds"], reverse=True):
                    if value > threshold:
                        flagger.flag(   entity = entity,
                                        message = (f"{value_alias} is over threshold of {threshold}. "
                                                   f"[value: {value:.7f}][threshold: {threshold}]"
                                                   ),
                                        severity = check_params["max_thresholds"][threshold],
                                        checkID = checkID)
                        flagged = True
                        break # end check for this sample's filelabel (note: break here exists the threshold checks)

            # global minimum threshold checks
            if check_params["min_thresholds"]:
                for threshold in sorted(check_params["min_thresholds"]).items():
                    if value < threshold:
                        flagger.flag(   entity = entity,
                                        message = (f"{value_alias} is under threshold of {threshold}. "
                                                   f"[value: {value:.7f}][threshold: {threshold}]"
                                                   ),
                                        severity = check_params["min_thresholds"][threshold],
                                        checkID = checkID)
                        flagged = True
                        break # end check for this sample's filelabel (note: break here exists the threshold checks, most severe flag is caught)

            # outlier by standard deviation threshold checks
            if check_params["outlier_thresholds"]:
                if stdev == 0:
                    deviation = 0
                else:
                    deviation = abs(value - middlepoint)/stdev
                for threshold in sorted(check_params["outlier_thresholds"], reverse=True):
                    if deviation > threshold:
                        flagger.flag(   entity = entity,
                                        message = (f"{value_alias} flagged as outlier. "\
                                                  f"Exceeds {middlepoint:.7f} by {threshold} standard deviations. "\
                                                  f"[value: {value:.7f}][deviation: {deviation:.7f}][threshold: {threshold}]"
                                                  ),
                                        severity = check_params["outlier_thresholds"][threshold],
                                        checkID = checkID)
                        flagged = True
                        break # end check for this sample's filelabel (note: break here exists the threshold checks, most severe flag is caught)

            if not flagged:
                flagger.flag(entity = entity,
                             message = f"No issues with {value_alias}. [value: {value:.7f}]",
                             severity = 30,
                             checkID = checkID)

def value_check_direct(check_params: dict,
                       value: dict,
                       all_values: list,
                       flagger: Flagger,
                       checkID: str,
                       entity: str,
                       value_alias: str,
                       middlepoint: str,
                       message_prefix: str = None):
    """ Performs checks and sends appropriate flag calls for a value.
    """
    # calculate middlepoint and standard deviation
    stdev = statistics.stdev(all_values)
    try:
        middlepoint_function = MIDDLEPOINT_FUNC[middlepoint]
    except KeyError:
        raise KeyError(f"Middlepoint named {middlepoint} not valid. Try from {list(MIDDLEPOINT_FUNC.keys())}")
    middlepoint = middlepoint_function(all_values)

    flagged = False
    # global maximum threshold checks
    if check_params["max_thresholds"]:
        for threshold in sorted(check_params["max_thresholds"], reverse=True):
            if value > threshold:
                flagger.flag(   entity = entity,
                                message = (f"<{message_prefix}> {value_alias} is over threshold of {threshold}. "
                                           f"[value: {value:.7f}][threshold: {threshold}]"
                                           ),
                                severity = check_params["max_thresholds"][threshold],
                                checkID = checkID)
                flagged = True
                break # end check for this sample's filelabel (note: break here exists the threshold checks)

    # global minimum threshold checks
    if check_params["min_thresholds"]:
        ascending_thresholds = sorted(check_params["min_thresholds"])
        for threshold in ascending_thresholds:
            if value < threshold:
                flagger.flag(   entity = entity,
                                message = (f"<{message_prefix}> {value_alias} is under threshold of {threshold}. "
                                           f"[value: {value:.7f}][threshold: {threshold}]"
                                           ),
                                severity = check_params["min_thresholds"][threshold],
                                checkID = checkID)
                flagged = True
                break # end check for this sample's filelabel (note: break here exists the threshold checks, most severe flag is caught)

    # outlier by standard deviation threshold checks
    if check_params["outlier_thresholds"]:
        if stdev == 0:
            deviation = 0
        else:
            deviation = abs(value - middlepoint)/stdev
        for threshold in sorted(check_params["outlier_thresholds"], reverse=True):
            if deviation > threshold:
                flagger.flag(   entity = entity,
                                message = (f"<{message_prefix}> {value_alias} flagged as outlier. "\
                                          f"Exceeds {middlepoint:.7f} by {threshold} standard deviations. "\
                                          f"[value: {value:.7f}][deviation: {deviation:.7f}][threshold: {threshold}]"
                                          ),
                                severity = check_params["outlier_thresholds"][threshold],
                                checkID = checkID)
                flagged = True
                break # end check for this sample's filelabel (note: break here exists the threshold checks, most severe flag is caught)

    if not flagged:
        flagger.flag(entity = entity,
                     message = f"<{message_prefix}> No issues with {value_alias}. [value: {value:.7f}]",
                     severity = 30,
                     checkID = checkID)

def bytes_to_gb(bytes: int) -> float:
    """ utility function, converts bytes to gb

    :param bytes: bytes to convert
    """
    return bytes/float(1<<30)
