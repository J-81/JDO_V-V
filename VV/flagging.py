""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from datetime import datetime
import sys
from pathlib import Path

import pandas as pd

FLAG_LEVELS = {
    20:"Info-Only",
    30:"Passed-Green",
    49:"Proto-Warning-Yellow",
    50:"Warning-Yellow",
    59:"Proto-Warning-Red",
    60:"Warning-Red",
    90:"Issue-Halt_Processing"
    }


class VVError(Exception):
    pass

class Flagger():
    """ Flagging object
    """
    def __init__(self,
                 script: str,
                 halt_level: int,
                 step: str = "General VV",):
        self._script = script # location of flagging script
        self._step = step # location of flagging script
        self._severity = FLAG_LEVELS
        self._halt_level = halt_level # level to raise a VV exception at
        self._log_threshold = 30

        self.timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        self.log_folder = Path("VV_output") / Path(self.timestamp)
        self.log_folder.mkdir(exist_ok=True, parents=True)
        self._log_filename = f"VV_Results.tsv"
        self._log_file = self.log_folder / self._log_filename

        with open(self._log_file, "w") as f:
            f.write("#START OF VV RUN:\n")
            f.write(f"#Time started: {self.timestamp}\n")
            f.write(f"#Python Command: {' '.join(sys.argv)}\n")

    def set_step(self, step: str):
        self._step = step

    def set_script(self, script: str):
        self._script = script

    def flag(self,
             entity: str,
             message: str,
             severity: int,
             checkID: str):
        """ Given an issue, logs a flag, prints human readable message
        """
        report = f"{self._severity[severity]}\t{severity}\t{self._step}\t{self._script}\t{entity}\t{message}\t{checkID}"
        #print(report)
        with open(self._log_file, "a") as f:
            f.write(report + "\n")

        # full exit upon severe enough issue
        if severity >= self._halt_level:
            raise VVError(f"SEVERE ISSUE, HALTING V-V AND ANY ADDITIONAL PROCESSING\nSee {self._log_file}")

    def _get_log_as_df(self):
        return pd.read_csv(self._log_file,
                           sep="\t",
                           comment="#",
                           names=["severity","flag_id","step","script","entity","message","checkID"])

    def check_sample_proportions(self,
                                 checkID: str,
                                 check_params: dict,
                                 protoflag_map: dict):
        df = self._get_log_as_df()
        # filter by checkID
        checkdf = df.loc[df["checkID"] == checkID]

        # compute proportion with proto flags
        flagged = False
        for flag_id in sorted(protoflag_map, reverse=True):
            threshold = check_params["sample_proportion_thresholds"][flag_id]
            valid_proto_ids = protoflag_map[flag_id]
            valid_proto_count = len(checkdf.loc[checkdf["flag_id"].isin(valid_proto_ids)])
            total_count = len(checkdf)
            proportion = valid_proto_count / total_count
            # check if exceeds threshold
            if proportion > threshold:
                self.flag(entity = "FULL_DATASET",
                          message = (f"{proportion*100}% of samples:files "
                                    f"({valid_proto_count} of {total_count}) "
                                    f"meet criteria for flagging. [threshold: {threshold*100}%]"
                                    ),
                          severity = flag_id,
                          checkID = checkID)
                flagged = True
                break
        if not flagged:
            self.flag(entity = "FULL_DATASET",
                      message = (f"{proportion*100}% of samples:files "
                                f"({valid_proto_count} of {total_count}) "
                                f" does not meet criteria for flagging. [threshold: {threshold*100}%]"
                                ),
                      severity = 30,
                      checkID = checkID)

    def generate_derivative_log(self, log_type: str, samples: list):
        known_log_types = ["only-issues", "by-sample", "by-step"]
        if log_type == "only-issues":
            full_df = self._get_log_as_df()
            output = f"{log_type}:{self._log_filename}"
            filter_out = [severity for flag_code, severity
                          in FLAG_LEVELS.items()
                          if flag_code <= 30]
            derived_df = full_df.loc[~full_df["severity"].isin(filter_out)]
            derived_df.to_csv(self.log_folder / output, index=False)
            print(f">>> Created {output}: Derived from {self._log_file}")
        elif log_type == "by-sample":
            full_df = self._get_log_as_df()
            parent_dir = self.log_folder / Path("bySample")
            parent_dir.mkdir()
            for sample in samples:
                output = parent_dir / f"{sample}:{self._log_filename}"
                derived_df = full_df.loc[full_df["entity"].str.contains(sample)]
                derived_df.to_csv(output, index=False, sep="\t")
                print(f">>> Created {output}: Derived from {self._log_file}")
        elif log_type == "by-step":
            full_df = self._get_log_as_df()
            parent_dir = self.log_folder / Path("byStep")
            parent_dir.mkdir()
            for step in full_df["step"].unique():
                output = parent_dir / f"{step}:{self._log_filename}"
                derived_df = full_df.loc[full_df["step"] == step]
                derived_df.to_csv(output, index=False, sep="\t")
                print(f">>> Created {output}: Derived from {self._log_file}")
        else:
            raise ValueError(f"{log_type} not implemented.  Try from {known_log_types}")
