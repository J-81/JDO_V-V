""" utility functions common to a number of operations to validation and
verification
"""
from typing import Tuple
from statistics import median, stdev

FLAG_LEVELS = {
    20:"Info-Only",
    50:"Yellow-Warning",
    60:"Red-Warning",
    70:"Severe-Issue"
    }

def outlier_check(value: float, against: list) -> [str]:
    """ For a dictionary of entity and a value.  Flag outliers with that are beyond a specified
        standard deviation threshold.

    :param value: Value to compute deviations for compared to full list of values
    :param against: Values to check for an outlier against
    """
    _median = median(against)
    _stdev = stdev(against)

    return  abs(value - _median) / _stdev

def bytes_to_gb(bytes: int) -> float:
    """ utility function, converts bytes to gb

    :param bytes: bytes to convert
    """
    return bytes/float(1<<30)
