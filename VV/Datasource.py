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
            except ValidationError as e:
                print(f"Datasource failed validation: {e}")
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
