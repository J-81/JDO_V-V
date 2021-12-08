"""
Defines base class for check class
"""
import abc
import importlib.resources
import traceback

import yaml

from VV.flagging import Flag

with importlib.resources.path("VV.config", "Test_defaults.yaml") as f:
    config_file = f

class BaseCheck(abc.ABC):
    """ A check performed as part of Validation and Verification task """
    globalPerformedLog = list()
    # load all config
    with open(config_file, 'r') as f:
        globalConfig = yaml.safe_load(f)

    def __init__(self):
        self._performedLog = list()
        self._dependencies = set()
        self.config = self.globalConfig.get(self.checkID, None)
        if self.config:
            print(f"Loaded configuration for {self.checkID} from {config_file}")
            # override class-defined description with one in config if present
            if self.config.get('description'):
                print(f"Found description in config, overriding if the one defined in the class")
                self.description = self.config.get('description')
        else:
            print(f"No configuration for {self.checkID} found in {config_file}")


    @abc.abstractproperty
    def checkID(self):
        """ The checkID """
        return

    @abc.abstractproperty
    def description(self):
        """ The description """
        return

    @property
    def dependencies(self):
        """ A set of other checks required to perform this one """
        return self._dependencies

    @dependencies.setter
    def dependencies(self, dependencies):
        """ A set of other checks required to perform this one """
        self._dependencies = dependencies

    @property
    def performedLog(self):
        """ A log of arguments supplied to the perform function """
        return self._performedLog

    @performedLog.getter
    def performedLog(self):
        return self._performedLog

    def __repr__(self):
        return f"CheckID: {self.checkID}.\n{self.description}"

    def _missing_dependencies(self):
        """ Checks for any unpeformed dependencies and returns them """
        performed = {p["checkID"] for p in self.globalPerformedLog}
        print(self.dependencies)
        print(performed)
        return self.dependencies.difference(performed)

    def flag(self, **kwargs) -> Flag:
        """ A wrapper that automatically adds the check to the flag instance """
        kwargs["check"] = self
        print(kwargs)
        return Flag(**kwargs)


    def perform(self, *args, **kwargs) -> Flag:
        """ A function that returns a flag based on an assessment """
        print(f"Peforming check: {self.checkID} with args: {args}, kwargs: {kwargs}")

        # return a flag for missing dependencies if perform is attempted without all dependencies performed prior
        if missing_deps := self._missing_dependencies():
            # note: return result here, since the perform_function is prevented, not performed and we don't want to add to globalPerformedLog
            result = self.flag(code = 101, msg = f"Missing dependencies: {missing_deps}")
            self._performedLog.append({'args':args,'kwargs':kwargs,'result':result})
            return result

        try:
            result = self.perform_function(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            # make the result the exception and wrap in a failing Flag
            result = self.flag(code = 91, msg = f"Bad peform_function. Function raised an exception: {e}")

        # if result is not a Flag object, create one to wrap the result and an error code
        if not isinstance(result, Flag):
            result = self.flag(code = 90, msg = f"Bad perform_function. Returned: {result} is not a Flag")

        self._performedLog.append({'args':args,'kwargs':kwargs,'result':result})
        self.globalPerformedLog.append({"checkID":self.checkID, "performLog":{'args':args,'kwargs':kwargs,'result':result}})
        return result


    @abc.abstractmethod
    def perform_function(self) -> Flag:
        ...



