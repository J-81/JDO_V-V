""" A test protocol """
from VV.protocol import BaseProtocol
from VV.test_checks import TCheck1, TCheck2, TCheck3

class TProtocol(BaseProtocol):

    def run_function(self):
        tc1 = TCheck1(config=self.check_config)
        tc2 = TCheck2(config=self.check_config)
        tc3 = TCheck3(config=self.check_config)

        tc1.perform()
        tc2.perform()
        tc3.perform()

