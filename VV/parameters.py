""" Stores configuration parameters for VV in python

    Top level objects should include all parameters for an entire VV process
    Final parameters must be in the following format: {value: FLAG_LEVEL}
    Empty dicts should be used to explicitly indicate no checks
"""
DEFAULT_PARAMS = \
{
    "middlepoint": "median",
    "raw_reads": {
        "fastq_lines_to_check" : 10000,
        "sequence_length" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                0 : 60,
            },
        },
        "file_size" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                2 : 50,
                4 : 60,
            },
        },
        "percent_duplicates" :{
            "max_thresholds" : {
                60 : 60,
                50 : 40,
            },
            "min_thresholds" : {},
            "outlier_thresholds" : {
                60 : 4,
                50 : 2,
            },
        },
    },
    "trimmed_reads": {
        "sequence_length" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                60 : 1,
            },
        },
    },
}
