""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""

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


    def flag(self, message, severity):
        """ Given an issue, logs a flag, prints human readable message
        """
        print(f"{self._severity[severity]}: {message}: source:{self._script}")
