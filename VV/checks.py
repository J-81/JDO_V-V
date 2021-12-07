"""
Defines base class for check class
"""
import abc

from VV.flagging import Flag

class BaseCheck(abc.ABC):
    """ A check performed as part of Validation and Verification task """
    globalPerformedLog = list()

    def __init__(self):
        self._performedLog = list()
        self._dependencies = set()

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

    def perform(self, *args, **kwargs) -> Flag:
        """ A function that returns a flag based on an assessment """
        print(f"Peforming check: {self.checkID} with args: {args}, kwargs: {kwargs}")

        # return a flag for missing dependencies if perform is attempted without all dependencies performed prior
        if missing_deps := self._missing_dependencies():
            # note: return result here, since the perform_function is prevented, not performed and we don't want to add to globalPerformedLog
            result = Flag(code = 101, msg = f"Missing dependencies: {missing_deps}")
            self._performedLog.append((args, kwargs, result))
            return result

        try:
            result = self.perform_function(*args, **kwargs)
        except Exception as e:
            # make the result the exception and wrap in a failing Flag
            result = Flag(code = 91, msg = f"Bad peform_function. Function raised an exception: {e}")

        # if result is not a Flag object, create one to wrap the result and an error code
        if not isinstance(result, Flag):
            result = Flag(code = 90, msg = f"Bad perform_function. Returned: {result} is not a Flag")

        self._performedLog.append((args, kwargs, result))
        self.globalPerformedLog.append({"checkID":self.checkID, "performLog":(args, kwargs, result)})
        return result


    @abc.abstractmethod
    def perform_function(self) -> Flag:
        ...



