import zipfile
import tempfile
import os
import json
from typing import Tuple
from statistics import median
import logging
log = logging.getLogger(__name__)

from VV.utils import readsWise_outlier_check

# TODO:
    # check total sequences between paired reads match
    # log total sequences max,med,min
    # log percent duplicates max,med,min
    # log percent GC max,med,min

class MultiQC():
    """ Representation of all MultiQC data.
    """
    def __init__(self,
                 multiQC_zip_path,
                 samples,
                 paired_end,
                 outlier_thresholds):
        json_file = self._json_multiQC(multiQC_zip_path)
        with open(json_file, "r") as f:
            data = json.load(f)
        self.data = data
        self.paired_end = paired_end
        self.samples = samples
        # TODO: assert this matches required signature for outlier checks
        self.outlier_thresholds = outlier_thresholds
        self.sample_mapping = self._map_samples()
        if self.paired_end:
            self._check_pair_counts_match()

        self._check_outliers()

        for data_source in self.data['report_data_sources'].keys():
            log.debug(f"Found MultiQC data sourced from {data_source}")
            if data_source == "FastQC":
                log.debug(f"Loading FastQC")
                self.fastQC = self._load_fastQC()
            else:
                log.debug(f"Loading {data_source}: not implemented")

    def _map_samples(self):
        """ Maps each sample to the sample files detected in multiQC

        sample: (forward_data, reverse_data)
        """
        mapping = dict()
        data = self.data['report_general_stats_data'][0]
        forward = None
        reverse = None
        for sample in self.samples:
            for read_name, read_data in data.items():
                if sample in read_name and "R1" in read_name:
                    forward = read_data
                elif sample in read_name and "R2" in read_name:
                    reverse = read_data

            mapping[sample] = (forward, reverse)
        return mapping

    def _check_pair_counts_match(self):
        for sample, sample_data in self.sample_mapping.items():
            forward_count = sample_data[0]['total_sequences']
            reverse_count = sample_data[1]['total_sequences']
            log.debug(f"Read Counts: {sample}: forward {forward_count}: "
                      f"reverse: {reverse_count}")
            if forward_count != reverse_count:
                log.error(f"Sample: {sample} has different forward and reverse reads counts")

    def _check_outliers(self):
        """ Checks for outliers across reads for the following:

            'percent_gc'
            'avg_sequence_length'
            'total_sequences'
            'percent_duplicates'
        """
        for metric in ['percent_gc',
                        'avg_sequence_length',
                        'total_sequences',
                        'percent_duplicates']:

            metric_values = {reads:data[0][metric]
                             for reads,data
                             in self.sample_mapping.items()}
            if self.paired_end:
                metric_values.update({reads:data[1][metric]
                                   for reads,data
                                   in self.sample_mapping.items()})

            log.debug(f"Starting {metric} outlier check")
            outliers = readsWise_outlier_check(metric_values, outlier_stdev=self.outlier_thresholds[metric])
            if outliers:
                log.error(f"FAIL: {metric} outliers {outliers}")
            log.debug(f"Finished {metric} outlier check")


    def _load_fastQC(self):
        data = dict()
        data['files_paths'] = [filepath
                                for filepath
                                in self.data['report_data_sources']['FastQC']['all_sections'].values()]
        data['files'] = [os.path.basename(filepath)
                        for filepath
                        in data['files_paths']]
        data['sample_reads'] = [sample
                                for sample
                                in self.data['report_data_sources']['FastQC']['all_sections'].keys()]

        return data



    def _json_multiQC(self, multiQC_zip_path: str) -> str:
        """ Unzips multiQC and places into a tmp contents folder.
        Returns path to multiQC json file.

        :param multiQC_zip_path: path to multiQC zip file
        """
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(multiQC_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return os.path.join(temp_dir, os.path.splitext(os.path.basename(multiQC_zip_path))[0], "multiqc_data.json")


def validate_verify(multiQC_zip_path: str,
                    paired_end: bool,
                    sequence_length_tolerance: float = 0.05):
    """ Checks multiQC data to ensure a metrics about raw reads are reasonable.

    Logs an error if the average sequence length of any sample significantly
    different than the rest of the data.

    :param multiQC_zip_path: path to multiQC zip file
    :param paired_end: True for assessing paired end reads, False for single end
    :param sequence_length_tolerance: Percent allowed smaller or greater than the median before error is logged
    """
    json_file = _json_multiQC(multiQC_zip_path)
    with open(json_file, "r") as f:
        data = json.load(f)

    # get max,min,median
    avg_sequence_length = _extract_general_stats("avg_sequence_length", data)
    max_avg_seq_len, med_avg_seq_len, min_avg_seq_len = _quick_stats(list(avg_sequence_length.values()))
    log.info(f"INFO: Maximum ReadsWise Average Sequence Length: {max_avg_seq_len}")
    log.info(f"INFO: Median  ReadsWise Average Sequence Length: {med_avg_seq_len}")
    log.info(f"INFO: Minimum ReadsWise Average Sequence Length: {min_avg_seq_len}")
    # define min and max and check
    MAX_ALLOWED_LEN = med_avg_seq_len*(1+sequence_length_tolerance)
    MIN_ALLOWED_LEN = med_avg_seq_len*(1-sequence_length_tolerance)
    log.info(f"Checking if average sequence length is reasonable")
    length_pass = True
    for sample, value in avg_sequence_length.items():
        log.debug(f"{sample} has average sequence length: {value}")
        if not (MAX_ALLOWED_LEN > value > MIN_ALLOWED_LEN):
            log.warning(f"Average sequence length is outside tolerated deviation from median: "
                        f"Sample: {sample}")
            length_pass = False
    if not length_pass:
        log.error(f"FAIL: At least one sample's average sequence length is outside tolerated deviation from median")

'''
def _json_multiQC(multiQC_zip_path: str) -> str:
    """ Unzips multiQC and places into a tmp contents folder.
    Returns path to multiQC json file.

    :param multiQC_zip_path: path to multiQC zip file
    """
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(multiQC_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return os.path.join(temp_dir, os.path.splitext(os.path.basename(multiQC_zip_path))[0], "multiqc_data.json")
'''
def _quick_stats(values: [float]) -> Tuple[float,float,float]:
    """ Given a list of values returns Max, Median and Maximum

    :param values: values to compute stats for
    """
    return (max(values), median(values), min(values))


def _extract_general_stats(extract: str, data: dict) -> dict:
    """ Extracts data from sampleWise multiQC general stats.

    :param extract: The string to extract from report_general_stats_data
    :param data: multiQC report data as directly imported by json.load
    """
    extracted = dict()
    general_stats_by_sample = data["report_general_stats_data"][0]
    for sample, general_stats in general_stats_by_sample.items():
        extracted[sample] = general_stats[extract]
    return extracted
