""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from datetime import datetime

class Flagger():
    """ Flagging object
    """
    def __init__(self, script):
        self._script = script # location of flagging script
        self._severity = {  30:"Anamoly",
                            50:"Yellow Warning",
                            70:"Red Warning",
                            90:"Fail"}
        self._log_threshold = 30
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        self._log_file = f"{timestamp}_VV_Results.txt"
        with open(self._log_file, "w") as f:
            f.write(f"START OF VV RUN: {timestamp}")

    def flag(self, message, severity, checkID):
        """ Given an issue, logs a flag, prints human readable message
        """
        report = f"{self._severity[severity]}: {message}: source:{self._script}: checkID: {checkID}"
        print(report)
        with open(self._log_file, "w") as f:
            f.write(report)
