""" Stores configuration parameters for VV in python

    Top level objects should include all parameters for an entire VV process
    Final parameters must be in the following format: {FLAG_LEVEL : value}
    Empty dicts should be used to explicitly indicate no checks
"""
DEFAULT_PARAMS = \
{
    "raw_reads": {
        "fastq_lines_to_check" : 10000,
        "sequence_length" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                60 : 0,
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
