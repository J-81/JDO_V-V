""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from typing import Callable
from datetime import datetime
import sys
from pathlib import Path
import math
from collections import OrderedDict, defaultdict
from functools import wraps, partial

import pandas as pd
pd.set_option('mode.chained_assignment', None)

from VV import __version__
#from VV.checks import BaseCheck

FLAG_LEVELS = {
    20:"Info-Only",
    30:"Passed-Green",
    49:"Proto-Warning-Yellow",
    50:"Warning-Yellow",
    59:"Proto-Warning-Red",
    60:"Warning-Red",
    70: "DEVELOPER-ONLY: TEMPORARY RELAXED FLAG",
    80:"Issue-Unable_To_Check",
    90:"Issue-Halt_Processing",
    94:"Check did not know how to handle return",
    95:"Check function raised unhandled exception",
    }

# order of the full report lines in the log
FULL_LOG_HEADER = [
    "sample",
    "sub_entity",
    "severity",
    "flag_id",
    "step",
    "script",
    "user_message",
    "debug_message",
    "check_id",
    "filename",
    "full_path",
    "flagged_positions",
    "position_units",
    "entity_value",
    "entity_value_units",
    "outlier_comparison_type",
    "max_thresholds_to_flag_ids",
    "min_thresholds_to_flag_ids",
    "max_min_thresholds_units",
    "outlier_stdev_thresholds_to_flag_ids",
    ]

FULL_REPORT_LINE_TEMPLATE = OrderedDict.fromkeys(FULL_LOG_HEADER)

class Flag():
    """ An object representing a flag """
    allFlags = list()

    def __init__(self, 
                 code: int,
                 check, #TODO fix BaseCheck type hint here
                 entity: str = "none supplied",
                 msg: str = "No Message Supplied",
                 short_msg: str = None,
                 data: dict = None):
        self.entity = entity
        self.code = code
        self.check = check # a Check instance, includes data about the check itself
        self.msg = msg # a verbose message describing the flag
        self.short_msg = short_msg if short_msg else msg # fallback on msg if short msg is not supplied, optional
        self.data = data # detailed data used to produce a given flag conclusion, optional
        
        # add to running list of generated flags
        self.allFlags.append(self)

    def __repr__(self):
        return f"Flag code: {self.code}. Message: '{self.msg}'"


class VVError(Exception):
    pass

