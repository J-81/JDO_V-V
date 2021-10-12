""" Reads RNASeq samplesheet
"""
from pathlib import Path
from itertools import combinations

import pandas as pd
from pandas import DataFrame

class RNASeqSampleSheet():
    """ Holds data for RNASeq samplesheet
    """
    def __init__(self,
                 sample_sheet: Path,
                 DEBUG:bool = False):

        self.sample_sheet_path = sample_sheet
        self.DEBUG = DEBUG
        df = pd.read_csv(self.sample_sheet_path)
        self.df = df
        self.contrasts_table, self.expected_contrasts = self.generate_contrasts_table()
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

        # patch directories for star and rsem
        # TODO: change associated VV to use direct sample directories instead
        self.STAR_Alignment_dir_mapping = df.set_index("sample_name")["STAR_Alignment"].to_dict()
        self.RSEM_Counts_dir_mapping = df.set_index("sample_name")["RSEM_Counts"].to_dict()

        # set up RSeQC output mapping
        print(list(df.columns))
        self.RSeQC_infer_experiment = {sample:{"infer_experiment":Path(df["rseqc_output__infer_experiment"][i])} for i,sample in enumerate(self.samples)}

        # set to path
        self.DESeq2_NormCount = Path(self.DESeq2_NormCount)
        self.DESeq2_DGE = Path(self.DESeq2_DGE)

    def generate_contrasts_table(self) -> DataFrame:
        """ Generates a contrast table that should be similar to the one created by RISA
        """
        # generate factor_group column
        # this column is a string of factors
        # i.e. '(A & B & C)'
        factor_cols = list(filter(lambda col: col.startswith("Factor Value["), self.df.columns))
        assert len(factor_cols) != 0, "There MUST be at least factor value column in the runsheet"
        print(f"DEBUG: Found factor columns: {factor_cols}") if self.DEBUG else ...
        self.df["factor_group"] = "(" + self.df[factor_cols].agg(" & ".join, axis=1) + ")"

        # generate all combinations for pairwise factor groups
        unique_factor_groups = self.df["factor_group"].unique()
        print(f"DEBUG: Unique factor groups ({len(unique_factor_groups)}): {unique_factor_groups}") if self.DEBUG else ...
        # get all pairs
        unique_contrasts = [pair for pair in combinations(unique_factor_groups, 2)]

        # for each pair, generate a contrast
        unique_contrasts = ["v".join(pair) for pair in unique_contrasts] + ["v".join(pair[::-1]) for pair in unique_contrasts]

        contrasts_df = pd.DataFrame(columns = unique_contrasts)

        # TODO: add in formated columns like R deseq2 script contrast table
        return contrasts_df, len(contrasts_df.columns)

if __name__ == "__main__":
    import sys

    print("ONLY FOR DEBUG USAGE")
    runsheet = RNASeqSampleSheet(sys.argv[1], DEBUG=True)
    print(runsheet.expected_contrasts)
    print(runsheet.contrasts_table)
