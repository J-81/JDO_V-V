""" utility functions common to a number of operations to validation and
verification
"""
from typing import Tuple, Callable
import statistics

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

def bytes_to_gb(bytes: int) -> float:
    """ utility function, converts bytes to gb

    :param bytes: bytes to convert
    """
    return bytes/float(1<<30)
