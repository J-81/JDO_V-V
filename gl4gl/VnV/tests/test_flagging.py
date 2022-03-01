from gl4gl.VnV.tests import flagging_demo


def test_flagging(caplog):
    """ This is the boiler plate code for all VnV modules """
    with caplog.at_level(10):
        flagging_demo.run()

    flags = [r for r in caplog.records if r.name.startswith("Flagging.")]

    assert len(flags) == 5


def test_bad_flagging(caplog):
    """ This is the boiler plate code for all VnV modules """
    import pytest

    # this should error out due to missing flag info
    with pytest.raises(ValueError):
        flagging_demo.run_with_error()


def test_checks_reporting(caplog):
    """ This is the boiler plate code for all VnV modules """
    from gl4gl.VnV.custom_logging import NO_CHECK_DESC

    with caplog.at_level(10):
        flag = flagging_demo.run()

    # 3 uncharacterized flags then 2 characterized ones
    assert flag.checks[NO_CHECK_DESC] == 3
    assert flag.checks[("9999-0001", "This ran during a test demo")] == 2
