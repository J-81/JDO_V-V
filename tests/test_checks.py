import pytest
import yaml

import VV
from VV.checks import BaseCheck
from VV.flagging import Flag
from VV.protocol import list_check_configs

check_config_f = list_check_configs()[0]
with open(check_config_f, "r") as f:
    check_config = yaml.safe_load(f)

class TCheck(BaseCheck):
    checkID = "T_001"

    def perform_function(self, x, y):
        """ if sum is greater than 100, return a yellow flag """
        _sum = x+y
        if not _sum > 100:
            result = self.flag(code = 10, msg = f"Sum: x+y = {x+y}")
        else:
            result = self.flag(code = 50, msg = f"Sum: x+y = {x+y}")
        return result 

def test_abc_BaseCheck():
    """ You should NOT be able to instantiate the base check class """
    with pytest.raises(TypeError):
        bad_obj = BaseCheck()

def test_TCheck_missing_dep():
    """ You should NOT be able to instantiate the base check class """
    class TCheck_needs_T_00F(BaseCheck):
        checkID = "T_002"
        description = "Test that depends on 'T_00F'"
        dependencies = {'T_00F'}

        def perform_function(self, x, y):
            result = self.flag(code = 10, msg = f"Sum: x+y = {x+y}")
            return result 
    # perform the prereq check 'Test_001'
    TCheck(config = check_config).perform(x=2,y=3)
    
    testCheck = TCheck_needs_T_00F(config = check_config)
    

    result = testCheck.perform(x=3,y=5)
    print(testCheck.performedLog)
    assert result.code == 101

    print(testCheck.globalPerformedLog)

def test_TCheck():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck(config = check_config)
    print(testCheck)

    result = testCheck.perform(1,2)
    print(testCheck.performedLog)
    assert result.code == 10

def test_TCheck_bad_return():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck(config = check_config)
    testCheck.perform_function = lambda x: x
    print(testCheck)

    result = testCheck.perform(1)
    print(testCheck.performedLog)
    assert result.code == 90 

def test_TCheck_exception():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck(config = check_config)
    testCheck.perform_function = lambda x: 1/0
    print(testCheck)

    result = testCheck.perform(1)
    print(testCheck.performedLog)
    assert result.code == 91 

    print(testCheck.globalPerformedLog)

def test_TCheck_has_dep():
    """ You should NOT be able to instantiate the base check class """
    class TCheck_needs_T_001(BaseCheck):
        checkID = "T_002"
        description = "Test that depends on 'T_001'"
        dependencies = {'T_001'}

        def perform_function(self, x, y):
            result = self.flag(code = 10, msg = f"Sum: x+y = {x+y}")
            return result 
    # perform the prereq check 'Test_001'
    TCheck(config = check_config).perform(x=2,y=3)
    
    testCheck = TCheck_needs_T_001(config = check_config)
    

    result = testCheck.perform(x=3,y=5)
    print(testCheck.performedLog)
    assert result.code == 10

    print(testCheck.globalPerformedLog)

def test_TCheck_flags():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck(config = check_config)
    print(testCheck)

    result = testCheck.perform(1,2)
    print(testCheck.performedLog)
    assert result.code == 10

    assert len(result.allFlags) == 8
    assert isinstance(result.allFlags[-1], VV.flagging.Flag)
    assert result.allFlags[0].msg == "Sum: x+y = 5"

def test_TCheck_iterative_perform():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck(config = check_config)
    print(testCheck)

    for i in range(10):
        result = testCheck.perform(i,2)
        print(testCheck.performedLog)
        assert result.code == 10

    assert len(testCheck.performedLog) == 10
    assert len(testCheck.globalPerformedLog) > 10

    testCheck.perform(100,y=100)
    assert testCheck.performedLog[-1]['args'] == (100,)
    assert testCheck.performedLog[-1]['kwargs'] == {'y':100}

class TCheck_with_config(TCheck):
    checkID = "T_000C"
    description = "Test desc." #this should be explicitly overridden by config
    step = "override_me"

    def perform_function(self, x, y):
        """ if sum is greater than 100, return a yellow flag """
        _sum = x+y
        if not float(_sum).is_integer() and not self.config["flag_non_wholenumber"]:
            result = self.flag(code = self.config["non_wholenumber_flag_code"], msg = f"Sum was not a whole number: {_sum}", data={'sum':_sum})
        elif not _sum > self.config["sum_max"]:
            result = self.flag(code = 10, msg = f"Sum: x+y = {x+y}", data={'sum':_sum})
        else:
            result = self.flag(code = self.config["sum_max_flag_code"], msg = f"Sum: x+y = {x+y}", data={'sum':_sum})

        return result 

def test_TCheck_with_config_iterative_perform():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck_with_config(config = check_config)
    print(testCheck)

    for i in range(10):
        result = testCheck.perform(i,2)
        print(testCheck.performedLog)
        assert result.code == 10

    assert len(testCheck.performedLog) == 10
    assert len(testCheck.globalPerformedLog) > 10

    testCheck.perform(100,y=100)
    assert testCheck.performedLog[-1]['args'] == (100,)
    assert testCheck.performedLog[-1]['kwargs'] == {'y':100}

    # this should trigger a 75 flag
    result = testCheck.perform(100,200)
    assert testCheck.performedLog[-1]['result'].code == 75
    assert result.code == 75


def test_TCheck_with_config_description():
    """ Check if the class defined description is overwritten by the config one """
    testCheck = TCheck_with_config(config = check_config)

    assert testCheck.description == "This is a description from the config file.\nPretty neat and readable.\n"


def test_TCheck_with_config_description():
    """ Check if the class defined description is overwritten by the config one """
    testCheck = TCheck_with_config(config = check_config)

    df = Flag.to_df()

    print(df.head())
    # check dataframe as created after all prior tests
    assert len(df) == 31 
    assert len(df.columns) == 10

    # check dataframe created with arguments
    df = Flag.to_df(data_to_column=['sum'])
    assert len(df) == 31
    assert len(df.columns) == 11
    assert df.iloc[-1]['sum'] == 300
    assert df.iloc[0]['sum'] == 'Not in flag data' 
