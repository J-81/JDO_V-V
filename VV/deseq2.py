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
                 params: dict):
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
        self.has_ERCC = params["hasERCC"]
        self._check_csv_files()

    def _check_csv_files(self):
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
