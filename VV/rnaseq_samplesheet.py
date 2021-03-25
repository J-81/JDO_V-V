""" Reads RNASeq samplesheet
"""
from pathlib import Path

import pandas as pd

class RNASeqSampleSheet():
    """ Holds data for RNASeq samplesheet
    """
    def __init__(self,
                 sample_sheet: Path):

        self.sample_sheet_path = sample_sheet

        self.df = pd.read_csv(self.sample_sheet_path)
