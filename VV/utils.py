""" utility functions common to a number of operations to validation and
verification
"""
from typing import Tuple
from statistics import median, stdev

def samplename_to_filenames(sample: str, paired_end: str) -> [str]:
    """ Converts samplename to expected filenames.
    Currently based on naming in GLDS-194.

    :param sample: sample name
    :param paired_end: returns both forward and reverse reads names if True.
    """
    forward_read_filename = f"{sample}_R1_raw.fastq.gz"
    reverse_read_filename = f"{sample}_R2_raw.fastq.gz"
    if not paired_end:
        return [forward_read_filename]
    else:
        return [forward_read_filename, reverse_read_filename]

def max_median_mean(values: [float]) -> Tuple[float, float, float]:
    """ Return max median and mean for a set of values

    :param values: Values to retrieve stats for
    """
    return max(values), median(values), min(values)


def sampleWise_outlier_check(samples: dict, outlier_stdev: float) -> [str]:
    """ For a dictionary of samples and a value.  Flag outliers with that are beyond a specified
        standard deviation threshold.

    :param samples: Sample and associated values to check for outliers
    :param outlier_stdev: How many standard deviations away from the median needed to flag as an outlier
    """
    outliers = list()
    _median = median(samples.values())
    _stdev = stdev(samples.values())
    _max_value = _median + _stdev*outlier_stdev
    _min_value = _median - _stdev*outlier_stdev

    for sample, value in samples.items():
        if _max_value >= value >= _min_value:
            continue
        else:
            outliers.append((read, value))

    return outliers


def readsWise_outlier_check(reads: dict, outlier_stdev: float):
    """ For a dictionary of read_files and a value.  Flag outliers with that are beyond a specified
        standard deviation threshold.

    :param reads: Reads and associated values to check for outliers
    :param outlier_stdev: How many standard deviations away from the median needed to flag as an outlier
    """
    outliers = list()
    _median = median(reads.values())
    _stdev = stdev(reads.values())
    _max_value = _median + _stdev*outlier_stdev
    _min_value = _median - _stdev*outlier_stdev

    for read, value in reads.items():
        if _max_value >= value >= _min_value:
            continue
        else:
            outliers.append((read, value))

    return outliers


def extract_samplename(name: str) -> Tuple[str, str, str, str]:
    """ Attempts to extract samplename from a filename.
    Expects GLDS-194 style naming.

    Example:
    Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R2_trimmed_fastqc.html
    11111111111111111111111111111_22_33333333333333.4444

    Assumptions:
    - Only R1 or R2 are length 2 substrings, with the exception of the extension

    1 - Sample name
    2 - Read indicator, forward or reverse
    3 - Suffix, often attached by a program, tracks modifications includuing trimming
    4 - file extension

    Returns these as tuple (1,2,3,4)
    """
    split_by = "_"
    tokens = name.split(split_by)
    sample = str()
    read = None
    suffix = str()
    for i, token in enumerate(tokens):
        if read:
            if "." in token:
                subtokens = token.split(".")
                extension = "." + subtokens[1]
                suffix += split_by + subtokens[0]
            else:
                suffix += token
            continue
        if token in ["R1","R2"]:
            read = token
        else:
            if sample:
                sample += split_by + token
            else:
                sample += token
    return (sample,read,suffix,extension)

def bytes_to_gb(bytes: int) -> float:
    """ utility function, converts bytes to gb

    :param bytes: bytes to convert
    """
    return bytes/float(1<<30)

# Test
if __name__ == "__main__":
    print("Testing function: extract_samplename")
    Test_Fastqc_html_raw = "Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R2_raw_fastqc.html"
    expected = ("Mmus_BAL-TAL_LRTN_FLT_Rep4_F9","R2","raw_fastqc",".html")
    results = extract_samplename("Mmus_BAL-TAL_LRTN_FLT_Rep4_F9_R2_raw_fastqc.html")
    assert expected == results
    print("Test Passed")
