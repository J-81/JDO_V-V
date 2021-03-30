#! /usr/bin/env python
""" Validation/Verification for raw reads in RNASeq Concensus Pipeline
"""
from __future__ import annotations
from collections import namedtuple, defaultdict
from pathlib import Path
import gzip
import statistics
import subprocess

from VV.utils import outlier_check, label_file, filevalues_from_mapping, value_based_checks, value_check_direct
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

    ###################################################################
    # PERFROM CHECKS
    ###################################################################

    ### START R_0001 ##################################################
    check_id = "T_0001"
    missing_file = list()
    for sample in file_mapping.keys():
        expected_file_lables = list(file_mapping[sample].keys())
        missing_files = list()
        for file_label in expected_file_lables:
            if not file_label in file_mapping[sample].keys():
                missing_file.append(file_label)
        if len(missing_files) != 0:
            flagger.flag(entity = sample,
                         debug_message = f"Missing expected files for {missing_files}",
                         severity = 90,
                         check_id = check_id)
        else:
            flagger.flag(entity = sample,
                         debug_message = f"All expected files present: {expected_file_lables}",
                         severity = 30,
                         check_id = check_id)
    ### DONE R_0001 ###################################################

    ### START R_0002 ##################################################
    # TODO: add header check (R_0002)
    check_proportion = cutoffs["trimmed_reads"]["fastq_proportion_to_check"]
    for sample in file_mapping.keys():
        checkArgs = dict()
        checkArgs["check_id"] = "T_0002"
        checkArgs["entity"] = sample
        for filelabel, filename in file_mapping[sample].items():
            checkArgs["sub_entity"] = filelabel
            passed, details = _check_headers(filename, check_proportion)
            if passed == True:
                checkArgs["debug_message"] = f"No header issues after checking {check_proportion*100}% of the records"
                checkArgs["user_message"] = f"Fastq.gz headers validated"
                checkArgs["severity"] = 30
            else:
                checkArgs["debug_message"] = f"Found header issues after checking {check_proportion*100}% of the records"
                checkArgs["user_message"] = f"Header issues"
                checkArgs["severity"] = 90
            flagger.flag(**checkArgs)
    ### DONE R_0002 ###################################################

    ### START R_0003 ##################################################
    check_id = "T_0003"
    def file_size(file: Path):
        """ Returns filesize for a Path object
        """
        return file.stat().st_size/float(1<<30)
    # compute file sizes
    filesize_mapping, all_filesizes = filevalues_from_mapping(file_mapping, file_size)

    metric = "file_size"
    value_based_checks(check_cutoffs = cutoffs["trimmed_reads"][metric],
                       value_mapping = filesize_mapping,
                       all_values = all_filesizes,
                       flagger = flagger,
                       check_id = check_id,
                       value_alias = metric,
                       middlepoint = cutoffs["middlepoint"]
                       )
    ### DONE R_0003 ###################################################

