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

        df = pd.read_csv(self.sample_sheet_path)
        self.samples = df["sample_name"].tolist()
        # set attributes for columns with a single unique value
        for col in df.columns:
            unique_values = df[col].unique()
            if len(unique_values) == 1:
                unique_value = unique_values[0]
                setattr(self, col, unique_value)

        # setup filemappings
        if self.paired_end:
            self.raw_reads = {sample:{"forward":df["raw_read1"][i], "forward":df["raw_read2"][i]} for i,sample in enumerate(self.samples)}
        else:
            self.raw_reads = {sample:{"read":df["raw_read1"][i]} for i,sample in enumerate(self.samples)}
        # somewhat patchy, depracated in favor of VV using mapping as arg instead of doing it within the process
        self.raw_reads_dir = Path(df["raw_read1"][0]).parent
        self.trimmed_reads_dir = Path(df["trimmed_read1"][0]).parent
