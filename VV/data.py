""" Data structures representing RNASeq Datasets in GeneLab

"""
import zipfile
import tempfile
import os
import logging
log = logging.getLogger(__name__)

from isatools.io import isatab_parser
from isatools.io.isatab_parser import ISATabRecord, ISATabAssayRecord

class RNASeq_Sample():
    """ Representation of one sample and associated data files
    """
    def __init__(self, name):
        """
        """
        self.name = name
        self.data = dict()

class Assay():
    """ Generic assay functionality and data representation
    """
    def __init__(self, assay: ISATabAssayRecord):
        self._assay = assay
        self.samples = self._get_samples()

    def _get_samples(self):
        return [node.name
                for node in self._assay.nodes.values()
                if node.ntype == "Sample Name"]

class RNASeqAssay(Assay):
    """ Representation of a transcription profiling by RNASeq
    assay including associated samples
    """
    def __init__(self, assay: ISATabAssayRecord):
        super().__init__(assay)
        self.platform = self._assay.metadata['Study Assay Technology Platform']


class Dataset():
    """ Datasets are composed of multiple samples and their associated sample files
    """

    def __init__(self, isa_zip_path):
        """
        """
        self._isa_data = self._parse_isa_dir_from_zip(isa_zip_path) # composition of ISATabRecord
        # assertions consistent with GLDS ISA files
        # only 1 study
        assert len(self._isa_data.studies) == 1
        self.study = self._isa_data.studies[0]

        self.assays, self._unimplemented_assays = self._load_assays()
        """
        self.samples = {sample_node.name:sample_node
                        for sample_node in assay
                        for assay in self.assays}
        #self.paired_end = None
        #self.dataset_type = None
        """

    def __repr__(self):
        print_assay_data = [f"{assay_name} with {len(assay.samples)} samples"
                            for assay_name, assay in self.assays.items()]

        return f"Study Title: {self.study.metadata['Study Title']}\n\tKnown Assay: " + \
                "\n\tImplemented Assays: ".join(print_assay_data) + \
                "\n\tUnimplemented Assays: ".join(self._unimplemented_assays) + \
                "\n\tNote: Any unimplemented assays printed above present in ISA, but accessing data from these " + \
                "assays have not been implemented yet."

    def _load_assays(self):
        implemented_assays = dict()
        unimplemented_assays = list()

        for assay in self.study.assays:
            assay_type = assay.metadata['Study Assay Measurement Type']
            assay_tech = assay.metadata['Study Assay Technology Type']
            if  assay_type == 'transcription profiling' and \
                assay_tech == 'RNA Sequencing (RNA-Seq)':
                log.debug(f"Found RNASeq Transcription Profiling Assay, loaded")
                implemented_assays["transcription profiling by RNASeq"] = RNASeqAssay(assay)
            else:
                unimplemented_assays.append(f"{assay_type} via {assay_tech}")
                log.warning(f"Found {assay_type} via {assay_tech}; "
                            "however, automated V-V for this assay type"
                            "not implemented in this package")
        return implemented_assays, unimplemented_assays


    def get_assay(self, assay_name: str) -> ISATabAssayRecord:
        try:
            return self.assays[assay_name]
        except KeyError:
            log.error(f"{assay_name} Assay not found in this study")

    def get_samples_names(self, assay_name: str) -> [str]:
        try:
            return [sample_node.name
                    for sample_node in self.assays[assay_name].nodes.values()
                    if sample_node.ntype == "Sample Name"]
        except KeyError:
            log.error(f"{assay_name} Assay not found in this study")

    def _get_study(self):
        """ Returns study name, checks only one study should exist
        """
        count_studies = len(self._investigation.studies)
        assert  (count_studies == 1),\
                f"Should be one study in the ISA file. {count_studies} found."

        study = self._investigation.studies[0]
        return study


    def _unzip_ISA(self, isa_zip_path: str) -> str:
        """ Unzips ISA and places into a tmp contents folder.
        Returns path to temporary directory holding ISA zip file contents.

        :param isa_zip_path: path to isa zip file
        """
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(isa_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir

    def _print_metadata(self, isaobject: ISATabRecord, level: int = 0):
        """ Prints metadata for an ISATabRecord.
        Converts empty strings into None for visibility

        :param isaobject: ISATabRecord as parsed with the isatools library
        :param level: Adds tabs before printing
        """
        for key,metadatum in isaobject.metadata.items():
            # enhance visibility for empty entries
            if (not metadatum and metadatum != 0):
                metadatum = None
                # indent
                print("\t"*level,end='')
                print(f"{key}: {metadatum}")

    def _parse_isa_dir_from_zip(self, isa_zip_path: str, pretty_print: bool = False) -> ISATabRecord:
        """ Unzips ISA zip files as found in GLDS metadata folders.

        ISA record metadata signature should match the specs here:
        https://isa-specs.readthedocs.io/en/latest/isamodel.html

        :param isa_zip_path: path to isa zip file
        :param pretty_print: print contents of parsed file, useful for debugging
        """
        INVESTIGATION_INDENT = 1
        STUDY_INDENT = 2
        ASSAY_INDENT = 3

        isa_temp_dir = self._unzip_ISA(isa_zip_path)
        investigation = isatab_parser.parse(isatab_ref=isa_temp_dir)

        # only print if requested, useful for debugging parsing and data extraction
        if pretty_print:
            print(f"INVESTIGATION: ISA ZIP: {os.path.basename(isa_zip_path)}")
            print("="*95)
            self._print_metadata(investigation, level=INVESTIGATION_INDENT)
            for i, study in enumerate(investigation.studies):
                print("\n")
                print(f"STUDY {i+1} of {len(investigation.studies)}")
                print("="*95)
                self._print_metadata(study, level=STUDY_INDENT)
                for design_descriptor in study.design_descriptors:
                    [print("\t"*STUDY_INDENT + f"{k}:  {v}") for k,v in design_descriptor.items()]

                # iterature thorugh assays
                for j, assay in enumerate(study.assays):
                    print("\n")
                    print(f"ASSAY {j+1} of {len(study.assays)} from STUDY {i+1}")
                    print("="*95)
                    self._print_metadata(assay, level=ASSAY_INDENT)

        return investigation

    def _parse_ISA(self, isa_zip_path: str):
        """ Extracts investigation sample names given a GLDS isa zip file path.
        Returns a dictionary

        :param isa_zip_path: path to isa zip file
        """
        #isa_data = dict()
        investigation = self._parse_isa_dir_from_zip(isa_zip_path)
        return investigation
        """
        # each ISA should only contain one study
        assert len(investigation.studies) == 1

        # study level
        study = None
        study_key = f"STUDY: {study.metadata['Study Title']}"
        self.study = study.metadata['Study Title']
        isa_data[study_key] = dict()
        for assay in study.assays:
            # assay level
            assay_key = f"ASSAY: {assay.metadata['Study Assay Measurement Type']}"
            sample_nodes = [node for node in assay.nodes.values() if node.ntype == "Sample Name"]
            isa_data[study_key][assay_key] = [sample_node.name for sample_node in sample_nodes]

        return isa_data
        """
