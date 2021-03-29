from abc import abstractmethod
from pathlib import Path
import json

from ValueContainers import WholeSampleValue, PartsOfSampleValues

class ValidationError(Exception):
    """ Errors when validating an existing file """
    pass

class ExtractionError(Exception):
    """ Errors when extracting data from what appears to be a valid file """
    pass

class Datasource():
    def __init__(self,
                 path: Path,
                 extract_now: bool = False,
                 ):
        self._path = Path(path)
        self._isExtracted = False
        self._isValid = False
        if extract_now:
            self.extract()
            self._validate()

    def _validate_wrapper(validation_func):
        """ Validate the file(s)
        """
        def validate(self):
            # check existence
            if not self._path.exists():
                raise FileNotFoundError(f"{self._path} does not exist!")
            try:
                validation_func(self)
                self._isValid = True
            except ValidationError:
                print("Failed to validate file! Halting extraction.")
                raise ExtractionError("Validation failed")
        return validate

    def _extract_wrapper(extract_func):
        """ Extract from validated file(s)
        """
        def extract(self):
            try:
                self._validate()
                extract_func(self)
                self._isExtracted = True
            except ExtractionError as e:
                print(f"Failed to extract data, reason: {e}")
        return extract

    @abstractmethod
    @_validate_wrapper
    def _validate(self):
        pass

    @abstractmethod
    @_extract_wrapper
    def extract(self):
        """ Extracts data from file(s) expected at path
        """
        pass

class Reads(Datasource):
    def __init__(self, layout_label,**kwargs):
        super().__init__(**kwargs)
        self.layout_label = layout_label

    @Datasource._validate_wrapper
    def _validate(self):
        if 2 == 1:
            print("Validated!")
        else:
            raise ValidationError("That's not how math works!")

    @Datasource._extract_wrapper
    def extract(self):
        self.filesize = self._path.stat().st_size

    def load_from_mqc(self, mqc_path):
        """ Loads more data about the reads file from a multiQC json
        """
        with open(mqc_path, "r") as f:
            raw_data = json.load(f)

        ###  extract general stats
        for file_data in raw_data["report_general_stats_data"]:
            for filename, data in file_data.items():
                if filename == _get_suffixless(self._path):
                    for key, value in data.items():
                        newValue = WholeSampleValue( name = key, value = value, value_units = key, source = self)
                        setattr(self, key, newValue)

        ### extract from plots
        for plot_name, data in raw_data["report_plot_data"].items():
            # different kinds of plot data need to be extracted with different methods
            plot_type = data["plot_type"]
            if plot_type == "bar_graph":
                self._extract_from_bar_graph(data, plot_name)
            elif plot_type == "xy_line":
                self._extract_from_xy_line_graph(data, plot_name)
            else:
                raise ValueError(f"Unknown plot type {plot_type}. Data parsing not implemented for multiQC {plot_type}")

    def _extract_from_bar_graph(self, data, plot_name):
        # this should be a list with one entry
        assert len(data["samples"]) == 1
        for i, filename in enumerate(data["samples"][0]):
            if filename == _get_suffixless(self._path):
                target_index = i
        # iterate through data from datasets
        # this should be a list with one entry
        assert len(data["datasets"]) == 1
        units = data["config"]["ylab"]
        for sub_data in data["datasets"][0]:
            name = sub_data["name"]
            values = sub_data["data"]
            name = _sanitize_attribute_keys(name)
            newValue = WholeSampleValue( name = name, value = values[target_index], value_units = units, source = self)
            setattr(self, name, newValue)
            print(f"Loaded {name} from {plot_name} in MultiQC")

    def _extract_from_xy_line_graph(self, data, plot_name):
        # determine data mapping for samples in multiqc (which are files)
        # and samples in a dataset (which may have a forward and reverse read file)

        # Iterate through datasets (each typically representing one sample)
        # Nested list of list, top level list includes percentage and counts

        # plots with multiple value types are detected
        multiple_value_types = True if len(data["datasets"]) > 1 else False

        # plots with bins are detected
        if "categories" in data["config"].keys():
            bins = [str(bin) for bin in data["config"]["categories"]]
            isCategorical = True
        else:
            bins = False
            isCategorical = False


        # dataset represents an entire plot (i.e. all lines)
        # Note: for xy plots with both percent and raw counts, there will be two datasets
        for i, dataset in enumerate(data["datasets"]):
            if multiple_value_types:
                data_label = f"-{data['config']['data_labels'][i]['name']}"
            else:
                data_label = ""

            # dataset entry represents one sample (i.e. one line from the line plot)
            for dataset_entry in dataset:
                file_name = dataset_entry["name"]
                # sometimes this includes an additional string
                # E.G Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_raw - illumina_universal_adapter
                # taking the first split token should work
                file_name = file_name.split()[0]

                # values is a list of [index,value]
                values = dataset_entry["data"]
                # for plots with bins, add bin string to values iterable
                if isCategorical:
                    values = zip(bins, values)
                    these_bins = bins
                else:
                    these_bins = [bin for bin, value in values]
                # three level nested dict entries for xy graphs
                # {sample: {sample_file-plot_type: {index: value}}}
                data_key = _sanitize_attribute_keys(f"{plot_name}{data_label}")
                newValues = PartsOfSampleValues( name_parts = data["config"]["xlab"], value_units = data["config"]["ylab"], values = dict(), source = self)
                # for non-categorical bins, each values should be an [index,value]
                for j, value in values:
                    newValues.values[j] = float(value)
            setattr(self, data_key, newValues)
            print(f"Loaded {data_key} from {plot_name} in MultiQC")

def _sanitize_attribute_keys(key):
    return key.replace("-","").replace(" ","_")

def _get_suffixless(path):
    #print(f"From: {path}")
    while path.suffixes: # return empty list when empty
        path = Path(path.stem)
    #print(f"To: {path}")
    return str(path)

if __name__ == '__main__':
    RAW_READ_PATH = "/home/joribello/Documents/OneDrive/NASA/Fall2020/project/V-V_scripts/VV_testing/GLDS-194/00-RawData/Fastq/Mmus_BAL-TAL_LRTN_BSL_Rep1_B7_R1_raw.fastq.gz"
    r1 = Reads(path=RAW_READ_PATH, layout_label="forward")
    RAW_READ_MQC = "/home/joribello/Documents/OneDrive/NASA/Fall2020/project/V-V_scripts/VV_testing/GLDS-194/00-RawData/FastQC_Reports/raw_multiqc_report/multiqc_data/multiqc_data.json"
    r1.load_from_mqc(RAW_READ_MQC)
