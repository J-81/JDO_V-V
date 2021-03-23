""" Reads RNASeq samplesheet
"""
from pathlib import Path

import pandas as pd

class RNASeqSampleSheet():
    """ Holds data for RNASeq samplesheet
    """
    def __init__(self,
                 samplesheet: Path):

        self.samplesheet_path = samplesheet

        self.df = pd.read_csv(self.samplesheet_path)

        self.cross_check = dict()
        self.cross_check["DF"] = self.df
