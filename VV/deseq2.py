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
                 params: dict,
                 cross_checks: dict):
        print(f"Starting VV for DESEQ2 script output")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("DESEQ2_OUTPUT")
        self.flagger = flagger
        self.params = params

        #print(f"Checking Deseq2 Normalized Counts Results")
        self.samples = samples
        self.counts_dir_path = counts_dir_path
        self.dge_dir_path = dge_dir_path
        self.has_ERCC = params["hasERCC"]
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
        entity = "FULL_DATASET"
        checkID_to_file = {
            "D_0001" : self.counts_dir_path / "SampleTable.csv",
            "D_0002" : self.counts_dir_path / "Unnormalized_Counts.csv",
            "D_0003" : self.counts_dir_path / "Normalized_Counts.csv",
            }
        if self.params["hasERCC"]:
            checkID_to_file["D_0004"] = self.counts_dir_path / "ERCC_Normalized_Counts.csv"

        for checkID, expectedFile in checkID_to_file.items():
            # check file existence
            if expectedFile.is_file():
                # check if samples match expectation
                df = pd.read_csv(expectedFile, header=0)
                # in counts tables, samples are columns (excluing first column)
                # in samples table, samples are rows
                samples_in_file = list(df.columns[1:]) if checkID != "D_0001" else list(df.iloc[:,0])
                if set(samples_in_file) == set(self.samples):
                    message = f"{expectedFile.name} exists and samples are correct"
                    self.flagger.flag(message = message,
                                      severity = 30,
                                      checkID = checkID,
                                      entity = entity)
                else:
                    message = f"{expectedFile.name} exists but samples are not as expected: In file: {samples_in_file}, expected: {self.samples}"
                    self.flagger.flag(message = message,
                                      severity = 90,
                                      checkID = checkID,
                                      entity = entity)

            else:
                message = f"{expectedFile.name} does not exist"
                self.flagger.flag(message=(f"Missing {expectedFile}"),
                              severity=90,
                              checkID=checkID,
                              entity = entity)

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
        checkID_to_file = {
            "D_0005" : self.dge_dir_path / "contrasts.csv",
            "D_0006" : self.dge_dir_path / "differential_expression.csv",
            "D_0007" : self.dge_dir_path / "visualization_output_table.csv",
            "D_0008" : self.dge_dir_path / "visualization_PCA_table.csv",
            }
        if self.params["hasERCC"]:
            checkID_to_file["D_0009"] = self.dge_dir_path / Path("ERCC_NormDGE") / "ERCCnorm_contrasts.csv"
            checkID_to_file["D_0010"] = self.dge_dir_path / Path("ERCC_NormDGE") / "ERCCnorm_differential_expression.csv"
            checkID_to_file["D_0011"] = self.dge_dir_path / Path("ERCC_NormDGE") / "visualization_output_table_ERCCnorm.csv"
            checkID_to_file["D_0012"] = self.dge_dir_path / Path("ERCC_NormDGE") / "visualization_PCA_table_ERCCnorm.csv"

        for checkID, expectedFile in checkID_to_file.items():
            # check file existence
            if expectedFile.is_file():
                # file specific checks
                if expectedFile.name == "contrasts.csv":
                    self._check_contrasts(expectedFile, checkID = checkID, entity = entity)

                # no file specific checks needed
                else:
                    message = f"{expectedFile.name} exists. No other filespecific checks requested."
                    self.flagger.flag(message = message,
                                      severity = 30,
                                      checkID = checkID,
                                      entity = entity)

            else:
                message = f"{expectedFile.name} does not exist"
                self.flagger.flag(message=(f"Missing {expectedFile}"),
                              severity=90,
                              checkID=checkID,
                              entity = entity)

    def _check_contrasts(self, contrasts_file, checkID, entity):
       """ Performs a check that appropriate number of contrasts generated
       """
       contrasts_df = pd.read_csv(contrasts_file, index_col=0)

       count_contrasts_from_deseq2 = len(contrasts_df.columns)

       ## Extract expected contrasts from samplesheet
       samplesheet_df = self.samplesheet_cross_checks["DF"]
       factor_cols = [col for col in samplesheet_df.columns if col.startswith("Factor Value[")]
       factor_unique_options = samplesheet_df[factor_cols].nunique(axis=0).to_dict()
       expected_contrasts = 1
       # get unique combinations of factor options
       for key, value in factor_unique_options.items():
           expected_contrasts = expected_contrasts*value
       # get number of possible combinations (excluding mirror combinations)
       expected_contrasts = expected_contrasts*(expected_contrasts-1)

       print(f"From DESEQ2: {count_contrasts_from_deseq2}")
       print(f"EXPECTED: {expected_contrasts}")

       if count_contrasts_from_deseq2 == expected_contrasts:
           self.flagger.flag(message=(f"Contrasts.csv contrasts ({count_contrasts_from_deseq2}) matches expected contrasts based on SampleSheet ({expected_contrasts})"),
                             severity=30,
                             checkID=checkID,
                             entity = entity)
       else:
           self.flagger.flag(message=(f"Contrasts.csv contrasts ({count_contrasts_from_deseq2})  DOES NOT match expected contrasts based on SampleSheet ({expected_contrasts})"),
                             severity=90,
                             checkID=checkID,
                             entity = entity)
