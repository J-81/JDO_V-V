""" Defines logic for vv protocols
VV protocols are steps of V&V to perform including parameters from a yml file.
They define where to output flag results

Examples of a VV protocol:
    1. V&V for entire RNASeq pipeline output
    2. V&V for the STAR alignment step for the RNASeq pipeline (e.g. to perform V&V in-tandem with processing).
    3. Manual V&V for a set of plots (here, usage of 'input' can be used to capture the V&V performers feedback in structured manner).

Each VV protocol:
    must be subclass of BaseProtocol
    is associated with one and only one yml file
    must import all checks
"""
import abc
import importlib
from pathlib import Path
import inspect
import re
import datetime
from typing import Tuple

import yaml
from pandas import DataFrame

from VV.flagging import Flag
from VV.checks import BaseCheck

_PACKAGED_CONFIG_FILES = list()
for resource in importlib.resources.contents("VV.config"):
    with importlib.resources.path("VV.config",resource) as f:
        if re.match(".*_(sp|checks).yml", str(f)):
            _PACKAGED_CONFIG_FILES.append(f)

class BaseProtocol(abc.ABC):

    def __init__(self, check_config, sp_config, vv_dir):
        # check if yaml files exist first
        assert Path(check_config).is_file(), "Check Config file supplied doesn't exist!"
        assert Path(sp_config).is_file(), "Check Config file supplied doesn't exist!"
        self.check_config_f = str(check_config)
        self.sp_config_f = str(sp_config)
        self.check_config = yaml.safe_load(Path(check_config).open().read())
        # clear prior logged flags, because a single protocol should be run at any given time, there should be no prior logged flags
        if Flag.allFlags:
            print(f"Warning! Clearing {len(Flag.allFlags)} flags from prior Flag class loading, this message shouldn't appear in one protocol mode")
        Flag.clear_flags()

        Flag.config = self.check_config["Flagging"]
        self.sp_config = yaml.safe_load(Path(sp_config).open().read())
        self.vv_dir = vv_dir
    
        # pass config into checks as well as convert into a dictionary of check class name and check instance
        self.checks_reformat = dict()
        for check in self.checks:
            assert issubclass(check,BaseCheck) # ensure all checks are actually BaseCheck derived objects
            check_instance = check(config=self.check_config)
            self.checks_reformat[check.__name__] = check_instance
        self.checks = self.checks_reformat

    @abc.abstractmethod
    def run_function(self):
        """ The actual runtime 'script' """
        ...

    @abc.abstractproperty
    def protocolID(self):
        """ The protocolID """
        return

    @abc.abstractproperty
    def checks(self):
        """ The checks to be performed """
        return

    @abc.abstractproperty
    def description(self):
        """ The description """
        return

    def run(self, append_to_log: bool = False) -> Tuple[Path,DataFrame]:
        """ Runs the runtime script """
        print(f"Protocol ID: {self.protocolID}\nProtocol Description: {self.description}\nRunning protocol with check config '{self.check_config_f}' and search pattern config'{self.sp_config_f}'")
        self.run_function()
        comment = f"Next rows generated at {datetime.datetime.now()} by protocolID: '{self.protocolID}' with config files: '{self.check_config_f}' '{self.sp_config_f}'"
        # get flags as dataframe for returning before writing to output log (and likely purging said flags)
        flag_df = Flag.to_df()
        if append_to_log:
            out_f = Flag.dump(comment=comment, append=append_to_log, purge_flags=True)
        else:
            out_f = Flag.dump(comment=comment, purge_flags=True)
        print(f"Wrote results to {out_f}")
        return out_f, flag_df

    def describe(self) -> str:
        """ Prints all the V&V checks that will be performed """
        description = f"Protocol:\n\tID: {self.protocolID}\n\tDescription: {self.description}\nConfiguration: \n\tchecks: {self.check_config_f}\n\tsearch_patterns: {self.sp_config_f}\n Protocol runs the following: \n {inspect.getsource(self.run_function)}"
        return description 
        

    def document(self):
        """ Write protocol to a human readable file.  This combines general checks and specific configuration into one report """
        out_f = Path(f"{self.protocolID}_Conf-{Path(self.check_config_f).name.replace('.yml','')}_Documentation.txt")
        print(f"Generating protocol document to file: {out_f}")
        with open(out_f, "w") as f:
            f.write(f"ProtocolID: {self.protocolID}\n")
            for i, (check_name, check) in enumerate(self.checks.items()):
                f.write(f"{i}. {check.checkID} {check.description}\n")
        return out_f
            


def _list_configs(pattern, search_paths: list = []):
    """ Returns a list of all protocols that are findable """
    found = [f for f in _PACKAGED_CONFIG_FILES.copy() if str(f).endswith(pattern)]
    for path in search_paths:
        found_yml = list(Path(path).glob(pattern))
        found.append(found_yml)
    return found


def list_check_configs(search_paths: list = []):
    """ Returns a list of all protocols that are findable """
    return _list_configs(pattern = "_checks.yml", search_paths=search_paths)

def list_sp_configs(search_paths: list = []):
    """ Returns a list of all protocols that are findable """
    return _list_configs(pattern = "_sp.yml", search_paths=search_paths)

def get_configs(search_paths: list = []) -> dict:
    check_found = list_check_configs(search_paths = search_paths)
    sp_found = list_sp_configs(search_paths = search_paths)
    # reformat as nested dict
    result = {"checks":{}, "sp":{}}
    for f in check_found:
        result['checks'][f.name] = f
    for f in sp_found:
        result['sp'][f.name] = f
    return result
