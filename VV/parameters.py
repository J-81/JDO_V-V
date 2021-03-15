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
        "fastqc_per_base_sequence_quality_plot" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                2 : 50,
                3 : 60,
            },
        },
        "fastqc_per_sequence_quality_scores_plot" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                2 : 50,
                3 : 60,
            },
        },
        "fastqc_per_sequence_gc_content_plot-Percentages" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                2 : 50,
                4 : 60,
            },
        },
        "fastqc_per_base_n_content_plot" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                1 : 50,
                2 : 60,
            },
        },
        "fastqc_sequence_duplication_levels_plot" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                2 : 60,
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
                40 : 50,
            },
            "min_thresholds" : {},
            "outlier_thresholds" : {
                4 : 60,
                2 : 50,
            },
        },
        "percent_gc" :{
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                4 : 60,
                2 : 50,
            },
        },
    },
    "trimmed_reads": {
        "fastq_lines_to_check" : 15000,
        "sequence_length" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                0 : 60,
            },
        },
        "sequence_length_dist" : {
            "max_thresholds" : {},
            "min_thresholds" : {},
            "outlier_thresholds" : {
                4 : 60,
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
}
