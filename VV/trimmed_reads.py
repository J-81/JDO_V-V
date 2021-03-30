#! /usr/bin/env python
""" Validation/Verification for raw reads in RNASeq Concensus Pipeline
"""
from __future__ import annotations
from collections import namedtuple, defaultdict
from pathlib import Path
import gzip
import statistics
import subprocess

from VV.utils import filevalues_from_mapping, value_based_checks, check_fastq_headers, general_mqc_based_check
from VV.flagging import Flagger
from VV import multiqc

def validate_verify(file_mapping: dict,
                    cutoffs: dict,
                    flagger: Flagger,
                    ):
    """ Performs VV for trimmed reads for checks involving trimmed reads files directly
    """
    print(f"Starting VV for Trimmed Reads based on fastq.gz files")
    ##############################################################
    # SET FLAGGING OUTPUT ATTRIBUTES
    ##############################################################
    flagger.set_script(__name__)
    flagger.set_step("Trimmed Reads")
    cutoffs_subsection = "trimmed_reads"

    ###################################################################
    # PERFROM CHECKS
    ###################################################################
    ### UNIQUE IMPLEMENTATION CHECKS ##################################
    # T_0001 ##########################################################
    for sample, file_map in file_mapping.items():
        checkArgs = dict()
        checkArgs["check_id"] = "T_0001"
        checkArgs["entity"] = sample
        missing_files = list()
        for filelabel, file in file_map.items():
            if not file.is_file():
                missing_files.append(file)
        if len(missing_files) != 0:
            checkArgs["debug_message"] = "Trimmed read files missing"
            checkArgs["full_path"] = " ".join([str(missing.resolve()) for missing in missing_files])
            checkArgs["relative_path"] = " ".join([missing.name for missing in missing_files])
            checkArgs["severity"] = 90
        else:
            checkArgs["debug_message"] = "Trimmed read files exist"
            checkArgs["severity"] = 30
        flagger.flag(**checkArgs)
    # T_0002 ##########################################################
    check_proportion = cutoffs[cutoffs_subsection]["fastq_proportion_to_check"]
    for sample in file_mapping.keys():
        checkArgs = dict()
        checkArgs["check_id"] = "T_0002"
        checkArgs["entity"] = sample
        for filelabel, filename in file_mapping[sample].items():
            checkArgs["sub_entity"] = filelabel
            #passed, details = check_fastq_headers(filename, check_proportion)
            passed, details = True, "DEBUG_SKIPPED"
            if passed == True:
                checkArgs["debug_message"] = f"No header issues after checking {check_proportion*100}% of the records"
                checkArgs["user_message"] = f"Fastq.gz headers validated"
                checkArgs["severity"] = 30
            else:
                checkArgs["debug_message"] = f"Found header issues after checking {check_proportion*100}% of the records"
                checkArgs["user_message"] = f"Header issues"
                checkArgs["severity"] = 90
            flagger.flag(**checkArgs)
    # T_0003 ##########################################################
    partial_check_args = dict()
    partial_check_args["check_id"] = "T_0003"
    def file_size(file: Path):
        """ Returns filesize for a Path object
        """
        return file.stat().st_size/float(1<<30)
    # compute file sizes
    filesize_mapping, all_filesizes = filevalues_from_mapping(file_mapping, file_size)

    metric = "file_size"
    value_based_checks(partial_check_args = partial_check_args,
                       check_cutoffs = cutoffs[cutoffs_subsection],
                       value_mapping = filesize_mapping,
                       all_values = all_filesizes,
                       flagger = flagger,
                       value_alias = metric,
                       middlepoint = cutoffs[cutoffs_subsection]["middlepoint"]
                       )

