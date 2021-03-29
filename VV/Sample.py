#! /usr/bin/env python
from __future__ import annotations
from dataclasses import dataclass

from VV.Dataset import Dataset, RNASeq_Dataset
from VV.Datasource import Datasource, Reads

class Sample():
    def __init__(self,
                 name: str,
                 organism: str,
                 dataset: Dataset,
                 ):
        self.name = name
        self.organism = organism
        self.dataset = dataset
        self._loadable_datasources = []

    def load_data(self, datasource):
        """ Loads data from a datasource
        """
        if not isinstance(datasource, tuple(self._loadable_datasources)):
            raise ValueError(f"This sample type doesn't have a way to load {type(datasource)}")
        print(f"Loading {datasource} into {self}")

class RNASeq_Sample(Sample):
    def __init__(self,
                 reads_list: list[Reads] = None,
                 **kwargs):
         super().__init__(**kwargs)

         # loadable sources of data
         self._reads = dict()
         if reads_list:
             for reads in reads_list:
                 self._loadable_datasources(reads)

         self.alignments = "Not Loaded"
         self.RSEM_counts = "Not Loaded"
         self.Deseq2_counts = "Not Loaded"
         self.DESeq2_DGE = "Not Loaded"

         self._loadable_datasources.append(Reads)

    @property
    def reads(self):
        return self._reads

    @reads.getter
    def reads(self):
        if self._reads:
            return self._reads
        else:
            raise ValueError("No Reads have been loaded!")

    def get_single_value(self, key):
        target_WholeSampleValue = self._single_value.get(key)
        if target_WholeSampleValue == None:
            raise ValueError(f"'{key}' is an invalid single value key.")
        elif target_WholeSampleValue.value:
            return target_WholeSampleValue.value
        elif target_WholeSampleValue.value == None:
            raise ValueError(f"'{key}' not loaded.  Must be loaded from {target_WholeSampleValue.source}")

    def get_parts_values(self, key):
        target_PartsOfSampleValues = self._parts_values.get(key)
        if target_PartsOfSampleValues == None:
            raise ValueError(f"'{key}' is an invalid parts values key.")
        elif target_PartsOfSampleValues.value:
            return target_PartsOfSampleValues.value
        elif target_PartsOfSampleValues.value == None:
            raise ValueError(f"'{key}' not loaded.  Must be loaded from {target_PartsOfSampleValues.source}")

    def load_data(self, datasource):
        super().load_data(datasource)

        if isinstance(datasource, Reads):
            self._load_reads(datasource)

    def _load_reads(self,
                    reads: Reads):
        self._reads[reads.layout_label] = reads

if __name__ == '__main__':
    x1 = RNASeq_Dataset(library_layout="paired_end",accession="GLDS-000",fromGenelab=True,samples=["a"])
    s1 = RNASeq_Sample(name="s1", organism="cat", dataset=x1)
    RAW_READ_PATH = "/home/joribello/Documents/OneDrive/NASA/Fall2020/project/V-V_scripts/VV_testing/GLDS-194/00-RawData/Fastq/Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_raw.fastq.gz"
    r1 = Reads(path=RAW_READ_PATH, layout_label="forward")
    RAW_READ_MQC = "/home/joribello/Documents/OneDrive/NASA/Fall2020/project/V-V_scripts/VV_testing/GLDS-194/00-RawData/FastQC_Reports/raw_multiqc_report/multiqc_data/multiqc_data.json"
    r1.load_from_mqc(RAW_READ_MQC)
    s1.load_data(r1)
