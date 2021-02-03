""" VV for deseq2 output
"""

import os
import logging
log = logging.getLogger(__name__)

import pandas as pd

class Deseq2NormalizedCounts():
    """ Representation of the output from Deseq2
    """
    def __init__(self,
                 samples: str,
                 dir_path: str,
                 has_ERCC: bool):
        log.debug(f"Checking Deseq2 Normalized Counts Results")
        self.samples = samples
        self.dir_path = dir_path
        self.has_ERCC = has_ERCC
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
        check_file = os.path.join(self.dir_path, "SampleTable.csv")
        log.debug(f"Checking {check_file}")
        if os.path.isfile(check_file):
            df = pd.read_csv(check_file, header=0)
            samples_in_file = list(df.iloc[:,0])
            if set(samples_in_file) != set(self.samples):
                log.error(f"FAIL: {check_file} samples do not match ones"
                          f" expected: SampleTable {samples_in_file}"
                          f" expected {self.samples}")
        else:
            log.error(f"FAIL: Missing {check_file}")

        # Unnormalized_Counts.csv Check
        check_file = os.path.join(self.dir_path, "Unnormalized_Counts.csv")
        log.debug(f"Checking {check_file}")
        if os.path.isfile(check_file):
            df = pd.read_csv(check_file, header=0, index_col=0)
            # capture first row of data for comparision
            unnorm_df = df.copy()

            samples_in_file = list(df.columns)
            if set(samples_in_file) != set(self.samples):
                log.error(f"FAIL: {check_file} samples do not match ones"
                          f" expected: Unnormalized_Counts {samples_in_file}"
                          f" expected {self.samples}")

        else:
            log.error(f"FAIL: Missing {check_file}")

        # Normalized_Counts.csv Check
        check_file = os.path.join(self.dir_path, "Normalized_Counts.csv")
        log.debug(f"Checking {check_file}")
        if os.path.isfile(check_file):
            df = pd.read_csv(check_file, header=0, index_col=0)
            # capture first row of data for comparision
            norm_df = df.copy()

            samples_in_file = list(df.columns)
            if set(samples_in_file) != set(self.samples):
                log.error(f"FAIL: {check_file} samples do not match ones"
                          f" expected: Normalized_Counts {samples_in_file}"
                          f" expected {self.samples}")

        else:
            log.error(f"FAIL: Missing {check_file}")

        # ERCC_Normalized_Counts.csv Check
        if self.has_ERCC:
            check_file = os.path.join(self.dir_path, "ERCC_Normalized_Counts.csv")
            log.debug(f"Checking {check_file}")
            if os.path.isfile(check_file):
                df = pd.read_csv(check_file, header=0, index_col=0)
                # capture first row of data for comparision
                ercc_norm_df = df.copy()

                samples_in_file = list(df.columns)
                if set(samples_in_file) != set(self.samples):
                    log.error(f"FAIL: {check_file} samples do not match ones"
                              f" expected: ERCC-Normalized_Counts {samples_in_file}"
                              f" expected {self.samples}")

            else:
                log.error(f"FAIL: Missing {check_file}")


        # length checks
        if self.has_ERCC and len(norm_df) == len(unnorm_df):
            log.error(f"FAIL: Normalized count rows should not be equal to"
                    " Unnormalized count rows in terms of number of rows if ERCC"
                    " Spikein added.  This may indicate ERCC not detected.")

        # find matching gene and compare values
        for i in range(1000):
            if norm_df.index[0] == (unnorm_df.index[i]):
                log.debug(f"Gene in row 1 of NORM: {norm_df.index[0]} should equal"
                f" Gene in row {i} of UNNORM: {unnorm_df.index[i+1]}")
                log.debug(f"Checking values of this row next")
                break


        # Gene name should match
        # values should not
        log.debug(f"Value NORM: {norm_df.iloc[0,:]} should NOT equal"
                f" Value UNNORM: {unnorm_df.iloc[i,:]}")
        if norm_df.iloc[0,:].equals(unnorm_df.iloc[i,:]):
            log.error(f"FAIL: Normalized count values are the same as "
                    "Unnormalized count values.  This means normalization was NOT "
                    " performed.")



        if self.has_ERCC:
            # length checks
            log.debug(f"Count ERCC_NORM: {len(ercc_norm_df.index)} should NOT equal"
                    f" Count UNNORM: {len(unnorm_df.index)}")
            if len(ercc_norm_df.index) == len(unnorm_df.index):
                log.error(f"FAIL: ERCC_Normalized count rows should NOT be equal to"
                        " Unnormalized count rows in terms of number of rows if ERCC"
                        " Spikein added.")

            log.debug(f"Count NORM: {len(norm_df.index)} should equal"
                    f" Count UNNORM: {len(unnorm_df.index)}")
            if len(norm_df.index) != len(ercc_norm_df.index):
                log.error(f"FAIL: The number of Normalized count rows should "
                        " equal the number of ERCC-Normalized count rows.")

            log.debug(f"Value NORM: {norm_df.iloc[0,:]} should NOT equal"
                    f" Value ERCC-NORM: {ercc_norm_df.iloc[0,:]}")
            if norm_df.iloc[0,:].equals(ercc_norm_df.iloc[0,:]):
                log.error(f"FAIL: Normalized count values are the same as "
                        "ERCC normalized count values.  This should differ.")
