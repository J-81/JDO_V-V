from VV.checks import BaseCheck
from VV.flagging import Flag

class TCheck1(BaseCheck):
    checkID = "TCheck1"

    def perform_function(self, sample: str, max: float):
        if max > self.config['high_threshold']:
            code = self.config['high_threshold_flag']
            msg = f"Went above high threshold of {self.config['high_threshold']}"
        elif max < self.config['low_threshold']:
            code = self.config['low_threshold_flag']
            msg = f"Went under low threshold of {self.config['high_threshold']}"
        else:
            code = 1
            msg = "All good!"

        return self.flag(code = code, msg = msg, entity = sample)

class TCheck2(BaseCheck):
    checkID = "TCheck2"

    def perform_function(self, sample):
        return self.flag(code = 2, msg = "Greetings from TCheck2 instance", entity = sample)

class TCheck3(BaseCheck):
    checkID = "TCheck3"

    def perform_function(self, sample):
        return self.flag(code = self.config['flag_code'], msg = "Greetings from TCheck3 instance", entity = sample)
