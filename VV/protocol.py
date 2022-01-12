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

import yaml

from VV.flagging import Flag

_PACKAGED_CONFIG_FILES = list()
for resource in importlib.resources.contents("VV.config"):
    with importlib.resources.path("VV.config",resource) as f:
        if re.match(".*_(sp|checks).yml", str(f)):
            _PACKAGED_CONFIG_FILES.append(f)

class BaseProtocol(abc.ABC):

    def __init__(self, check_config, sp_config):
        # check if yaml files exist first
        assert Path(check_config).is_file(), "Check Config file supplied doesn't exist!"
        assert Path(sp_config).is_file(), "Check Config file supplied doesn't exist!"
        self.check_config_f = str(check_config)
        self.sp_config_f = str(sp_config)
        self.check_config = yaml.safe_load(Path(check_config).open().read())
        self.sp_config = yaml.safe_load(Path(sp_config).open().read())

    @abc.abstractmethod
    def run_function(self):
        """ The actual runtime 'script' """
        ...

    @abc.abstractproperty
    def protocolID(self):
        """ The protocolID """
        return

    @abc.abstractproperty
    def description(self):
        """ The description """
        return

    def run(self):
        """ Runs the runtime script """
        print(f"Protocol ID: {self.protocolID}\nProtocol Description: {self.description}\nRunning protocol with check config '{self.check_config_f}' and search pattern config'{self.sp_config_f}'")
        self.run_function() 

    def describe(self) -> str:
        """ Prints all the V&V checks that will be performed """
        description = f"Protocol:\n\tID: {self.protocolID}\n\tDescription: {self.description}\nConfiguration: \n\tchecks: {self.check_config_f}\n\tsearch_patterns: {self.sp_config_f}\n Protocol runs the following: \n {inspect.getsource(self.run_function)}"
        return description 
        

    def document(self):
        """ Write protocol to a human readable file.  This combines general checks and specific configuration into one report """
        print("Generating protocol document to file: ")


def _list_configs(pattern, search_paths: list = []):
    """ Returns a list of all protocols that are findable """
    print(_PACKAGED_CONFIG_FILES)
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
