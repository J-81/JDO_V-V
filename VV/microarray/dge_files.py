from __future__ import annotations
from pathlib import Path

import pandas as pd

from VV.flagging import Flagger
from VV.utils import filevalues_from_mapping, value_based_checks


class DGEFilesVV():
    def __init__(self,
                 samples: list,
                 expected_contrasts: int,
                 dge_file_dir: Path,
                 cutoffs: dict,
                 flagger: Flagger,
                 ):
        """ Performs VV for limma dge files (reference: VV CHecklist #8,9,10
        """
        print("Running VV for DGE Files")

        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("DGE Files")
        cutoffs_subsection = "limma_dge"
        self.samples = samples
        self.expected_contrasts = expected_contrasts
        self.flagger = flagger
        # generate expected files in the main sample directory

        for file, check_id in [
            (dge_file_dir / "contrasts.csv", "MICROARRAY_D_00012a"),
            (dge_file_dir / "differential_expression.csv", "MICROARRAY_D_00012b"),
            (dge_file_dir / "visualization_output_table.csv", "MICROARRAY_D_00012c"),
        ]:
            checkArgs = dict()
            checkArgs["check_id"] = check_id
            checkArgs["convert_sub_entity"] = False
            checkArgs["entity"] = "All_Samples"
            flagger.flag_file_exists(check_file = file,
                                     partial_check_args = checkArgs,
                                     optional = False)

            # file specific checks
            if file.name in ["contrasts.csv"]:
                self._check_contrasts(file, partial_check_args = checkArgs)

            # file specific checks
            if file.name in ["visualization_output_table.csv"]:
                self._check_visualization_table(file, partial_check_args = checkArgs)

            # file specific checks
            if file.name in ["differential_expression.csv"]:
                self._check_dge_table(file, partial_check_args = checkArgs)


    def _check_visualization_table(self, expectedFile, partial_check_args: dict):
            visualization_df = pd.read_csv(expectedFile, index_col=None)
            flagged = False
            # check all samples have a column
            missing_sample_cols = set(self.samples) - set(visualization_df.columns)
            if missing_sample_cols:
                flagged = True
                debug_message = f"File exists but appears to be missing sample columns {missing_sample_cols}."
                partial_check_args["debug_message"] = debug_message
                partial_check_args["severity"] = 70 # TODO: REESCALATE to 90 UPON CORRECTION: Truncated sample names found in GLDS-121
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
                partial_check_args["severity"] = 70 # TODO: REESCALATE UPON CORRECTION: MISSING: {'GOSLIM_IDS', 'ENSEMBL', 'GENENAME'}
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

       count_contrasts_from_limma_script = len(contrasts_df.columns)
       expected_contrasts = self.expected_contrasts

       if count_contrasts_from_limma_script == expected_contrasts:
           debug_message=f"{contrasts_file.name} contrasts ({count_contrasts_from_limma_script}) matches expected contrasts based on SampleSheet ({expected_contrasts})"
           partial_check_args["debug_message"] = debug_message
           partial_check_args["severity"] = 30
       else:
           debug_message = f"{contrasts_file.name} contrasts ({count_contrasts_from_limma_script})  DOES NOT match expected contrasts based on SampleSheet ({expected_contrasts})"
           partial_check_args["debug_message"] = debug_message
           partial_check_args["severity"] = 90
           self.flagger.flag(**partial_check_args)

    def _check_dge_table(self, expectedFile, partial_check_args: dict):
        dge_df = pd.read_csv(expectedFile, index_col=None)
        flagged = False
        # check all samples have a column
        missing_sample_cols = set(self.samples) - set(dge_df.columns)
        if missing_sample_cols:
            flagged = True
            debug_message = f"Missing sample columns {missing_sample_cols}."
            partial_check_args["debug_message"] = debug_message
            partial_check_args["severity"] = 70 # TODO: REESCALATE TO 90 UPON CORRECTION, GLDS-121 truncated sample names
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
            partial_check_args["severity"] = 70 # TODO: REESCALATE UPON CORRECTION: MISSING: {'GOSLIM_IDS', 'ENSEMBL', 'GENENAME'}
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
