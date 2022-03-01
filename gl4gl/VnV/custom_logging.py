# import logging

from functools import wraps
from logging import Logger, config
from collections import Counter

import logging
from typing import Callable

from numpy import iterable

NO_CHECK_DESC = ("9999-0000", "No check description")

log = logging.getLogger(__name__)

"""
class FileHandlerWithHeader(logging.FileHandler):

    # Pass the file name and header string to the constructor.
    def __init__(self, filename, header, mode="a", encoding=None, delay=0):
        # Store the header information.
        self.header = "ENTITY\tMODULE\tFLAGCODE\tMESSAGE\tLOGLEVEL\tFUNCTION"

        # Determine if the file pre-exists
        self.file_pre_exists = os.path.exists(filename)

        # Call the parent __init__
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)

        # Write the header if delay is False and a file stream was created.
        if not delay and self.stream is not None:
            self.stream.write("%s\n" % header)

    def emit(self, record):
        # Create the file stream if not already created.
        if self.stream is None:
            self.stream = self._open()

            # If the file pre_exists, it should already have a header.
            # Else write the header to the file so that it is the first line.
            if not self.file_pre_exists:
                self.stream.write("%s\n" % self.header)

        # Call the parent class emit function.
        logging.FileHandler.emit(self, record)

"""
log_config = {
    "version": 1,
    "loggers": {
        "": {"handlers": ["console"], "level": "DEBUG",},
        "gl4gl.VnV": {"handlers": ["console", "fullLog",], "level": "DEBUG",},
        "Flagging": {
            "handlers": ["flagsDebug", "flagsIssues", "flagsInfo",],
            "level": "DEBUG",
        },
    },
    "handlers": {
        "console": {
            "formatter": "std_out",
            "class": "logging.StreamHandler",
            "level": "INFO",
        },
        "fullLog": {
            "formatter": "std_out",
            "class": "logging.FileHandler",
            "level": "INFO",
            "filename": "VnV_user.log",
        },
        "flagsDebug": {
            "formatter": "flag_tab_internal",
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "filename": "all_flags_user_DEBUG.tsv",
        },
        "flagsIssues": {
            "formatter": "flag_tab_publish",
            "class": "logging.FileHandler",
            "level": "WARNING",
            "filename": "issue_flags_user.tsv",
        },
        "flagsInfo": {
            "formatter": "flag_tab_publish",
            "class": "logging.FileHandler",
            "level": "INFO",
            "filename": "all_flags_user.tsv",
        },
    },
    "formatters": {
        "std_out": {
            "format": "%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(lineno)d : (Process Details : (%(process)d, %(processName)s), Thread Details : (%(thread)d, %(threadName)s))\nLog : %(message)s",
            "datefmt": "%d-%m-%Y %I:%M:%S",
        },
        "flag_out": {
            # "format": "{module} : {funcName} : {lineno} : FLAG_CODE {flag_code} : {message}",
            "format": "%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(lineno)d : Log : %(message)s ",
            # "datefmt": "%d-%m-%Y %I:%M:%S",
        },
        "flag_tab_internal": {
            # This formatter REQUIRES args as required by the final flag table output
            # these are ['flag_code':int]
            "format": "%(entity)s\t%(checkID)s\t%(checkDescription)s\t%(message)s\t%(flag_code)d\t%(filenames)s\t%(filepaths)s\t%(levelname)s\t%(module)s\t%(funcName)s:%(lineno)d",
            # "datefmt": "%d-%m-%Y %I:%M:%S",
        },
        "flag_tab_publish": {
            # This formatter REQUIRES args as required by the final flag table output
            # these are ['flag_code':int]
            "format": "%(entity)s\t%(checkID)s\t%(checkDescription)s\t%(message)s\t%(flag_code)d\t%(filenames)s",
            # "datefmt": "%d-%m-%Y %I:%M:%S",
        },
    },
}

log.debug("Loading VnV logger configuration")
config.dictConfig(log_config)


