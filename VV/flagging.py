""" Functions to create a consistent system for flagging issues found during
the V-V checks.  Uses logging
"""
from datetime import datetime
import sys
import argparse
import configparser

def _parse_args():
    """ Parse command line args.
    """
    parser = argparse.ArgumentParser(description='Perform Automated V&V on '
                                                 'raw reads.')
    parser.add_argument('--config', metavar='c', nargs='+', required=True,
                        help='INI format configuration file')

    args = parser.parse_args()
    print(args)
    return args


args = _parse_args()
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)

class Flagger():
    """ Flagging object
    """
    def __init__(self, script):
        self._script = script # location of flagging script
        self._severity = {  20:"Info",
                            30:"Anamoly",
                            50:"Yellow Warning",
                            70:"Red Warning",
                            90:"Fail"}
        self._log_threshold = 30
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        self._log_file = f"{timestamp}_VV_Results.txt"
        with open(self._log_file, "w") as f:
            f.write("START OF VV RUN:\n")
            f.write(f"Time started: {timestamp}\n")
            f.write(f"Python Command: {' '.join(sys.argv)}\n")

    def flag(self, message, severity, checkID):
        """ Given an issue, logs a flag, prints human readable message
        """
        report = f"{self._severity[severity]}: {message}: source:{self._script}: checkID: {checkID}"
        print(report)
        with open(self._log_file, "a") as f:
            f.write(report + "\n")

        # full exit upon severe enough issue
        if severity >= config["Logging"].getint("HaltSeverity"):
            print("SEVERE ISSUE, HALTING V-V AND ANY ADDITIONAL PROCESSING")
            sys.exit()

class FlaggedEntity():
    """ Representation of flaggable entities.

    Unique indentifier format:
    DATASET:SAMPLES:READSET:READS:POSITIONS

    """
