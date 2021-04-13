""" VV for deseq2 output
"""
import os
from pathlib import Path

from VV.flagging import Flagger

import pandas as pd

class Deseq2ScriptOutput():
    """ Representation of the output from Deseq2
    """
    def __init__(self,
                 samples: str,
                 counts_dir_path: Path,
                 dge_dir_path: Path,
                 flagger: Flagger,
                 cutoffs: dict,
                 has_ERCC: bool,
                 cross_checks: dict):
        print(f"Starting VV for DESEQ2 script output")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("DESEQ2_OUTPUT")
        self.flagger = flagger
        self.cutoffs = cutoffs

        #print(f"Checking Deseq2 Normalized Counts Results")
        self.samples = samples
        self.counts_dir_path = counts_dir_path
        self.dge_dir_path = dge_dir_path
        self.has_ERCC = has_ERCC
        self.rsem_cross_checks = cross_checks["RSEM"]
        self.samplesheet_cross_checks = cross_checks["SampleSheet"]
        self._check_counts_csv_files()
        self._check_dge_files()

    def _check_counts_csv_files(self):
        """ Checks that expected files exist and meet folowing conditions:
        - SampleTable.csv
            - contains supplied samples (likley coming from parsing ISA) in first column
        - Unnormalized_Counts.csv
            - contains supplied samples as columns headers
        - Normalized_Counts.csv
            - contains supplied samples as columns headers
        - ERCC_Normalized_Counts.csv (ONLY IF has_ERCC is set to True)
            - contains supplied samples as columns headers
        - additionally checks that the first and last lines of each counts csv are different
            - This implies normalization with performed correctly
        """
        # SampleTable.csv Check
        check_id_to_file = {
            "D_0001" : self.counts_dir_path / "SampleTable.csv",
            "D_0002" : self.counts_dir_path / "Unnormalized_Counts.csv",
            "D_0003" : self.counts_dir_path / "Normalized_Counts.csv",
            }
        if self.has_ERCC:
            check_id_to_file["D_0004"] = self.counts_dir_path / "ERCC_Normalized_Counts.csv"

        check_args = dict()
        check_args["entity"] = "All_Samples"
        for check_id, expectedFile in check_id_to_file.items():
            check_args["check_id"] = check_id
            check_args["full_path"] = Path(expectedFile).resolve()
            check_args["filename"] = Path(expectedFile).name
            # check file existence
            self.flagger.flag_file_exists(check_file = expectedFile,
                                          partial_check_args = check_args)
            if expectedFile.is_file():
                self._check_samples_match(expectedFile, check_args)
                if expectedFile.name in ["Unnormalized_Counts.csv"]:
                    self._check_counts_match_gene_results(expectedFile, check_args)

    def _check_dge_files(self):
        """ Checks that expected files exist and meet folowing conditions:
        - SampleTable.csv
            - contains supplied samples (likley coming from parsing ISA) in first column
        - Unnormalized_Counts.csv
            - contains supplied samples as columns headers
        - Normalized_Counts.csv
            - contains supplied samples as columns headers
        - ERCC_Normalized_Counts.csv (ONLY IF has_ERCC is set to True)
            - contains supplied samples as columns headers
        - additionally checks that the first and last lines of each counts csv are different
            - This implies normalization with performed correctly
        """
        # ERCC_NormDGE  visualization_PCA_table.csv
        # SampleTable.csv Check
        entity = "FULL_DATASET"
        check_id_to_file = {
            "D_0005" : self.dge_dir_path / "contrasts.csv",
            "D_0006" : self.dge_dir_path / "differential_expression.csv",
            "D_0007" : self.dge_dir_path / "visualization_output_table.csv",
            "D_0008" : self.dge_dir_path / "visualization_PCA_table.csv",
            }
        if self.has_ERCC:
            check_id_to_file["D_0009"] = self.dge_dir_path / Path("ERCC_NormDGE") / "ERCCnorm_contrasts.csv"
            check_id_to_file["D_0010"] = self.dge_dir_path / Path("ERCC_NormDGE") / "ERCCnorm_differential_expression.csv"
            check_id_to_file["D_0011"] = self.dge_dir_path / Path("ERCC_NormDGE") / "visualization_output_table_ERCCnorm.csv"
            check_id_to_file["D_0012"] = self.dge_dir_path / Path("ERCC_NormDGE") / "visualization_PCA_table_ERCCnorm.csv"

        check_args = dict()
        check_args["entity"] = "All_Samples"
        for check_id, expectedFile in check_id_to_file.items():
            check_args["check_id"] = check_id
            check_args["full_path"] = Path(expectedFile).resolve()
            check_args["filename"] = Path(expectedFile).name
            # check file existence
            self.flagger.flag_file_exists(check_file = expectedFile,
                                          partial_check_args = check_args)


            # file specific checks
            if expectedFile.name in ["contrasts.csv","ERCCnorm_contrasts.csv"]:
                self._check_contrasts(expectedFile, partial_check_args = check_args)

            elif expectedFile.name in ["differential_expression.csv","ERCCnorm_differential_expression.csv"]:
                self._check_dge_table(expectedFile, partial_check_args = check_args)

            elif expectedFile.name in ["visualization_output_table.csv","visualization_output_table_ERCCnorm.csv"]:
                self._check_visualization_table(expectedFile, partial_check_args = check_args)


    def _check_dge_table(self, expectedFile, partial_check_args: dict):
        dge_df = pd.read_csv(expectedFile, index_col=None)
        flagged = False
        # check all samples have a column
        missing_sample_cols = set(self.samples) - set(dge_df.columns)
        if missing_sample_cols:
            flagged = True
            debug_message = f"Missing sample columns {missing_sample_cols}."
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

        # check expected columns based on groups and groups_versus
        expected_cols = [f"Group.Mean_{factor_group}" for factor_group in self.factor_groups] + \
                        [f"Group.Stdev_{factor_group}" for factor_group in self.factor_groups] + \
                        [f"Log2fc_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"P.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"Adj.p.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        ["All.mean","All.stdev"] + \
                        ["ENSEMBL","SYMBOL","GENENAME","REFSEQ","ENTREZID","STRING_id","GOSLIM_IDS"]
        expected_cols = set(expected_cols)
        missing_cols = expected_cols - set(dge_df.columns)
        if missing_cols:
            flagged = True
            debug_message = f"Missing expected data columns ({missing_cols})"
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

        non_negative_cols = [f"P.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                            [f"Adj.p.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus]
        has_negative_values = list()
        for non_negative_col in non_negative_cols:
            has_negative = (dge_df[non_negative_cols] < 0).values.any()
            if has_negative:
                has_negative_values.append(non_negative_cols)
        if has_negative_values:
            flagged = True
            debug_message = f"Found negative values in {has_negative_values}"
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

        if not flagged:
            debug_message = f"File exists, expected columns found, p.values and adj.p.values were non-negative"
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 30
            self.flagger.flag(**partial_check_args)

    def _check_visualization_table(self, expectedFile, partial_check_args: dict):
        visualization_df = pd.read_csv(expectedFile, index_col=None)
        flagged = False
        # check all samples have a column
        missing_sample_cols = set(self.samples) - set(visualization_df.columns)
        if missing_sample_cols:
            flagged = True
            debug_message = f"File exists but appears to be missing sample columns {missing_sample_cols}."
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

        # check expected columns based on groups and groups_versus
        expected_cols = [f"Group.Mean_{factor_group}" for factor_group in self.factor_groups] + \
                        [f"Group.Stdev_{factor_group}" for factor_group in self.factor_groups] + \
                        [f"Log2fc_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"P.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"Adj.p.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"Updown_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"Sig.05_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"Sig.1_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        [f"Log2_P.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                        ["All.mean","All.stdev"] + \
                        ["ENSEMBL","SYMBOL","GENENAME","REFSEQ","ENTREZID","STRING_id","GOSLIM_IDS"]
        expected_cols = set(expected_cols)
        missing_cols = expected_cols - set(visualization_df.columns)
        if missing_cols:
            flagged = True
            debug_message = f"Missing columns ({missing_cols})"
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

        non_negative_cols = [f"P.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus] + \
                            [f"Adj.p.value_{factor_groups_versus}" for factor_groups_versus in self.factor_groups_versus]

        has_negative_values = list()
        for non_negative_col in non_negative_cols:
            has_negative = (visualization_df[non_negative_cols] < 0).values.any()
            if has_negative:
                has_negative_values.append(non_negative_cols)
        if has_negative_values:
            flagged = True
            debug_message = f"Found negative values in {has_negative_values}"
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

        if not flagged:
            debug_message = f"File exists, expected columns found, columns datatypes/values were within constraints"
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 30
            self.flagger.flag(**partial_check_args)

    def _check_counts_match_gene_results(self, unnorm_counts_file, partial_check_args: dict):
        """ Checks that the gene counts match on a per sample basis """
        # get by sample counts (from RSEM)
        bySample_summed_gene_counts = self.rsem_cross_checks["bySample_summed_gene_counts"]

        unnorm_df = pd.read_csv(unnorm_counts_file, index_col=0)

        for col in unnorm_df.columns:
            sample = col
            partial_check_args["entity"] = sample
            unnorm_sum_of_counts = sum(unnorm_df[sample])
            rsem_sum_of_counts = bySample_summed_gene_counts[sample]

            if unnorm_sum_of_counts == rsem_sum_of_counts:
                debug_message=f"{unnorm_counts_file.name} summed gene counts ({unnorm_sum_of_counts}) matches counts from RSEM ({rsem_sum_of_counts})"
                partial_check_args["debug_message"] = debug_message
                partial_check_args["severity"] = 30
            else:
                debug_message=debug_message=f"{unnorm_counts_file.name} summed gene counts ({unnorm_sum_of_counts})  DOES NOT match counts from RSEM ({rsem_sum_of_counts})"
                partial_check_args["debug_message"] = debug_message
                partial_check_args["severity"] = 90
            self.flagger.flag(**partial_check_args)

    def _check_samples_match(self, expectedFile, partial_check_args: dict):
        """ Checks that sample names match
        """
        # check if samples match expectation
        df = pd.read_csv(expectedFile, header=0)
        # in counts tables, samples are columns (excluing first column)
        # in samples table, samples are rows
        check_id = partial_check_args["check_id"]
        samples_in_file = list(df.columns[1:]) if check_id != "D_0001" else list(df.iloc[:,0])
        if set(samples_in_file) == set(self.samples):
            partial_check_args["debug_message"] = f"{expectedFile.name} exists and samples are correct"
            partial_check_args["severity"] = 30
        else:
            partial_check_args["debug_message"] = f"{expectedFile.name} exists but samples are not as expected: In file: {samples_in_file}, expected: {self.samples}"
            partial_check_args["severity"] = 90
        self.flagger.flag(**partial_check_args)

    def _check_contrasts(self, contrasts_file, partial_check_args: dict):
       """ Performs a check that appropriate number of contrasts generated.

       Also sets contrast groups
       """
       contrasts_df = pd.read_csv(contrasts_file, index_col=0)
       self.factor_groups_versus = set(contrasts_df.columns)
       self.factor_groups = list()
       parsed_factor_groups = [group_versus.split("v") for group_versus in self.factor_groups_versus.copy()]
       for factor_group in parsed_factor_groups:
           self.factor_groups.extend(factor_group)
       self.factor_groups = set(self.factor_groups)

       count_contrasts_from_deseq2 = len(contrasts_df.columns)
       expected_contrasts = self.samplesheet_cross_checks.expected_contrasts

       if count_contrasts_from_deseq2 == expected_contrasts:
           debug_message=f"{contrasts_file.name} contrasts ({count_contrasts_from_deseq2}) matches expected contrasts based on SampleSheet ({expected_contrasts})"
           partial_check_args["debug_message"] = debug_message
           partial_check_args["severity"] = 30
       else:
           debug_message = f"{contrasts_file.name} contrasts ({count_contrasts_from_deseq2})  DOES NOT match expected contrasts based on SampleSheet ({expected_contrasts})"
           partial_check_args["debug_message"] = debug_message
           partial_check_args["severity"] = 90
           self.flagger.flag(**partial_check_args)
