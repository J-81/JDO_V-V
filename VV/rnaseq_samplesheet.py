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
            self.raw_reads = {sample:{"forward":Path(df["raw_read1"][i]), "reverse":Path(df["raw_read2"][i])} for i,sample in enumerate(self.samples)}
            self.trimmed_reads = {sample:{"forward":Path(df["trimmed_read1"][i]), "reverse":Path(df["trimmed_read2"][i])} for i,sample in enumerate(self.samples)}
        else:
            self.raw_reads = {sample:{"read":Path(df["raw_read1"][i])} for i,sample in enumerate(self.samples)}
            self.trimmed_reads = {sample:{"read":Path(df["trimmed_read1"][i])} for i,sample in enumerate(self.samples)}

        # extract factors
        factors = dict()
        for col in df.columns:
            # E.G. Factor Value[Spaceflight]
            if col.startswith("Factor Value["):
                factor = col.split("[")[1].replace("]","").strip()
                factor_values = df[col].unique().tolist()
                factors[factor] = factor_values
        self.factors = factors
        # compute expected contrasts
        expected_contrasts = 1
        # get unique combinations of factor options
        for factor_set in self.factors.values():
            num_factors = len(factor_set)
            expected_contrasts = expected_contrasts*num_factors
        # get number of possible combinations (excluding mirror combinations)
        self.expected_contrasts = expected_contrasts*(expected_contrasts-1)

        # patch directories for star and rsem
        # TODO: change associated VV to use direct sample directories instead
        self.STAR_Alignment_dir_mapping = df.set_index("sample_name")["STAR_Alignment"].to_dict()
        self.RSEM_Counts_dir_mapping = df.set_index("sample_name")["RSEM_Counts"].to_dict()

        # set to path
        self.DESeq2_NormCount = Path(self.DESeq2_NormCount)
        self.DESeq2_DGE = Path(self.DESeq2_DGE)
