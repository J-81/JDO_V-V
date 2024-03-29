#! /usr/bin/env python
""" Parser for multiQC data
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import namedtuple, defaultdict, namedtuple
from typing import Union, Callable
import configparser
import argparse
from pathlib import Path
import gzip
import json
from statistics import stdev, median, mean

@dataclass
class Subset:
    name: str
    datakey: str
    samples: list = field(repr=False)
    values: Union[list, dict] = field(repr=False)

@dataclass
class OneValueData:
    """ Representation of data for a single sample from a bar graph or general stats
    """
    datakey: str
    units: str
    value: float

@dataclass
class IndexedValuesData:
    """ Representation of data for a single sample from a XY line graph
    """
    datakey: str
    units: str
    bins: list
    bin_units: str
    values: dict


class MultiQC():
    OUTLIER_COMPARISION = {"median":median,
                           "mean":mean}

    def __init__(self, multiQC_json: Path,
                       file_mapping: dict,
                       outlier_comparision_point: str = "median"):
        try:
            self.outlier_comparision = self.OUTLIER_COMPARISION[outlier_comparision_point]
        except KeyError:
            raise ValueError(f"Outlier comparision point not defined.  Select from {list(self.OUTLIER_COMPARISION.keys())}")
        self.samples = list(file_mapping.keys())
        self.file_mapping = file_mapping
        self.file_labels = list(file_mapping[self.samples[0]].keys())

        # extracts data from multiQC json file.
        self.data = self._extract_multiQC_data(json_file = multiQC_json, samples = self.samples)
        self.sample_wise_data_keys = list(self.data[self.samples[0]].keys())

        # holds subsets computed by user
        self.subsets = defaultdict(dict)

    def compile_subset(self, samples_subset, key, aggregator: Callable = None):
        compiled = None

        # check samples_subset is a true subset
        assert set(self.samples).issuperset(set(samples_subset)), \
               f"Samples supplied ({set(samples_subset)}) are not a subset of {self.samples}"
        # check key is in extracted data
        # removed as this check is sample-wise
        # assert key in self.sample_wise_data_keys, f"Missing key {key}"

        for sample in samples_subset:
            # handle cases where not every sample is plotted
            # this occurs for instance when only a limited number of samples
            # have adapter content, while are adapter-free and unplotted
            data = self.data[sample].get(key)
            if data == None:
                print(f"No data for {sample} for {key}")
                continue # skip this sample, unplotted and data does not exist
            if isinstance(data, OneValueData):
                data = data.value
                # initiate aggregate data type to match
                # if already initiated, this does not affect aggregate
                compiled = list() if not compiled else compiled
                compiled.append(data)
            elif isinstance(data, IndexedValuesData):
                # these must be {index:value} dicts of length 1
                data = data.values
                # initiate aggregate data type to match
                # if already initiated, this does not affect aggregate
                compiled = defaultdict(list) if not compiled else compiled
                for index, value in data.items():
                    compiled[index].append(value)
            else:
                print(data)
                raise ValueError(f"For {key}, {type(data)} type for data is unexpected.  Aggregation not implemented.")

        # if aggregator supplied, aggregate across bins by using the function
        if aggregator:
            aggregated_compiled = list()
            values_only = list(compiled.values())
            # transpose
            values_only = list(map(list, zip(*values_only)))
            for i,values in enumerate(values_only):
                aggregated_compiled.append(aggregator(values))
            # set return variable to finished aggregation
            compiled = aggregated_compiled


        # if compiled is a defaultdict, lock back as dict to avoid accessing unfilled keys
        if isinstance(compiled, defaultdict):
            compiled = dict(compiled)

        return compiled

    def detect_outliers(self, key: str, deviation: float, subset_samples: list = None):
        # if subset samples not given, assume all samples for outlier detection
        if not subset_samples:
            subset_samples = self.samples
        values = self.compile_subset(subset_samples, key)
        outliers = list()
        # handle one value per sample style data
        if type(values) == list:
            _stdev = stdev(values)
            _median = median(values)
            if _stdev == 0:
                #print("Standard Deviation equals zero for {key}! No outliers detected!")
                return outliers
            for i, value in enumerate(values):
                stdevs_from_median = abs(value - _median) / _stdev
                if stdevs_from_median > deviation:
                    outliers.append((subset_samples[i], stdevs_from_median))

        elif type(values) == dict:
            for index, values in values.items():
                # line graphs that did not start at the origin
                # (values of zero before a certain x value - e.g. length distribution plot)
                # these do not have entries and must be corrected with explicit zeros
                # add zeroes to length of subset_samples
                implicit_zeroes = len(subset_samples) - len(values)
                if implicit_zeroes:
                    values.extend([0]*implicit_zeroes)
                _stdev = stdev(values)
                _median = median(values)
                if _stdev == 0:
                    #print(f"Standard Deviation equals zero for {key}:{index}. No outliers values.")
                    continue
                for i, value in enumerate(values):
                    stdevs_from_median = abs(value - _median) / _stdev
                    if stdevs_from_median > deviation:
                        outliers.append((subset_samples[i], index, stdevs_from_median))
        else:
            print(type(values))
            raise ValueError("Unknown type for outlier detection")
        if outliers:
            #print(f"Outliers detected!")
            pass
        else:
            #print(f"No outliers detected!")
            pass
        return outliers

    def _sample_filelabel_from_filename(self, query_filename: str):
        """ Given a filename.  Return the file label and sample based on file_mapping.
        """
        matched = False
        for sample, file_map in self.file_mapping.items():
            for filelabel, search_file in file_map.items():
                # search_file: # has extension and parent paths, these are removed when comparing
                # query_filename: sample1_R1 # notice no extension
                if query_filename in str(search_file):
                    if not matched:
                        matched = (sample, filelabel)
                    else:
                        raise ValueError(f"File name {query_filename} matched multiple filenames in provided mapping {self.file_mapping}")
        if matched:
            return matched
        else:
        # no matches
            raise ValueError(f"File name {query_filename} did not match any in provided mapping {self.file_mapping}")

    # data extraction functions
    # TODO: These should return a value that will be assigned directly to the data mapping
    def _extract_multiQC_data(self, json_file: Path, samples):
        data_mapping = defaultdict(lambda: defaultdict(dict))
        with open(json_file, "r") as f:
            raw_data = json.load(f)

        ###  extract general stats
        for file_data in raw_data["report_general_stats_data"]:
            for filename, data in file_data.items():
                cur_sample, filelabel = self._sample_filelabel_from_filename(filename)
                for key, value in data.items():
                    full_key = f"{filelabel}-{key}"
                    data_mapping[cur_sample][full_key] = \
                        OneValueData( datakey = full_key,
                                      value = value,
                                      units = key
                                         )

        ### extract plot data

        # extract fastqc_sequence_counts_plot
        for plot_name, plot_data in raw_data["report_plot_data"].items():
            # different kinds of plot data need to be extracted with different methods
            plot_type = plot_data["plot_type"]
            if plot_type == "bar_graph":
                data_mapping = self._extract_from_bar_graph(plot_data, plot_name, data_mapping, samples)
            elif plot_type == "xy_line":
                data_mapping = self._extract_from_xy_line_graph(plot_data, plot_name, data_mapping, samples)
            elif plot_type == "heatmap":
                print(f"Warning: plot type 'heatmap' is not yet implemented: data_mapping will NOT include {plot_name}")
                continue
                #data_mapping = self._extract_from_heatmap(plot_data, plot_name, data_mapping, samples)
            else:
                raise ValueError(f"Unknown plot type {plot_type}. Data parsing not implemented for multiQC {plot_type}")

        # lock data mapping to parsed data by converting by to dict (from defaultdict)
        data_mapping = dict(data_mapping)
        for sample in self.samples:
            data_mapping[sample] = dict(data_mapping[sample])
        return data_mapping

    """
    def _extract_from_heatmap(self, data, plot_name, data_mapping, samples):
        # determine data mapping for samples in multiqc (which are files)
        # and samples in a dataset (which may have a forward and reverse read file)
        mqc_samples_to_samples = dict()
        # this should be a list with one entry
        assert len(data["ycats"]) == 1
        for i, mqc_sample in enumerate(data["ycats"][0]):
            matching_samples = [sample for sample in samples if sample in mqc_sample]
            # only one sample should map
            assert len(matching_samples) == 1

            sample = matching_samples[0]
            mqc_samples_to_samples[i] = (self._sample_filelabel_from_filename(mqc_sample))

        # iterate through data from datasets
        # this should be a list with one entry
        assert len(data["datasets"]) == 1
        units = data["config"]["ylab"]
        for sub_data in data["datasets"][0]:
            name = sub_data["name"]
            values = sub_data["data"]
            for i, value in enumerate(values):
                sample, sample_file = mqc_samples_to_samples[i]
                key = f"{sample_file}-{plot_name}-{name}"
                data_mapping[sample][key] = \
                    OneValueData( datakey = key, units = units , value = values[i])
        return data_mapping
    """

    def _extract_from_bar_graph(self, data, plot_name, data_mapping, samples):
        # determine data mapping for samples in multiqc (which are files)
        # and samples in a dataset (which may have a forward and reverse read file)
        mqc_samples_to_samples = dict()
        # this should be a list with one entry
        assert len(data["samples"]) == 1
        for i, mqc_sample in enumerate(data["samples"][0]):
            matching_samples = [sample for sample in samples if sample in mqc_sample]
            # only one sample should map
            assert len(matching_samples) == 1

            sample = matching_samples[0]
            mqc_samples_to_samples[i] = (self._sample_filelabel_from_filename(mqc_sample))

        # iterate through data from datasets
        # this should be a list with one entry
        assert len(data["datasets"]) == 1
        units = data["config"]["ylab"]
        for sub_data in data["datasets"][0]:
            name = sub_data["name"]
            values = sub_data["data"]
            for i, value in enumerate(values):
                sample, sample_file = mqc_samples_to_samples[i]
                key = f"{sample_file}-{plot_name}-{name}"
                data_mapping[sample][key] = \
                    OneValueData( datakey = key, units = units , value = values[i])
        return data_mapping

    def _extract_from_xy_line_graph(self, data, plot_name, data_mapping, samples):
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
                sample, sample_file = self._sample_filelabel_from_filename(file_name)
                # for plots with bins, add bin string to values iterable
                if isCategorical:
                    values = zip(bins, values)
                    these_bins = bins
                else:
                    these_bins = [bin for bin, value in values]
                # three level nested dict entries for xy graphs
                # {sample: {sample_file-plot_type: {index: value}}}
                data_key = f"{sample_file}-{plot_name}{data_label}"
                data_mapping[sample][data_key] = \
                    IndexedValuesData( datakey = data_key,
                                       units = data["config"]["ylab"],
                                       bins = these_bins,
                                       bin_units = data["config"]["xlab"],
                                       values = dict()) # data is populated later
                cur_data_mapping_entry = data_mapping[sample][data_key]

                # for non-categorical bins, each values should be an [index,value]
                for j, value in values:
                    cur_data_mapping_entry.values[j] = float(value)
        return data_mapping
