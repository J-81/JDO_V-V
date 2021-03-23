""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from datetime import datetime
import sys
from pathlib import Path
import math

import pandas as pd

from VV import __version__

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
                 step: str = "General VV",
                 log_to: Path = None):
        self._script = script # location of flagging script
        self._step = step # location of flagging script
        self._severity = FLAG_LEVELS
        self._halt_level = halt_level # level to raise a VV exception at

        self._flag_count = 0 # increments for each flag call, useful for testing

        # timestamp only used for new logs
        self.timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

        # if a file is supplied
        if log_to:
            # if the file already exists (we are appending results to it)
            if log_to.is_file():
                log_to_relative_to_cwd = log_to.absolute().relative_to(Path.cwd())
                print(f"Supplied Existing VV flag log: flag output going into {str(log_to_relative_to_cwd)}")
                self._log_file = Path(log_to)
                self._log_folder = self._log_file.parent
                with open(self._log_file, "a+") as f:
                    f.write(f"#Next Python Command: {' '.join(sys.argv)}\n")
            # if the file does not exist, we want to start the file
            else:
                print(f"Could not find existing log file: {str(log_to)}")
                self._log_file = Path(log_to)
                self._log_folder = self._log_file.parent
                self._start_log_file()
        else:
            print("No existing log file given, starting new log file")
            self._set_timestamped_logfile()
            self._start_log_file()

    def _set_timestamped_logfile(self):
        """ sets log file and log folder """
        self._log_folder = Path("VV_output") / Path(self.timestamp)
        self._log_folder.mkdir(exist_ok=True, parents=True)
        log_filename = f"VV-Results.tsv"
        self._log_file  = self._log_folder / log_filename

    def _start_log_file(self):
        """ Starts a new full log file with a comment header
        """
        print(f"Starting new log file: {self._log_file}")
        with open(self._log_file, "w") as f:
            f.write("#START OF VV RUN:\n")
            f.write(f"#Time started: {self.timestamp}\n")
            f.write(f"#VV Program Version: {__version__}\n")
            f.write(f"#Python Command: {' '.join(sys.argv)}\n")

    def set_step(self, step: str):
        self._step = step

    def set_script(self, script: str):
        self._script = script

    def flag(self,
             entity: str,
             debug_message: str,
             severity: int,
             checkID: str,
             preprocess_debug_messages: bool = True,
             full_path: str = "",
             relative_path: str = "",
             indices: list = [],
             entity_value: float = "NAN",
             max_thresholds: list = [],
             min_thresholds: list = [],
             outlier_thresholds: list = [],
             unique_criteria_results: str = "",
             check_function: str = "",
             ):
        """ Given an issue, logs a flag, prints human readable debug_message
        """
        self._flag_count += 1
        # not required but provides some quality of life improvements in the log debug_messages
        if preprocess_debug_messages:
            # space out consecutive [Number: 1][value: 2] -> [Number: 1] [value: 2]
            debug_message = debug_message.replace("][","] [")
            # significant figure rounding for non-indice related flags
            if "indices" not in debug_message:
                debug_message = self._parse_debug_message_and_round_values_to_sigfig(debug_message)
            #### END PREPROCESS MESSAGES ####

        report = f"{self._severity[severity]}\t{severity}\t{self._step}\t{self._script}\t{entity}\t{debug_message}\t{checkID}\t{full_path}\t{relative_path}\t{indices}\t{entity_value}\t{max_thresholds}\t{min_thresholds}\t{outlier_thresholds}\t{unique_criteria_results}\t{check_function}"
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
                           names=["severity","flag_id","step","script","entity","debug_message","checkID","full_path","relative_path","indices","entity_value","max_thresholds","min_thresholds","outlier_thresholds","unique_critera_results","check_function"]
                           )

    def check_sample_proportions(self,
                                 checkID: str,
                                 check_cutoffs: dict,
                                 protoflag_map: dict):
        df = self._get_log_as_df()
        # filter by checkID
        checkdf = df.loc[df["checkID"] == checkID]

        # compute proportion with proto flags
        flagged = False
        for flag_id in sorted(protoflag_map, reverse=True):
            threshold = check_cutoffs["sample_proportion_thresholds"][flag_id]
            valid_proto_ids = protoflag_map[flag_id]
            valid_proto_count = len(checkdf.loc[checkdf["flag_id"].isin(valid_proto_ids)])
            total_count = len(checkdf)
            proportion = valid_proto_count / total_count
            # check if exceeds threshold
            if proportion > threshold:
                self.flag(entity = "FULL_DATASET",
                          debug_message = (f"{proportion*100}% of samples:files "
                                    f"({valid_proto_count} of {total_count}) "
                                    f"meet criteria for flagging. [threshold: {threshold*100}%]"
                                    ),
                          severity = flag_id,
                          checkID = checkID)
                flagged = True
                break
        if not flagged:
            self.flag(entity = "FULL_DATASET",
                      debug_message = (f"{proportion*100}% of samples:files "
                                f"({valid_proto_count} of {total_count}) "
                                f" does not meet criteria for flagging. [threshold: {threshold*100}%]"
                                ),
                      severity = 30,
                      checkID = checkID)

    def generate_derivative_log(self, log_type: str, samples: list):
        known_log_types = ["only-issues", "by-sample", "by-step"]
        if log_type == "only-issues":
            full_df = self._get_log_as_df()
            output = f"{log_type}__{self._log_file.name}"
            filter_out = [severity for flag_code, severity
                          in FLAG_LEVELS.items()
                          if flag_code <= 30]
            # remove non-issue rows
            derived_df = full_df.loc[~full_df["severity"].isin(filter_out)]
            # remove columns
            derived_df = derived_df.drop(["full_path"], axis=1)
            derived_df.to_csv(self._log_folder / output, index=False, sep="\t")
            print(f">>> Created {output}: Derived from {self._log_file}")
        elif log_type == "by-sample":
            full_df = self._get_log_as_df()
            parent_dir = self._log_folder / Path("bySample")
            parent_dir.mkdir()
            for sample in samples:
                output = parent_dir / f"{sample}__{self._log_file.name}"
                derived_df = full_df.loc[full_df["entity"].str.contains(sample)]
                derived_df.to_csv(output, index=False, sep="\t")
                print(f">>> Created {output}: Derived from {self._log_file}")
        elif log_type == "by-step":
            full_df = self._get_log_as_df()
            parent_dir = self._log_folder / Path("byStep")
            parent_dir.mkdir()
            for step in full_df["step"].unique():
                # remove spaces in step for filename
                output = parent_dir / f"{step.replace(' ', '_')}__{self._log_file.name}"
                derived_df = full_df.loc[full_df["step"] == step]
                derived_df.to_csv(output, index=False, sep="\t")
                print(f">>> Created {output}: Derived from {self._log_file}")
        else:
            raise ValueError(f"{log_type} not implemented.  Try from {known_log_types}")

    def _parse_debug_message_and_round_values_to_sigfig(self,
                                                  debug_message,
                                                  sigfigs = 2,
                                                  ignore_ints = True):
        def is_number(x):
            try:
                float(x)
                return True
            except ValueError:
                return False
        words = debug_message.split()
        new_debug_message = list()
        for i, word in enumerate(words):
            # also catch values that look like this
            # [value: 52.0000000] <- notice the trailing square bracket!
            if word[-1] == "]":
                hasTrailingBracket = True
                word = word[:-1] # remove temporarily
            else:
                hasTrailingBracket = False

            # round numeric values to sigfigs
            is_int = "." not in word
            if is_number(word) and not all([ignore_ints, is_int]):
                original_value = float(word)
                rounded_value = round(original_value, sigfigs - int(math.floor(math.log10(abs(original_value)))) - 1)
                word = str(rounded_value)

            # add back square bracket if removed
            if hasTrailingBracket:
                word += "]"
            new_debug_message.append(word)
        return " ".join(new_debug_message)