class _Flagger():
    """ Flagging object
    """
    def __init__(self,
                 script: str,
                 halt_level: int,
                 log_to: Path,
                 step: str = "General VV"):
        self._cwd = Path.cwd()
        self._flag_dict = defaultdict(lambda: 0)
        self._script = script # location of flagging script
        self._step = step # location of flagging script
        self._severity = FLAG_LEVELS
        self._halt_level = halt_level # level to raise a VV exception at
        self.derivatives = list() # these mimic the flag calls conditionally to generate derivative logs

        self._flag_count = 0 # increments for each flag call, useful for testing

        # timestamp only used for new logs
        self.timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

        # use absolute path
        log_to = log_to.resolve()
        # if the file already exists (we are appending results to it)
        if log_to.is_file():
            log_to_relative_to_cwd = log_to.absolute().relative_to(Path.cwd())
            print(f"Supplied Existing VV flag log: flag output going into {str(log_to_relative_to_cwd)}")
            self._log_file = log_to
            self._log_folder = self._log_file.parent
            with open(self._log_file, "a+") as f:
                f.write(f"#Next Python Command: {' '.join(sys.argv)}\n")
        # if the file does not exist, we want to start the file
        else:
            print(f"Could not find existing log file: {str(log_to)}")
            self._log_file = log_to
            self._log_folder = self._log_file.parent
            self._log_folder.mkdir(exist_ok=True, parents=True)
            self._start_log_file()
        # load log file as dataframe
        self.df = self._get_log_as_df()

    def _start_log_file(self):
        """ Starts a new full log file with a comment header
        """
        print(f"Starting new log file: {self._log_file.relative_to(Path.cwd())}")
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
             check_id: str,
             full_path: str,
             filename: str,
             sub_entity: str = "NA",
             user_message: str = "NA",
             preprocess_debug_messages: bool = True,
             convert_sub_entity: bool = True,
             flagged_positions: list = "NA",
             entity_value: float = "NA",
             entity_value_units: str = "NA",
             outlier_comparison_type: str = "NA",
             max_thresholds: list = "NA",
             min_thresholds: list = "NA",
             outlier_thresholds: list = "NA",
             units_for_thresholds: str = "NA",
             position_units: str = "NA"
             ):
        """ Given an issue, logs a flag, prints human readable debug_message

        If a user message is not supplied,
        debug message will be used in its place

        Note for programmers: this means if the debug message
        is good enough as a user message, leaving user message blank to allow
        override works great!
        """
        self._flag_count += 1
        self._flag_dict[severity] += 1
        # not required but provides some quality of life improvements in the log debug_messages
        if preprocess_debug_messages:
            # space out consecutive [Number: 1][value: 2] -> [Number: 1] [value: 2]
            debug_message = debug_message.replace("][","] [")
            # significant figure rounding for non-indice related flags
            if "flagged_positions" not in debug_message:
                debug_message = self._parse_debug_message_and_round_values_to_sigfig(debug_message)
            #### END PREPROCESS MESSAGES ####

        # convert sub entity labels according to a mapping if supplied
        if convert_sub_entity and sub_entity != "NA":
            CONVERT_DICT = {"forward":"R1","read":"R1","reverse":"R2"}
            if not (new_name := CONVERT_DICT.get(sub_entity)):
                raise ValueError(f"Failed to convert {sub_entity} to new label")
            else:
                sub_entity = new_name

        # replace user message with debug if user message not supplied
        if user_message == "NA":
            user_message = debug_message


        # masks for entity_value_units
        # mainly to improve end user readability
        # but still use automatically parsed keys
        ENTITY_VALUE_UNITS_MASKS = {
            "bin_sum-fastqc_per_base_n_content_plot" : "sum_percent_of_n_per_base",
            "bin_mean-fastqc_per_base_n_content_plot" : "mean_percent_of_n_per_base",
            "fastqc_overrepresented_sequencesi_plot-Top over-represented sequence" : "percent_of_top_over-represented_sequence_per_total",
            "fastqc_overrepresented_sequencesi_plot-Sum of remaining over-represented sequences" : "percent_of_remaining_over-represented_sequences_per_total",
        }
        if mask_for_entity_value_units := ENTITY_VALUE_UNITS_MASKS.get(entity_value_units, None):
            #print(f"Masking entity_value_units key '{entity_value_units}' with '{mask_for_entity_value_units}'")
            entity_value_units = mask_for_entity_value_units

        # in most cases, make threshold units the same as the entity units
        if units_for_thresholds == "NA":
            units_for_thresholds = entity_value_units # should be safe in most cases, even where entity value units is NA (just replaces NA with NA)


        report = FULL_REPORT_LINE_TEMPLATE.copy()
        report.update({
                  "sample": entity,
                  "sub_entity": sub_entity,
                  "severity": self._severity[severity],
                  "flag_id": severity,
                  "step": self._step,
                  "script":self._script,
                  "user_message": user_message,
                  "debug_message": debug_message,
                  "check_id": check_id,
                  "full_path": full_path,
                  "filename": filename,
                  "flagged_positions": flagged_positions,
                  "entity_value": entity_value,
                  "entity_value_units": entity_value_units,
                  "outlier_comparison_type": outlier_comparison_type,
                  "max_thresholds_to_flag_ids": max_thresholds,
                  "min_thresholds_to_flag_ids": min_thresholds,
                  "max_min_thresholds_units": units_for_thresholds,
                  "outlier_stdev_thresholds_to_flag_ids": outlier_thresholds,
                  "position_units": position_units
                  })

        # ensure report dict matches expected headers
        assert report.keys() == FULL_REPORT_LINE_TEMPLATE.keys(), "Report keys MUST be the ones expected full log header."
        add_df = pd.DataFrame.from_records([report])
        # add to in memory log
        self.df = pd.concat([self.df, add_df])
        #if len(self.df) % 50 == 0:
        #    print(self.df) # debug
        # add to file log, if first log add header
        if len(self.df) == 1:
            add_df.to_csv(self._log_file, mode="a", index=False, sep="\t")
        else:
            add_df.to_csv(self._log_file, mode="a", index=False, sep="\t", header=False)

        # full exit upon severe enough issue
        if severity >= self._halt_level:
            raise VVError(f"SEVERE ISSUE, HALTING V-V AND ANY ADDITIONAL PROCESSING\nHalting flag message: '{report['debug_message']}'")

    def flag_file_exists(self,
                         check_file: Path,
                         partial_check_args: dict,
                         optional: bool = False
                         ):
        if not check_file.is_file():
            partial_check_args["debug_message"] = f"{check_file.name} not found"
            partial_check_args["full_path"] = str(check_file.resolve())
            partial_check_args["filename"] = check_file.name
            partial_check_args["severity"] = 90 if not optional else 50
        else:
            partial_check_args["debug_message"] = f"{check_file.name} exists"
            partial_check_args["full_path"] = str(check_file.resolve())
            partial_check_args["filename"] = check_file.name
            partial_check_args["severity"] = 30
        self.flag(**partial_check_args)

    def _get_log_as_df(self):
        return pd.read_csv(self._log_file,
                           sep="\t",
                           comment="#",
                           names=FULL_LOG_HEADER,
                           )

    def check_sample_proportions(self,
                                 check_args: dict,
                                 check_cutoffs: dict,
                                 protoflag_map: dict):
        df = self._get_log_as_df()
        # filter by check_id
        checkdf = df.loc[df["check_id"] == check_args["check_id"]]

        check_args["entity"] = "All_Samples"

        # compute proportion with proto flags
        flagged = False
        for flag_id in sorted(protoflag_map, reverse=True):
            threshold = check_cutoffs["sample_proportion_thresholds"][flag_id]
            valid_proto_ids = [str(id) for id in protoflag_map[flag_id]]
            valid_proto_count = len(checkdf.loc[checkdf["flag_id"].isin(valid_proto_ids)])
            total_count = len(checkdf)
            proportion = valid_proto_count / total_count
            # check if exceeds threshold
            if proportion > threshold:
                check_args["debug_message"] = (f"{proportion*100}% of samples:files "
                          f"({valid_proto_count} of {total_count}) "
                          f"meet criteria for flagging. [threshold: {threshold*100}%]"
                          )
                check_args["severity"] = flag_id
                self.flag(**check_args)
                flagged = True
                break

        if not flagged:
            check_args["debug_message"] = (f"{proportion*100}% of samples:files "
                                           f"({valid_proto_count} of {total_count}) "
                                           f" does not meet criteria for flagging. [threshold: {threshold*100}%]"
                                           )
            check_args["severity"] = 30
            self.flag(**check_args)

    def generate_derivative_log(self, log_type: str, samples: list):
        known_log_types = ["only-issues", "by-sample", "by-step", "all-by-entity"]
        if log_type == "only-issues":
            full_df = self._get_log_as_df()
            output = self._log_folder / f"{log_type}__{self._log_file.name}"
            filter_out = [severity for flag_code, severity
                          in FLAG_LEVELS.items()
                          if flag_code <= 30]
            # remove non-issue rows
            derived_df = full_df.loc[~full_df["severity"].isin(filter_out)]
            # remove columns
            derived_df = derived_df.drop(["full_path"], axis=1)
            derived_df.to_csv(output, index=False, sep="\t", header=False, na_rep="NA")
            print(f">>> Created {output.relative_to(self._cwd)}: Derived from {self._log_file.relative_to(self._cwd)}")


        elif log_type == "by-sample":
            full_df = self._get_log_as_df()
            parent_dir = self._log_folder / Path("bySample")
            parent_dir.mkdir(exist_ok=True)
            for sample in samples:
                output = parent_dir / f"{sample}__{self._log_file.name}"
                derived_df = full_df.loc[full_df["sample"].str.contains(sample)]
                derived_df.to_csv(output, index=False, sep="\t", na_rep="NA")
                print(f">>> Created {output.relative_to(self._cwd)}: Derived from {self._log_file.relative_to(self._cwd)}")



        elif log_type == "by-step":
            full_df = self._get_log_as_df()
            parent_dir = self._log_folder / Path("byStep")
            parent_dir.mkdir(exist_ok=True)
            for step in full_df["step"].unique():
                # remove spaces in step for filename
                output = parent_dir / f"{step.replace(' ', '_')}__{self._log_file.name}"
                derived_df = full_df.loc[full_df["step"] == step]
                derived_df.to_csv(output, index=False, sep="\t", na_rep="NA")
                print(f">>> Created {output.relative_to(self._cwd)}: Derived from {self._log_file.relative_to(self._cwd)}")



        elif log_type == "all-by-entity":
            full_df = self._get_log_as_df()
            output = self._log_folder / f"all-by-sample.tsv"
            filter_out = [severity for flag_code, severity
                          in FLAG_LEVELS.items()
                          if flag_code <= 30]
            # remove non-issue rows
            derived_df = full_df.loc[~full_df["severity"].isin(filter_out)]

            # create derived report message
            def _make_report(row):
                #sub_entity_repr = f"({row['sub_entity']})" if row['sub_entity'] != "nan" else ""
                return f"[{row['severity']}] {row['user_message']}"
            derived_df["report"] = derived_df.apply(_make_report, axis="columns")
            # only use columns
            #derived_df = derived_df[["check_id","sample","report"]]
            #derived_df = derived_df.drop_duplicates()
            with open(output.with_suffix('.txt'), "w") as f:
                # iterate by unique entities
                for entity in derived_df["sample"].unique():
                    entity_df = derived_df.loc[derived_df["sample"] == entity]
                    f.write(f"SAMPLE: {entity}\n")
                    for i, (_, row) in enumerate(entity_df.iterrows()):
                        if i == 0:
                            continue # skip header
                        #print(row['sub_entity'], type(row['sub_entity']))
                        #print(f"ROW:  {row['user_message']} {type( row['user_message'])}")
                        message = row['user_message'] if not row['user_message'] != "" else row['debug_message']
                        message_line = f"{i}. ({row['sub_entity']}) " if str(row["sub_entity"]) != "nan" else f"{i}. "
                        message_line += message
                        details_line = f"Severity: {FLAG_LEVELS[int(row['flag_id'])]} ({row['flag_id']})  CheckID: {row['check_id']}"
                        f.write(f"  {message_line}\n    {details_line}\n\n")
            print(f">>> Created {output.with_suffix('.txt').relative_to(self._cwd)}: Derived from {self._log_file.relative_to(self._cwd)}")


            '''# create summary table for percentage of samples in certain flag categories
            red_filter = derived_df["severity"] == "Warning-Red"
            red_tally_df = derived_df.loc[red_filter].groupby(by=['sample','step']).agg('count')["severity"]
            yellow_filter = derived_df["severity"] == "Warning-Yellow"
            yellow_tally_df = derived_df.loc[yellow_filter].groupby(by=['sample','step']).agg('count')["severity"]
            '''

            # create summary of percentages
            # adds in "All_Samples" to each set before subtracting it
            def _percent_flagged(step, df):
                # skip this
                red_filter = df["severity"] == "Warning-Red"
                yellow_filter = df["severity"] == "Warning-Yellow"
                total_samples = len(df["sample"][~df["sample"].isin(["All_Samples","sample"])].unique())
                if total_samples == 0:
                    return None
                if step == "any":
                    percent_red_samples = len(df.loc[red_filter]["sample"][~df["sample"].isin(["All_Samples","sample"])].unique()) / total_samples * 100
                    percent_yellow_samples = len(df.loc[yellow_filter]["sample"][~df["sample"].isin(["All_Samples","sample"])].unique()) / total_samples * 100
                    return (percent_red_samples, percent_yellow_samples)
                else:
                    step_filter = (df["step"] == step)
                    percent_red_samples = len(df.loc[red_filter & step_filter]["sample"][~df["sample"].isin(["All_Samples","sample"])].unique()) / total_samples * 100
                    percent_yellow_samples = len(df.loc[yellow_filter & step_filter]["sample"][~df["sample"].isin(["All_Samples","sample"])].unique()) / total_samples * 100
                    return (percent_red_samples, percent_yellow_samples)

            output_summary = self._log_folder /"Summary.tsv"
            with open(output_summary, "w") as f:
                # write header
                f.write(f"Step\tPercent_Samples_Red_Warning\tPercent_Samples_Yellow_Warning\n")
                for step in full_df["step"].unique():
                    if step == "step":
                        step = "any"
                    if percents := _percent_flagged(step, full_df):
                        f.write(f"{step}\t{percents[0]:.2f}\t{percents[1]:.2f}\n")
                    else:
                        f.write(f"{step}\t{'Not assessed: No single sample flags for this step found'}\t{'Not assessed: No single sample flags for this step found'}\n")
            print(f">>> Created {output_summary.relative_to(self._cwd)}: Derived from {self._log_file.relative_to(self._cwd)}")


            # transpose and save
            try:
                derived_df = derived_df.pivot(index=['step','check_id','sub_entity'], columns='sample', values='report')
                derived_df = derived_df.sort_values(by="sample",axis="columns")
                #derived_df = derived_df.reindex(sorted(derived_df.columns), axis=1)
                derived_df.to_csv(output, index=True, sep="\t", na_rep="NA")
                print(f">>> Created {output.relative_to(self._cwd)}: Derived from {self._log_file.relative_to(self._cwd)}")
            except ValueError: # raised as Index contains duplicate entries, cannot reshape
                pass
            # sort columns



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


