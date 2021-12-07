import pytest

from VV.checks import BaseCheck
from VV.flagging import Flag

class TCheck(BaseCheck):
    checkID = "T_001"
    description = "Test desc."

    def perform_function(self, x, y):
        result = Flag(code = 10, msg = f"Sum: x+y = {x+y}")
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
            result = Flag(code = 10, msg = f"Sum: x+y = {x+y}")
            return result 
    # perform the prereq check 'Test_001'
    TCheck().perform(x=2,y=3)
    
    testCheck = TCheck_needs_T_00F()
    

    result = testCheck.perform(x=3,y=5)
    print(testCheck.performedLog)
    assert result.code == 101

    print(testCheck.globalPerformedLog)

def test_TCheck():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck()
    print(testCheck)

    result = testCheck.perform(1,2)
    print(testCheck.performedLog)
    assert result.code == 10

def test_TCheck_bad_return():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck()
    testCheck.perform_function = lambda x: x
    print(testCheck)

    result = testCheck.perform(1)
    print(testCheck.performedLog)
    assert result.code == 90 

def test_TCheck_exception():
    """ You should NOT be able to instantiate the base check class """
    testCheck = TCheck()
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
            result = Flag(code = 10, msg = f"Sum: x+y = {x+y}")
            return result 
    # perform the prereq check 'Test_001'
    TCheck().perform(x=2,y=3)
    
    testCheck = TCheck_needs_T_001()
    

    result = testCheck.perform(x=3,y=5)
    print(testCheck.performedLog)
    assert result.code == 10

    print(testCheck.globalPerformedLog)

