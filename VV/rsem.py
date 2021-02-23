""" VV related to the output from RSEM results
"""
import os
import logging
log = logging.getLogger(__name__)

from VV.utils import sampleWise_outlier_check, max_median_mean_stdev

class RsemCounts():
    """ Representation of Rsem results for a set of samples.
    Validates:
        - <sample>.genes.results
        - <sample>.isoforms.results
    """
    def __init__(self,
                 samples: str,
                 dir_path: str,
                 outlier_stdev_threshold: float):
        log.debug(f"Checking RSEM Results")
        self.samples = samples
        self.dir_path = dir_path
        log.debug(f"Parsing gene counts")
        self.gene_counts, gene_file_missing = self._parse_gene_counts()

        log.debug(f"Parsing isoform counts")
        self.isoform_counts, isoform_file_missing = self._parse_isoform_counts()

        if len(self.isoform_counts) == 0 or len(self.gene_counts) == 0:
            log.error(f"FAIL: Empty results found for Rsem: {self.isoform_counts}: {self.gene_counts}")

        log.debug(f"Checking for outliers")
        if gene_file_missing or isoform_file_missing:
            log.warning(f"Skipping outlier check, RSEM files missing")
        else:
            self._check_for_outliers("gene_counts", outlier_stdev_threshold)
            self._check_for_outliers("isoform_counts", outlier_stdev_threshold)

    def _parse_counts(self, result_type):
        counts = dict()
        file_missing_flag = False
        for sample in self.samples:
            file_path = os.path.join(self.dir_path,
                                     ,sample
                                     ,f"{sample}.{result_type}.results")
            if not os.path.isfile(file_path):
                log.error(f"FAIL: For {sample}, {file_path} not found")
                continue
            # open and count lines in file
            with open(file_path, "r") as f:
                counts[sample] = len(f.readlines())
        return counts, file_missing_flag

    def _parse_gene_counts(self):
        return self._parse_counts("genes")

    def _parse_isoform_counts(self):
        return self._parse_counts("isoforms")

    def _check_for_outliers(self, result_type, threshold):
        # log max median min
        metric = getattr(self, result_type)
        _max, _median, _min, _stdev = max_median_mean_stdev(metric.values())
        log.debug(f"Unique {result_type} stats: Max: {_max} Median: {_median} "
                  f"Min: {_min} St.Dev: {_stdev}")

        # check for outliers
        outliers = sampleWise_outlier_check(metric,
                                            outlier_stdev=threshold)
        if outliers:
            log.error(f"FAIL: {metric} Outliers detected "
                      f"in Rsem Results: {outliers}")