class NullFlagger(_Flagger):
    """ A flagger that does not write output
    """
    def flag(*args,**kwargs):
        pass

_instance = None

def Flagger(**kwargs):
    global _instance
    if not _instance or kwargs.get("force_new_flagger"):
        if kwargs.get("force_new_flagger"):
            kwargs.pop("force_new_flagger")
        _instance = _Flagger(**kwargs)
    return _instance

def check(flagger: _Flagger, 
          return_interactions: dict,
          check_id: str = "not suppied",
          full_path: str = "not supplied",
          file_name: str = "not supplied",
          entity: str = "not supplied"):
    """ Generic check that generates flags based on output from a function """
    code = 0
    def inner_function(function: Callable):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                result = function(*args, **kwargs)
                print(code)
                severity, formatter = return_interactions.get(code, None)
                debug_message = formatter(result)
                if response == None:
                    # i.e. function ran but response not programmed
                    severity = 94
                    debug_message = f"Check function: {function} returned, but check doesn't know how to handle returned result: {result}"
            except Exception as e:
                raise e
                # uncaught issues are flagged
                severity = 95
                debug_message = f"Unhandled Exception: {e}, refer to V&V developer"
            flagger.flag(check_id=check_id, 
                         full_path=full_path, 
                         debug_message=debug_message, 
                         filename=file_name,
                         severity=severity, 
                         entity=entity)
        
        return wrapper
    return inner_function

def init_check(flagger):
    """ Returns a check decorator with a supplied flagger object attached """
    
    return partial(check, flagger=flagger)
