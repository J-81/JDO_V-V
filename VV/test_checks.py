from VV.checks import BaseCheck
from VV.flagging import Flag

class TCheck1(BaseCheck):
    checkID = "TCheck1"

    def perform_function(self):
        return Flag(code = 1, msg = "Greetings from TCheck1 instance")

class TCheck2(BaseCheck):
    checkID = "TCheck2"

    def perform_function(self):
        return Flag(code = 2, msg = "Greetings from TCheck2 instance")

class TCheck3(BaseCheck):
    checkID = "TCheck3"

    def perform_function(self):
        return Flag(code = 3, msg = "Greetings from TCheck3 instance")