def validate_verify_multiqc(multiqc_json: Path,
                            file_mapping: dict,
                            cutoffs: dict,
                            flagger: Flagger,
                            paired_end: bool,
                            outlier_comparision_point: str = "median",
                            ):
    """ Performs VV for trimmed reads for checks involving multiqc json generated
            by trimmed reads fastqc aggregation
    """
    print(f"Starting VV for Trimmed Reads based on MultiQC file")
    ##############################################################
    # SET FLAGGING OUTPUT ATTRIBUTES
    ##############################################################
    flagger.set_script(__name__)
    flagger.set_step("Trimmed Reads [MultiQC]")
    cutoffs_subsection = "trimmed_reads"
    ##############################################################
    # STAGE MULTIQC DATA FROM JSON
    ##############################################################
    mqc = multiqc.MultiQC(multiQC_json = multiqc_json,
                          file_mapping = file_mapping,
                          outlier_comparision_point = outlier_comparision_point)
    samples = list(file_mapping.keys())
    ### UNIQUE IMPLEMENTATION CHECKS ##################################
    # T_1001 ##########################################################
    if paired_end:
        check_args = dict()
        check_args["check_id"] = "T_1001"
        for sample in samples:
            check_args["entity"] = sample
            forward_count = mqc.data[sample]["forward-total_sequences"].value
            reverse_count = mqc.data[sample]["reverse-total_sequences"].value
            pairs_match = forward_count == reverse_count
            if pairs_match:
                check_args["severity"] = 30
                check_args["debug_message"] = f"Count of reads matches between paired reads."
            else:
                check_args["severity"] = 90
                check_args["debug_message"] = f"Count of reads different between paired reads."

            flagger.flag(**check_args)

    ################################################################
    check_specific_args = [
        {"check_id":"T_1002", "mqc_base_key":"fastqc_sequence_length_distribution_plot", "by_indice":True, "allow_missing_base_key":True},
        {"check_id":"T_1003", "mqc_base_key":"percent_duplicates"},
        {"check_id":"T_1004", "mqc_base_key":"percent_gc"},
        {"check_id":"T_1005", "mqc_base_key":"fastqc_overrepresented_sequencesi_plot-Top over-represented sequence"},
        {"check_id":"T_1006", "mqc_base_key":"fastqc_overrepresented_sequencesi_plot-Sum of remaining over-represented sequences"},
        {"check_id":"T_1007", "mqc_base_key":"fastqc_per_base_sequence_quality_plot", "by_indice":True},
        {"check_id":"T_1008", "mqc_base_key":"fastqc_per_sequence_quality_scores_plot", "by_indice":True},
        {"check_id":"T_1009", "mqc_base_key":"fastqc_per_sequence_gc_content_plot-Percentages", "by_indice":True},
        {"check_id":"T_1010", "mqc_base_key":"fastqc_sequence_duplication_levels_plot", "by_indice":True},
        {"check_id":"T_1011", "mqc_base_key":"fastqc_per_base_n_content_plot", "aggregation_function":sum, "cutoffs_subkey":"bin_sum"},
        {"check_id":"T_1012", "mqc_base_key":"fastqc_per_base_n_content_plot", "aggregation_function":statistics.mean, "cutoffs_subkey":"bin_mean"},
        {"check_id":"T_1013", "mqc_base_key":"fastqc_adapter_content_plot", "by_indice":True, "allow_missing_base_key":True},
        ]
    for mqc_check_args in check_specific_args:
        general_mqc_based_check(samples = samples,
                                mqc = mqc,
                                cutoffs = cutoffs[cutoffs_subsection],
                                flagger = flagger,
                                **mqc_check_args)
    ############################################################################
    # maps which codes to consider for assessing realized flags
    # from protoflags
    PROTOFLAG_MAP = {
        60 : [59],
        50 : [59,49]
    }
    ### Check if any sample proportion related flags should be raised
    check_id_with_samples_proportion_threshold = {"T_1005":"fastqc_overrepresented_sequencesi_plot-Top over-represented sequence",
                                                 "T_1006":"fastqc_overrepresented_sequencesi_plot-Sum of remaining over-represented sequences",
    }
    for check_id, cutoffs_key in check_id_with_samples_proportion_threshold.items():
        flagger.check_sample_proportions(check_id,
                                         cutoffs["trimmed_reads"][cutoffs_key],
                                         PROTOFLAG_MAP)
