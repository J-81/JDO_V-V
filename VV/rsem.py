""" VV related to the output from RSEM results
"""
import os
import statistics
from pathlib import Path

import pandas as pd


from VV.utils import value_check_direct
from VV.flagging import Flagger

class RsemCounts():
    """ Representation of Rsem results for a set of samples.
    Validates:
        - <sample>.genes.results
        - <sample>.isoforms.results
    """
    def __init__(self,
                 dir_mapping: dict,
                 flagger: Flagger,
                 cutoffs: dict,
                 has_ERCC: bool
                 ):
        print(f"Starting VV for RSEM counting output")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("RSEM")
        self.flagger = flagger
        self.cutoffs = cutoffs
        self.cutoffs_subsection = "RSEM"
        self.has_ERCC = has_ERCC

        # start data extraction and VV
        self.samples = list(dir_mapping.keys())
        # generate expected files in the main sample directory
        self.file_mapping = dict()
        for sample, directory in dir_mapping.items():
            self.file_mapping[sample] = dict()
            self.file_mapping[sample][".genes.results"] = Path(directory) / f"{sample}.genes.results"
            self.file_mapping[sample][".isoforms.results"] = Path(directory) / f"{sample}.isoforms.results"

        self.gene_counts = dict()
        self.isoform_counts = dict()

        # cross_check
        # a dictionary of results to pass to other processes for crossing checking steps
        self.cross_check = dict()

        for sample in self.samples:
            gene_count_path = self.file_mapping[sample][".genes.results"]
            isoform_count_path = self.file_mapping[sample][".isoforms.results"]

            # check if file exists
            partial_check_args = dict()
            partial_check_args["check_id"] = "M_0001"
            partial_check_args["entity"] = sample
            self.flagger.flag_file_exists(check_file = gene_count_path,
                                          partial_check_args = partial_check_args)

            # check if file exists
            partial_check_args = dict()
            partial_check_args["check_id"] = "M_0002"
            partial_check_args["entity"] = sample
            self.flagger.flag_file_exists(check_file = isoform_count_path,
                                          partial_check_args = partial_check_args)


            self.gene_counts[sample] = pd.read_csv(gene_count_path ,sep="\t")
            self.isoform_counts[sample] = pd.read_csv(isoform_count_path ,sep="\t")

        # vv related to genes
        counts_of_NonERCC_genes_expressed = dict()
        counts_of_genes_expressed = dict()
        counts_of_ERCC_genes_detected = dict()
        # extract counts of genes
        # i.e. how many unique genes found (those with counts greater than zero)
        for sample, df in self.gene_counts.items():
            isExpressed = df["expected_count"] > 0
            notERCC = ~df["gene_id"].str.startswith("ERCC-")
            full_mask = isExpressed & notERCC
            counts_of_NonERCC_genes_expressed[sample] = len(df.loc[full_mask])
            counts_of_genes_expressed[sample] = len(df.loc[isExpressed])
            counts_of_ERCC_genes_detected[sample] = len(df.loc[~notERCC & isExpressed])

        # extract summed counts
        # i.e. for each sample, what was the sum of the gene counts
        summed_gene_counts = dict()
        for sample, df in self.gene_counts.items():
            summed_gene_counts[sample] = sum(df["expected_count"])

        self.cross_check["bySample_summed_gene_counts"] = summed_gene_counts

        # vv related to isoforms
        counts_of_NonERCC_isoforms_expressed = dict()
        counts_of_isoforms_expressed = dict()
        for sample, df in self.isoform_counts.items():
            isExpressed = df["expected_count"] > 0
            notERCC = ~df["gene_id"].str.startswith("ERCC-")
            full_mask = isExpressed & notERCC
            counts_of_NonERCC_isoforms_expressed[sample] = len(df.loc[full_mask])
            counts_of_isoforms_expressed[sample] = len(df.loc[isExpressed])

        # flag if under average count
        partial_check_args = {"check_id":"M_0003"}
        file_path = self.file_mapping[sample][".genes.results"]
        partial_check_args["full_path"] = Path(file_path).resolve()
        partial_check_args["filename"] = Path(file_path).name
        mean_count = statistics.mean(counts_of_NonERCC_genes_expressed.values())
        for sample, count in counts_of_NonERCC_genes_expressed.items():
            partial_check_args["entity"] = sample
            if count < mean_count:
                partial_check_args["debug_message"] = "Gene counts are less than the average."
                partial_check_args["severity"] = 50
            else:
                partial_check_args["debug_message"] = "Gene counts are not less than the average"
                partial_check_args["severity"] = 30
            self.flagger.flag(**partial_check_args)

        # flag if under average count
        partial_check_args = {"check_id":"M_0004"}
        file_path = self.file_mapping[sample][".isoforms.results"]
        partial_check_args["full_path"] = Path(file_path).resolve()
        partial_check_args["filename"] = Path(file_path).name
        mean_count = statistics.mean(counts_of_NonERCC_isoforms_expressed.values())
        for sample, count in counts_of_NonERCC_isoforms_expressed.items():
            partial_check_args["entity"] = sample
            if count < mean_count:
                partial_check_args["debug_message"] = "Isoform counts are less than the average."
                partial_check_args["severity"] = 50
            else:
                partial_check_args["debug_message"] = "Isoform counts are not less than the average"
                partial_check_args["severity"] = 30
            self.flagger.flag(**partial_check_args)


        ################################################################
        # Checks for each sample:file_label vs all samples
        check_specific_args = [
            ({"check_id": "M_0005"}, "number_of_unique_genes_expressed", counts_of_genes_expressed, ".genes.results"),
            ({"check_id": "M_0006"}, "count_of_unique_isoforms_expressed", counts_of_isoforms_expressed, ".isoforms.results"),
                        ]
        if self.has_ERCC:
            check_specific_args.append(({"check_id": "M_0007"}, "number_of_ERCC_genes_detected", counts_of_ERCC_genes_detected, ".genes.results"))
        for partial_arg_set, key, df_dict, filename_key in check_specific_args:
            all_values = df_dict.values()
            for sample in self.samples:
                value = df_dict[sample]
                file_path = self.file_mapping[sample][filename_key]
                partial_arg_set["full_path"] = Path(file_path).resolve()
                partial_arg_set["filename"] = Path(file_path).name
                partial_arg_set["entity"] = sample
                partial_arg_set["entity_value"] = df_dict[sample]
                partial_arg_set["entity_value_units"] = key
                partial_arg_set["outlier_comparison_type"] = "Across-Samples"
                value_check_direct(partial_check_args = partial_arg_set,
                                   check_cutoffs = cutoffs[self.cutoffs_subsection][key],
                                   value = value,
                                   all_values = all_values,
                                   flagger = flagger,
                                   value_alias = key,
                                   middlepoint = cutoffs[self.cutoffs_subsection]["middlepoint"],
                                   )
