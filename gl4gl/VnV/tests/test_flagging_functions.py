import logging
from gl4gl import VnV

LOGGER_NAME = "Flagging.gl4gl.VnV.tests.flagging_demo"


def test_decorated_func_with_flagged_pass(tmp_path, caplog):
    existing = tmp_path / "tmp.txt"
    existing.write_text("Test")
    from gl4gl.VnV.tests.flagging_demo import flag  # get module level flag object

    EXAMPLE_ENTITY = ("TestSample1", "Forward_Reads", "")

    flag.entity = EXAMPLE_ENTITY
    flag.filenames = {"Some/Path/1"}
    with caplog.at_level(10, logger=LOGGER_NAME):
        if VnV.tests.flagging_demo.check_file_exists(input_f=existing):
            flag.info("File exists", extra={"flag_code": 30})
        else:
            flag.info("File D.N.E.", extra={"flag_code": 50})

    flags = [r for r in caplog.records if r.name.startswith("Flagging.")]

    assert len(flags) == 1

    expected_passing_flag = flags[0]

    assert expected_passing_flag.flag_code == 30
    assert expected_passing_flag.entity == EXAMPLE_ENTITY
    assert expected_passing_flag.name == LOGGER_NAME


def test_decorated_func_with_flagged_fail(tmp_path, caplog):
    existing = tmp_path / "tmp.txt"
    # existing.write_text("Test") # HENCE THE FILE D.N.E.
    from gl4gl.VnV.tests.flagging_demo import flag  # get module level flag object

    EXAMPLE_ENTITY = ("TestSample1", "Forward_Reads", "")

    flag.entity = EXAMPLE_ENTITY
    flag.filenames = {"Some/Path/1"}
    with caplog.at_level(10, logger=LOGGER_NAME):
        if VnV.tests.flagging_demo.check_file_exists(input_f=existing):
            flag.info("File exists", extra={"flag_code": 30})
        else:
            flag.info("File D.N.E.", extra={"flag_code": 50})

    flags = [r for r in caplog.records if r.name.startswith("Flagging.")]

    assert len(flags) == 1

    expected_failing_flag = flags[0]

    assert expected_failing_flag.flag_code == 50
    assert expected_failing_flag.entity == EXAMPLE_ENTITY
    assert expected_failing_flag.message == "File D.N.E."
    assert expected_failing_flag.name == LOGGER_NAME


def test_decorated_func_raises_unhandled_exception(tmp_path, caplog):
    existing = tmp_path / "tmp.txt"
    # existing.write_text("Test")
    from gl4gl.VnV.fastqc import flag  # get module level flag object

    EXAMPLE_ENTITY = ("TestSample1", "Forward_Reads", "")

    flag.entity = EXAMPLE_ENTITY
    flag.filenames = {"Some/Path/1"}
    with caplog.at_level(10, logger=LOGGER_NAME):
        VnV.tests.flagging_demo.check_file_exists(
            input_f=str(existing)
        )  # turn into a string to force an error

    flags = [r for r in caplog.records if r.name.startswith("Flagging.")]

    assert len(flags) == 1

    expected_failing_flag = flags[0]

    assert expected_failing_flag.flag_code == 99
    assert expected_failing_flag.entity == EXAMPLE_ENTITY
    assert expected_failing_flag.message.startswith(
        "Function raised unhandled exception [see traceback in full log: Exception ID: <"
    )  # the exact message depends on the tempdir
    assert expected_failing_flag.name == LOGGER_NAME