def _check_headers(filename, check_proportion: float = 0.2):
    """ Checks fastq lines for expected header content

    Note: Example of header from GLDS-194

    |  ``@J00113:376:HMJMYBBXX:3:1101:26666:1244 1:N:0:NCGCTCGA\n``

    This also assumes the fastq file does NOT split sequence or quality lines
    for any read

    :param file: compressed fastq file to check
    :param count_lines_to_check: number of lines to check. Special value: -1 means no limit, check all lines.
    """
    ###### Generate temporary gzipped file
    assert 1 >= check_proportion > 0, "Check proportion must be  value between 0 and 1"
    subsampled = subprocess.Popen(['seqtk', 'sample', '-s',
                                   '777', filename, str(check_proportion)],
                                   stdout=subprocess.PIPE)
    #sampled_lines, _ = subsampled.communicate()
    # decode binary and split
    #sampled_lines = sampled_lines.decode().split("\n")
    for i, line in enumerate(iter(subsampled.stdout.readline, None)):
        # end of iteration returns None
        if not line:
            #print("Finished checking sample of header lines")
            break
        # this indicates the end of sampled lines
        line = line.decode().rstrip()

        #print(i, line) #DEBUG PRINT
        # every fourth line should be an identifier
        expected_identifier_line = (i % 4 == 0)
        # check if line is actually an identifier line
        if (expected_identifier_line and line[0] != "@"):
            return False, "Expected header line missing"
    return True, "NO ISSUES"

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
    ##############################################################
    # STAGE MULTIQC DATA FROM JSON
    ##############################################################
    mqc = multiqc.MultiQC(multiQC_json = multiqc_json,
                          file_mapping = file_mapping,
                          outlier_comparision_point = outlier_comparision_point)
    samples = list(file_mapping.keys())
    ### START T_1001 ##################################################
    check_id = "T_1001"
    for sample in samples:
        entity = sample
        # I.E: if the study is paired end
        if set(("forward", "reverse")) == set(mqc.file_labels):
            forward_count = mqc.data[sample]["forward-total_sequences"].value
            reverse_count = mqc.data[sample]["reverse-total_sequences"].value
            pairs_match = forward_count == reverse_count
            if pairs_match:
                flagger.flag(entity = entity,
                             debug_message = f"Total Count of reads matches between pairs.",
                             severity = 30,
                             check_id = check_id)
            else:
                flagger.flag(entity = entity,
                             debug_message = f"Total Count of reads does NOT matches between pairs.",
                             severity = 90,
                             check_id = check_id)
    ### DONE T_1001 ###################################################

    ### START T_1002 ##################################################
    # NOTE: outliers is calculated for each sample.  This is redudant and efficiency may be improved by refactoring this in the future.
    check_id = "T_1002"
    key = "fastqc_sequence_length_distribution_plot"
    check_cutoffs = cutoffs["trimmed_reads"]["sequence_length_dist"]
    try:
        mqc.data[samples[0]][f"{mqc.file_labels[0]}-{key}"]
        for sample in samples:
            for file_label in mqc.file_labels:
                flagged = False
                entity = f"{sample}:{file_label}"
                cur_data_key = f"{file_label}-{key}"
                thresholds = sorted(check_cutoffs["outlier_thresholds"], reverse=True)
                for threshold in thresholds:
                    severity = check_cutoffs["outlier_thresholds"][threshold]
                    outliers = mqc.detect_outliers(key = cur_data_key,
                                                   deviation = threshold
                                                 )
                    outliers_for_sample = [index for _sample,index,_ in outliers if _sample == sample]
                    if len(outliers_for_sample) != 0:
                        flagger.flag(entity = entity,
                                     debug_message = (f"Outliers detected by sequence "
                                               f"length bin. This indicates sequence length "
                                               f"distribution may vary by sample. "
                                               f"See the following x-indices "
                                               f"{outliers_for_sample}"),
                                     severity = severity,
                                     check_id = check_id)
                        flagged = True
                        break
                if not flagged:
                    flagger.flag(entity = entity,
                                 debug_message = (f"Sequence length varies "
                                            f"across samples; however, "
                                            f"no outliers detected by "
                                            f"sequence length bin [deviation > {threshold}]."),
                                 severity = 30,
                                 check_id = check_id)

    except KeyError:
        # this indicates the plot was not generated.
        # this happens when all average sequences are the same.
        # therefore this is a pass condition for the check
        for sample in samples:
            entity = sample
            flagger.flag(entity = entity,
                         debug_message = ("Average sequence lengths across all samples matches. "\
                                   "Reason: MultiQC did not graph average sequence "\
                                   "lengths.  This happens when the graph is replace "\
                                   "with a debug_message indicating 'All samples have "\
                                   "sequences of a single length'"),
                         severity = 30,
                         check_id = check_id)

    ### DONE T_1002 ###################################################

    ################################################################
    # Checks for each sample:file_label vs all samples
    # for single value cases
    check_ids_to_keys = {"T_1003":"percent_duplicates",
                        "T_1004":"percent_gc",
                        "T_1005":"fastqc_overrepresented_sequencesi_plot-Top over-represented sequence",
                        "T_1006":"fastqc_overrepresented_sequencesi_plot-Sum of remaining over-represented sequences"
                        }
    for check_id, key in check_ids_to_keys.items():
        # compile all values for all file labels
        # e.g. for paired end, both forward and reverse reads
        all_values = list()
        for file_label in mqc.file_labels:
            full_key = f"{file_label}-{key}"
            all_values.extend(mqc.compile_subset(samples_subset = samples,
                                                 key = full_key))
        # iterate through each sample:file_label
        # test against all values from all file-labels
        for sample in samples:
            for file_label in mqc.file_labels:
                entity = f"{sample}:{file_label}"
                all_values = mqc.compile_subset(samples_subset = samples,
                                                key = full_key)
                value = mqc.data[sample][full_key].value
                value_check_direct(value = value,
                                   all_values = all_values,
                                   check_cutoffs = cutoffs["trimmed_reads"][key],
                                   flagger = flagger,
                                   check_id = check_id,
                                   entity = entity,
                                   value_alias = key,
                                   middlepoint = cutoffs["middlepoint"],
                                   debug_message_prefix = "Sample:File_Label vs Samples")

    #######################################################
    # Checks against index values
    # Outliers are detected within each index bin and outlier bins are reported
    check_ids_to_keys = {"T_1007":"fastqc_per_base_sequence_quality_plot",
                        "T_1008":"fastqc_per_sequence_quality_scores_plot",
                        "T_1009":"fastqc_per_sequence_gc_content_plot-Percentages",
                        "T_1010":"fastqc_sequence_duplication_levels_plot",
                        }
    for check_id, key in check_ids_to_keys.items():
        check_cutoffs = cutoffs["trimmed_reads"][key]
        for sample in samples:
            for file_label in mqc.file_labels:
                flagged = False
                entity = f"{sample}:{file_label}"
                cur_data_key = f"{file_label}-{key}"
                bin_units = mqc.data[sample][cur_data_key].bin_units
                # iterate through thresholds in descending order (more severe first)
                thresholds = sorted(check_cutoffs["outlier_thresholds"], reverse=True)
                for threshold in thresholds:
                    outliers = mqc.detect_outliers(key = cur_data_key,
                                                   deviation = threshold
                                                 )
                    outliers_for_sample = [index for _sample,index,_ in outliers if _sample == sample]
                    if len(outliers_for_sample) != 0:
                        flagger.flag(entity = entity,
                                     debug_message = (f"<Sample:Filelabel:bin vs AllSamples:Filelabel:bin> Outliers detected by {bin_units} "
                                              f" bin. This indicates {bin_units} "
                                              f"distribution may vary by sample. "
                                              f"See the following x-indices in {key} "
                                              f"{outliers_for_sample}"),
                                     severity = check_cutoffs["outlier_thresholds"][threshold],
                                     check_id = check_id)
                        flagged = True
                # log passes
                if not flagged:
                    flagger.flag(entity = entity,
                                 debug_message = (f"No outliers detected for {key} [deviation > {threshold}]."),
                                 severity = 30,
                                 check_id = check_id)

    ################################################################
    # Checks against indexed values with aggregation of such values
    check_ids_to_keys = {"T_1011":("fastqc_per_base_n_content_plot", sum, "bin_sum"),
                        "T_1012":("fastqc_per_base_n_content_plot", statistics.mean, "bin_mean"),
                        }
    for check_id, (key, aggregator, cutoffs_key) in check_ids_to_keys.items():
        check_cutoffs = cutoffs["trimmed_reads"][key][cutoffs_key]
        for sample in samples:
            for file_label in mqc.file_labels:
                entity = f"{sample}:{file_label}"
                cur_data_key = f"{file_label}-{key}"
                bin_units = mqc.data[sample][cur_data_key].bin_units
                all_values = mqc.compile_subset(samples_subset = samples,
                                            key = cur_data_key,
                                            aggregator = aggregator)
                value = mqc.compile_subset(samples_subset = [sample], # note: this is just the sample to check for outliers!
                                            key = cur_data_key,
                                            aggregator = aggregator)
                assert len(value) == 1, "Aggregation should return more than one value!"
                value = float(value[0]) # an error here may indicate an issue generating a single value from the compile subset arg
                value_check_direct(value = value,
                                   all_values = all_values,
                                   check_cutoffs = check_cutoffs,
                                   flagger = flagger,
                                   check_id = check_id,
                                   entity = entity,
                                   value_alias = f"{key}-aggregated by {cutoffs_key}",
                                   middlepoint = cutoffs["middlepoint"],
                                   debug_message_prefix = "Sample:File_Label vs Samples")


    ### START T_1002 ##################################################
    # NOTE: outliers is calculated for each sample.  This is redudant and efficiency may be improved by refactoring this in the future.
    check_id = "T_1013"
    key = "fastqc_adapter_content_plot"
    check_cutoffs = cutoffs["trimmed_reads"]["fastqc_adapter_content_plot"]
    try:
        mqc.data[samples[0]][f"{mqc.file_labels[0]}-{key}"]
        flagger.flag(entity = "FULL_DATASET",
                     debug_message = ("Adaptor content across all samples is neglible (< 0.1%). "
                               "Reason: MultiQC did not Adaptor content. "
                               "This happens when the graph is replace "
                               "with a debug_message indicating 'No samples found "
                               "with any adapter contamination > 0.1%'"),
                     severity = 60,
                     check_id = check_id)

    except KeyError:
        # this indicates the plot was not generated.
        # this happens when neglible adaptor content is found.
        # therefore this is a pass condition for the check
        flagger.flag(entity = "FULL_DATASET",
                     debug_message = ("Adaptor content across all samples is neglible (< 0.1%). "
                               "Reason: MultiQC did not Adaptor content. "
                               "This happens when the graph is replace "
                               "with a debug_message indicating 'No samples found "
                               "with any adapter contamination > 0.1%'"),
                     severity = 30,
                     check_id = check_id)


    ### DONE R_1003 ###################################################
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
