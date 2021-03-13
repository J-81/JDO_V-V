""" utility functions common to a number of operations to validation and
verification
"""
from typing import Tuple
from statistics import median, stdev

FLAG_LEVELS = {
    20:"Info-Only",
    30:"Passed-Green",
    50:"Warning-Yellow",
    60:"Warning-Red",
    70:"Issue-Terminate_Process"
    }

def outlier_check(value: float, against: list) -> [str]:
    """ For a dictionary of entity and a value.  Flag outliers with that are beyond a specified
        standard deviation threshold.

    :param value: Value to compute deviations for compared to full list of values
    :param against: Values to check for an outlier against
    """
    _median = median(against)
    _stdev = stdev(against)

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