class FlagAdapter(logging.LoggerAdapter):
    # This defines expectations for the flag entity index
    EXAMPLE_ENTITY = ("Sample1", "Forward_Read", "BP_1")
    ENTITY_INDEX_LENGTH = len(EXAMPLE_ENTITY)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug("Instancing flag adaptor")
        self.__entity = None
        self.__filepaths = None
        self.__check = None
        self.__checks = list()  # this will store checks run

    def reset(self):
        log.debug("Resetting attributes: 'entity,filesnames,check' to None")
        self.__entity = None
        self.__filepaths = None
        self.__check = None

    @property
    def entity(self):
        return self.__entity

    @entity.setter
    def entity(self, value):
        assert all((len(value) == 3, isinstance(value, tuple)))
        self.__entity = value

    @property
    def filepaths(self):
        return self.__filepaths

    @filepaths.setter
    def filepaths(self, value):
        assert isinstance(value, set), "filepaths must be a set"
        self.__filepaths = value

    @property
    def check(self):
        return self.__check

    @check.setter
    def check(self, value):
        assert all((len(value) == 2, isinstance(value, tuple)))
        self.__check = value

    @property
    def checks(self):
        return Counter(self.__checks)

    @checks.setter
    def checks(self, value):
        raise ValueError("Cannot set checks directly, use 'add_check' instead")

    def add_check(self, value):
        assert all((len(value) == 2, isinstance(value, tuple)))
        self.__checks.append(value)

    def process(self, msg, kwargs):
        # values defined on adapter init (of
        # validate minimum information for flagging, throw exception if anything is missing
        # kwargs = {**self.extra, **kwargs["extra"]}
        supplied_kwargs = kwargs.get(
            "extra", {}
        )  # default to empty dict if none supplied

        # these must be supplied during flag call or set be the flag beforehand
        REQUIRED = ["flag_code", "entity", "filepaths"]
        # these should be supplied but a default is assigned if otherwise
        # a check denotes a tuple of (checkID: str, checkDescription: str)
        SOFT_REQUIRED = ["check"]
        CAN_BE_SET = ["entity", "filepaths", "check"]

        # add in current flag attributes if existing, raise errors if clashing
        for required in CAN_BE_SET:
            if all([not supplied_kwargs.get(required), getattr(self, f"{required}")]):
                supplied_kwargs[required] = getattr(self, f"{required}")
            elif all([supplied_kwargs.get(required), getattr(self, f"{required}")]):
                if (
                    supplied_kwargs["flag_code"] != 99
                ):  # the function exception code that should skip this issue and fall back on supplied
                    raise ValueError(
                        f"Found 'entity' in both the call and the flag object.  Use one OR the other"
                    )
                else:
                    # for this case, fall back on prior set flags, but print supplied
                    log.critical(
                        f"Using set attrs in flag in unhandled exception flag but these were supplied to the flag call: {supplied_kwargs[required]}"
                    )
                    supplied_kwargs[required] = getattr(self, f"{required}")

        # these are from soft required
        # use supplied but fallback to default NO_CHECK_DESC
        supplied_kwargs["check"] = supplied_kwargs.get("check", NO_CHECK_DESC)

        if missing := set(REQUIRED) - set(supplied_kwargs.keys()):
            raise ValueError(f"Missing required flagging 'extra': {missing}")

        if excess := set(supplied_kwargs.keys()) - set(REQUIRED):
            log.warning(
                f"The following were supplied, but are unused in flag message: {excess}.  Only {REQUIRED} are used."
            )

        # confirm requisite types
        assert all(
            (
                isinstance(supplied_kwargs["entity"], tuple),
                len(supplied_kwargs["entity"]) == self.ENTITY_INDEX_LENGTH,
            )
        ), f"Bad type or length, 'entity' must be a tuple of length {self.ENTITY_INDEX_LENGTH}. e.g. {self.EXAMPLE_ENTITY}. Instead got: {supplied_kwargs['entity']}"
        assert isinstance(
            supplied_kwargs["flag_code"], int
        ), f"Bad type, 'flag_code' must be an integer. Instead got: {supplied_kwargs['flag_code']}"

        # before final send to handlers, add check to tracked runtime list
        self.add_check(supplied_kwargs["check"])

        # finally, reformat if needed
        supplied_kwargs["checkID"] = supplied_kwargs["check"][0]
        supplied_kwargs["checkDescription"] = supplied_kwargs["check"][1]
        supplied_kwargs.pop("check")  # not used in final flag message
        supplied_kwargs["filenames"] = {
            path.name for path in supplied_kwargs["filepaths"]
        }

        return f"{msg}", kwargs


# TODO: Make expected set-ables work with slots to raises exceptions on typos (e.g. flag.filenams should raise an exception when trying to set)
def Flag(log: Logger, module_args: dict) -> FlagAdapter:
    """Generates a derived logger for the module for use in VnV flagging 

    :param log: The module level log, recommend creation with 'log = logging.getLogger(__name__)'
    :type log: Logger
    :param module_args: Module level information to pass onto flag adaptor. Currently uses the following keys in the flag messages: ['module_info']
    :type module_args: dict
    :return: A derived logger that is used for VnV flagging
    :rtype: Logger
    """
    flag_log = logging.getLogger(f"Flagging.{log.name}")
    adapter = FlagAdapter(flag_log, module_args)

    return adapter


def flag_exceptions(flag):
    """ Runs the function in a way that unhandled exceptions are flagged, but otherwise runs unhalted"""

    def callable(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                # generate a 99 code flag
                # save full traceback to log
                # include a uuid to link the two for developer debugging
                import uuid

                search_id = uuid.uuid4()
                flag.critical(
                    f"Function raised unhandled exception [see traceback in full log: Exception ID: <{search_id}>] with args: {args} and kwargs: {kwargs}",
                    extra={"entity": ("EXCEPTION", "", ""), "flag_code": 99},
                )
                log.exception(f"Unhandled Exception ID: {search_id}")

        return wrapper

    return callable
