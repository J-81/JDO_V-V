""" Handles functions related to file searching.  Much of the functionality if borrowed from MultiQC's robust file searching """
import importlib.resources
import fnmatch
import re
import os
from pathlib import Path

from multiqc.utils import report
import yaml


def monkey_patch_search_file(pattern, f, module_key):
    """ Adds in additional search pattern methods """
    original_matched = report._search_file_original(pattern, f, module_key)
    dir_fn_matched = False
    if pattern.get("dir_fn_re") is not None:
        if re.match(pattern["dir_fn_re"], os.path.join(f["root"],f["fn"])):
            dir_fn_matched = True
        return dir_fn_matched
    else:
        # fallback on fn and contents matching
        return original_matched

# add in additional match methods
report._search_file_original = report.search_file
report.search_file = monkey_patch_search_file

class FileSearcher():

    def __init__(self, sp_config: str, analysis_dir: list = None):
        """ creates a fileSearcher object.  
        This wraps the multiQC based file searching functionality, while replacing the default file_search patterns 

        params:
          sp_config: path to a search_patterns.yaml config file. See: https://github.com/ewels/MultiQC/blob/master/multiqc/utils/search_patterns.yaml for formatting example
          analsis_dir: list of paths to search for files within
        """
        with importlib.resources.path("VV.config", sp_config) as fpath:
            with open(fpath, "r") as f:
                self.search_patterns = yaml.safe_load(f)
        
        # replace default search patterns with custom ones
        report.config.sp = self.search_patterns

        # replace search location
        if not analysis_dir:
            analysis_dir = [os.getcwd()]
        report.config.analysis_dir = analysis_dir


        # replace default ignore files
        report.config.fn_ignore_files = ['*.DS_Store','*.py[cod]','*[!s][!u][!m][!_\\.m][!mva][!qer][!cpy].html']
        self.report = report

    def get_files(self, modules: list = None):
        # search all modules if not specified
        if not modules:
            modules = list(self.search_patterns)
        self.report.get_filelist(modules)
        self.files = self.report.files
