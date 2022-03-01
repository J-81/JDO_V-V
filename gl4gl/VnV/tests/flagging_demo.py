def run():
    #################################################
    # THIS IS THE BOILER PLATE
    #################################################
    import logging

    print(logging.raiseExceptions)
    logging.raiseExceptions = False  # should be set for development

    log = logging.getLogger(__name__)  # note: this can be used to log as normal

    from gl4gl.VnV.custom_logging import Flag

    flag = Flag(log, {"module_info": "test_module"})
    #################################################
    # END OF THE BOILER PLATE
    #################################################

    # now log some info NOT through flagging
    log.debug("Super low level info, not a flag at all")
    log.info("Some info, not a flag")
    log.error("Some error, again not a flag though")

    # now push some flags
    filenames = {"Some/Path/1"}
    flag.info(
        "This looks good",
        extra={"entity": ("DS1", "Rep2", ""), "flag_code": 30, "filenames": filenames},
    )
    flag.info(
        "This looks bad",
        extra={"entity": ("DS1", "Rep2", ""), "flag_code": 40, "filenames": filenames},
    )
    flag.info(
        "This is really bad",
        extra={"entity": ("DS1", "Rep2", ""), "flag_code": 50, "filenames": filenames},
    )

    # set check description
    flag.check = ('9999-0001','This ran during a test demo')
    flag.info(
        "This means the processing should stop ASAP",
        extra={"entity": ("DS1", "Rep2", ""), "flag_code": 80, "filenames": filenames},
    )

    # now with flag attribute testing
    flag.entity = ("A", "B", "C")
    flag.filenames = {"Some/Path/1", "Some/path/2"}

    # only need to call with flag_code
    flag.info("This has attributes", extra={"flag_code": 30})

    # this should reset entity and filenames
    flag.reset()

    # now flag this should raise an error
    return flag


def run_with_error():
    #################################################
    # THIS IS THE BOILER PLATE
    #################################################
    import logging

    print(logging.raiseExceptions)
    logging.raiseExceptions = False  # should be set for development

    log = logging.getLogger(__name__)  # note: this can be used to log as normal

    from gl4gl.VnV.custom_logging import Flag

    flag = Flag(log, {"module_info": "test_module"})
    #################################################
    # END OF THE BOILER PLATE
    #################################################
    # now with flag attribute testing
    flag.entity = ("A", "B", "C")
    flag.filenames = {"Some/Path/1", "Some/path/2"}

    # only need to call with flag_code
    flag.info("This has attributes", extra={"flag_code": 30})

    # this should reset entity and filenames
    flag.reset()

    flag.info("This should fail due to missing requirements", extra={"flag_code": 30})





from pathlib import Path
import logging

from gl4gl.VnV.custom_logging import Flag, flag_exceptions

# load module specific logger
log = logging.getLogger(__name__)
# load in module specific data with an adaptor that also handles kwargs and default
flag = Flag(log, {"module_info": "TestDemo"})

@flag_exceptions(flag)
def check_file_exists(input_f: Path) -> bool:
    """Returns passing if the file '{input_f.name}' exists. """
    return input_f.exists()