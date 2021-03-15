""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from datetime import datetime
import sys
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
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        self._log_file = f"{timestamp}_VV_Results.tsv"
        with open(self._log_file, "w") as f:
            f.write("#START OF VV RUN:\n")
            f.write(f"#Time started: {timestamp}\n")
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
            raise VVError("SEVERE ISSUE, HALTING V-V AND ANY ADDITIONAL PROCESSING")

    def check_sample_proportions(self,
                                 checkID: str,
                                 check_params: dict,
                                 protoflag_map: dict):
        df = pd.read_csv(self._log_file,
                        sep="\t",
                        comment="#",
                        names=["severity","flag_id","step","script","entity","message","checkID"])
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
