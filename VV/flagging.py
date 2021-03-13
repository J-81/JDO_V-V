""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from datetime import datetime
import sys

FLAG_LEVELS = {
    20:"Info-Only",
    30:"Passed-Green",
    50:"Warning-Yellow",
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
        report = f"{self._severity[severity]}\t{self._step}\t{self._script}\t{entity}\t{message}\t{checkID}"
        print(report)
        with open(self._log_file, "a") as f:
            f.write(report + "\n")

        # full exit upon severe enough issue
        if severity >= self._halt_level:
            raise VVError("SEVERE ISSUE, HALTING V-V AND ANY ADDITIONAL PROCESSING")
