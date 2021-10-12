""" Stores configuration cutoffs for VV in python

    Top level objects should include all cutoffs for an entire VV process
    Final cutoffs must be in the following format: {value: FLAG_LEVEL}
    Empty dicts should be used to explicitly indicate no checks
"""
# TOP LEVEL MUST BE NAMED CUTOFFS
CUTOFFS = \
{
    "DEFAULT_RNASEQ" : {
        "raw_reads": {
            "middlepoint": "median",
            "fastq_lines_to_check" : 4000000,
            "sequence_length" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    0 : 60,
                },
            },
            "fastqc_sequence_length_distribution_plot" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
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
                "bin_sum" : {
                    "max_thresholds" : {},
                    "min_thresholds" : {},
                    "outlier_thresholds" : {
                        1 : 50,
                        2 : 60,
                    },
                },
                "bin_mean" : {
                    "max_thresholds" : {
                        8 : 60,
                        3 : 50,
                    },
                    "min_thresholds" : {},
                    "outlier_thresholds" : {},
                },
            },
            "fastqc_sequence_duplication_levels_plot" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 60,
                },
            },
            "fastqc_overrepresented_sequencesi_plot-Top over-represented sequence" : {
                "max_thresholds" : {
                    40 : 49,
                    60 : 59,
                },
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 50,
                    4 : 60,
                },
                "sample_proportion_thresholds" : {
                    60 : 0.80,
                    50 : 0.80,
                },
            },
            "fastqc_overrepresented_sequencesi_plot-Sum of remaining over-represented sequences" : {
                "max_thresholds" : {
                    40 : 49,
                    60 : 59
                },
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 50,
                    4 : 60,
                },
                "sample_proportion_thresholds" : {
                    60 : 0.80,
                    50 : 0.80,
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
        "rseqc": {
            "middlepoint": "median",
            "rseqc_infer_experiment_plot-Sense" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
                },
            },
            "rseqc_infer_experiment_plot-Antisense" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
                },
            },
            "rseqc_infer_experiment_plot-Undetermined" : {
                "max_thresholds" : {
                    0.4 : 60,
                    0.2 : 50,
                    },
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
                },
            },
        },
        "trimmed_reads": {
            "middlepoint": "median",
            "fastq_lines_to_check" : 4000000,
            "sequence_length" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    0 : 60,
                },
            },
            "fastqc_sequence_length_distribution_plot" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
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
                    60 : 4,
                    50 : 2,
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
            "fastqc_overrepresented_sequencesi_plot-Top over-represented sequence" : {
                "max_thresholds" : {
                    40 : 49,
                    60 : 59,
                },
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 50,
                    4 : 60,
                },
                "sample_proportion_thresholds" : {
                    60 : 0.80,
                    50 : 0.80,
                },
            },
            "fastqc_overrepresented_sequencesi_plot-Sum of remaining over-represented sequences" : {
                "max_thresholds" : {
                    40 : 49,
                    60 : 59
                },
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 50,
                    4 : 60,
                },
                "sample_proportion_thresholds" : {
                    60 : 0.80,
                    50 : 0.80,
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
                "bin_sum" : {
                    "max_thresholds" : {},
                    "min_thresholds" : {},
                    "outlier_thresholds" : {
                        1 : 50,
                        2 : 60,
                    },
                },
                "bin_mean" : {
                    "max_thresholds" : {
                        8 : 60,
                        3 : 50,
                    },
                    "min_thresholds" : {},
                    "outlier_thresholds" : {},
                },
            },
            "fastqc_sequence_duplication_levels_plot" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 60,
                },
            },
            "fastqc_adapter_content_plot" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    1 : 50,
                    2 : 60,
                },
                "bin_sum" : {
                    "max_thresholds" : {},
                    "min_thresholds" : {},
                    "outlier_thresholds" : {
                        1 : 50,
                        2 : 60,
                    },
                },
                "bin_mean" : {
                    "max_thresholds" : {
                        8 : 60,
                        3 : 50,
                    },
                    "min_thresholds" : {},
                    "outlier_thresholds" : {},
                },
            },

        },
        "STAR" : {
            "middlepoint": "median",
            "total_reads_mapped-Percentage" : {
                "max_thresholds" : {},
                "min_thresholds" : {
                    50 : 60,
                    70 : 50,
                },
                "outlier_thresholds" : {},
                "sample_proportion_thresholds" : {
                    60 : 0.80,
                    50 : 0.80,
                },
            },
            "mapped_to_multiple_loci-Percentage" : {
                "max_thresholds" : {},
                "min_thresholds" : {
                    15 : 60,
                    30 : 50,
                },
                "outlier_thresholds" : {},
                "sample_proportion_thresholds" : {
                    60 : 0.80,
                    50 : 0.80,
                },
            },
        },
        "RSEM" : {
            "middlepoint": "median",
            "number_of_unique_genes_expressed" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
                },
                "sample_proportion_thresholds" : {},
            },
            "count_of_unique_isoforms_expressed" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
                },
                "sample_proportion_thresholds" : {},
            },
            "number_of_ERCC_genes_detected" : {
                "max_thresholds" : {},
                "min_thresholds" : {
                    1 : 60,
                },
                "outlier_thresholds" : {
                    4 : 60,
                    2 : 50,
                },
                "sample_proportion_thresholds" : {},
            },
        },
    },
    "DEFAULT_MICROARRAY" : {
        "raw_files" : {
            "middlepoint": "median",
            "file_size" : {
                "max_thresholds" : {},
                "min_thresholds" : {},
                "outlier_thresholds" : {
                    2 : 50,
                    4 : 60,
                },
            },
        },
        "normalized_data" : {
            "middlepoint": "median",
        },
        "limma_dge" : {
            "middlepoint": "median",
        },
    },
}
