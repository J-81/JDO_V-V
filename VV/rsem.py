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
                 samples: str,
                 dir_path: str,
                 flagger: Flagger,
                 params: dict
                 ):
        print(f"Starting VV for RSEM counting output")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("RSEM")
        self.flagger = flagger
        self.params = params

        # start data extraction and VV
        self.samples = samples
        self.dir_path = Path(dir_path)

        self.gene_counts = dict()
        self.isoform_counts = dict()
        for sample in samples:
            gene_count_path = self.dir_path / sample / f"{sample}.genes.results"
            isoform_count_path = self.dir_path / sample / f"{sample}.isoforms.results"

            # check if file exists
            checkID = "M_0001"
            if gene_count_path.is_file():
                message = f"Gene counts file found. {gene_count_path}"
                self.flagger.flag(entity = sample, message = message,
                                  severity = 30, checkID = checkID
                                )
            else:
                message = f"Gene counts file NOT found. {gene_count_path}"
                self.flagger.flag(entity = sample, message = message,
                                  severity = 90, checkID = checkID
                                )
            # check if file exists
            checkID = "M_0002"
            if isoform_count_path.is_file():
                message = f"Isoform counts file found. {isoform_count_path}"
                self.flagger.flag(entity = sample, message = message,
                                  severity = 30, checkID = checkID
                                )
            else:
                message = f"Isoform counts file NOT found. {isoform_count_path}"
                self.flagger.flag(entity = sample, message = message,
                                  severity = 90, checkID = checkID
                                )
            self.gene_counts[sample] = pd.read_csv(gene_count_path ,sep="\t")
            self.isoform_counts[sample] = pd.read_csv(isoform_count_path ,sep="\t")

        # vv related to genes
        counts_of_NonERCC_genes_expressed = dict()
        counts_of_genes_expressed = dict()
        counts_of_ERCC_genes_detected = dict()
        for sample, df in self.gene_counts.items():
            isExpressed = df["expected_count"] > 0
            notERCC = ~df["gene_id"].str.startswith("ERCC-")
            full_mask = isExpressed & notERCC
            counts_of_NonERCC_genes_expressed[sample] = len(df.loc[full_mask])
            counts_of_genes_expressed[sample] = len(df.loc[isExpressed])
            counts_of_ERCC_genes_detected[sample] = len(df.loc[~notERCC & isExpressed])

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
        checkID = "M_0003"
        mean_count = statistics.mean(counts_of_NonERCC_genes_expressed.values())
        for sample, count in counts_of_NonERCC_genes_expressed.items():
            if count < mean_count:
                message = "Gene counts are less than the average."
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 50,
                                  checkID = checkID
                                )
            else:
                message = "Gene counts are not less than the average."
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 30,
                                  checkID = checkID
                                )
        # flag if under average count
        checkID = "M_0004"
        mean_count = statistics.mean(counts_of_NonERCC_isoforms_expressed.values())
        for sample, count in counts_of_NonERCC_isoforms_expressed.items():
            if count < mean_count:
                message = "Isoform counts are less than the average."
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 50,
                                  checkID = checkID
                                )
            else:
                message = "Isoform counts are not less than the average."
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 30,
                                  checkID = checkID
                                )

        ################################################################
        # Checks for each sample:file_label vs all samples
        checkIDs_to_keys = {"M_0005":("count_of_unique_genes_expressed", counts_of_genes_expressed),
                            "M_0006":("count_of_unique_isoforms_expressed", counts_of_isoforms_expressed),
                            }
        if self.params["hasERCC"]:
            checkIDs_to_keys["M_0007"] = ("count_of_ERCC_genes_detected", counts_of_ERCC_genes_detected)
        for checkID, (key, df_dict) in checkIDs_to_keys.items():
            # compile all values for all file labels
            # e.g. for paired end, both forward and reverse reads
            all_values = df_dict.values()

            # iterate through each sample:file_label
            # test against all values from all file-labels
            for sample in samples:
                    entity = f"{sample}"
                    value = df_dict[sample]
                    value_check_direct(value = value,
                                       all_values = all_values,
                                       check_params = params["RSEM"][key],
                                       flagger = flagger,
                                       checkID = checkID,
                                       entity = entity,
                                       value_alias = key,
                                       middlepoint = params["middlepoint"],
                                       message_prefix = "Sample vs Samples")
