#! /usr/bin/env python
class Dataset():
    def __init__(self,
                 accession: str,
                 fromGenelab: bool,
                 samples: list):
        self.accession = accession
        self.fromGenelab = fromGenelab
        self.samples = samples

class RNASeq_Dataset(Dataset):
    def __init__(self,
                 library_layout: str,
                 **kwargs):
        super().__init__(**kwargs)

        ALLOWED_LAYOUTS = {"single","paired_end"}

        if library_layout in ALLOWED_LAYOUTS:
            self.library_layout = library_layout
        else:
            raise ValueError(f"Library layout must be from {ALLOWED_LAYOUTS}")

class Datasource():
    def __init__(self):
        pass

class Reads(Datasource):
    def __init__(self, layout_label):
        self.layout_label = layout_label

class Spectroscopy(Datasource):
    def __init__(self, name):
        self.name = "Speccy"

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

from dataclasses import dataclass

@dataclass
class WholeSampleValue:
    name: str
    value: float
    source: Datasource

@dataclass
class PartsOfSampleValues:
    name_parts: str
    name_values: str
    values: dict
    source: Datasource

class RNASeq_Sample(Sample):
    def __init__(self,
                 **kwargs):
         super().__init__(**kwargs)

         # loadable sources of data
         self.reads = "Not Loaded"
         self.alignments = "Not Loaded"
         self.RSEM_counts = "Not Loaded"
         self.Deseq2_counts = "Not Loaded"
         self.DESeq2_DGE = "Not Loaded"

         self._loadable_datasources.append(Reads)

         ## data extracted from loaded data
         # data described in a single value
         # MUST be a float or int
         # key here also is the final user friendly string
         self._single_value = dict()
         #e.g.
         self._single_value["Percent GC"] = WholeSampleValue(name="percent_gc", value=None, source="Raw Reads")

         # data described about a part of the sample
         # MUST be a dict with format. {part:value}, part name
         self._parts_values = dict()

         self._parts_values["Average Phred Score By Base Position"] = \
         PartsOfSampleValues(name_parts="bp", name_values="avg Phred score", values={1:30,2:31,3:31,4:31}, source="Raw Reads")


    def get_single_value(self, key):
        target_WholeSampleValue = self._single_value.get(key)
        if target_WholeSampleValue == None:
            raise ValueError(f"'{key}' is an invalid single value key.")
        elif target_WholeSampleValue.value:
            return target_WholeSampleValue.value
        elif target_WholeSampleValue.value == None:
            raise ValueError(f"'{key}' not loaded.  Must be loaded from {target_WholeSampleValue.source}")

    def get_parts_values(self, key):

        return self._parts_values.get(key, "ERROR-NoSuchPartsValues")


    def load_data(self, datasource):
        super().load_data(datasource)

        if isinstance(datasource, Reads):
            self._load_reads(datasource)

    def _load_reads(self,
                    reads: Reads):
        self.reads = dict()
        self.reads = {Reads.layout_label:Reads}

if __name__ == '__main__':
    x = RNASeq_Dataset(library_layout="paired_end",accession="GLDS-000",fromGenelab=True,samples=["a"])
    s1 =RNASeq_Sample(name="s1", organism="cat", dataset=x)
