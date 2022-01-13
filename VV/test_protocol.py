""" A test protocol """
from VV.protocol import BaseProtocol
from VV.test_checks import TCheck1, TCheck2, TCheck3
from VV.file_search import FileSearcher


# Data extraction/wrangling
# For this template dummy data object
DATA = {
        "sample1":
            {
                'max':10, 
                'min':1, 
                'intensity':2
            },
        "sample2":
            {
                'max':1,
                'min':0.5,
                'intensity':3
            },
        "sample3":
            {
                'max':2,
                'min':0.5,
                'intensity':'error'
            },
        "sample4":
            {
                'max':2.5,
                'min':0,
                'intensity':3
            }
        }



# Define the protocol to V&V the data extracted above.
class TProtocol(BaseProtocol):
    protocolID = "TestProtocol"
    description = "This protocol is used solely for testing this package and serves a template for writing production protocols"

    # OPTIONAL METHOD
    # METHOD IS USED FOR AUTOMATED DATA EXTRACTION AND LEVERAGES FILE SEARCHING
    # EXAMPLE OF PROTOCOLS THAT WOULDN'T USE THIS INCLUDE ONES THAT ARE SIMPLE ENOUGH TO INCLUDE IN RUN; HOEVER, FOR ANY LENGTHY PROTOCOL A SEPARATE 
    # EXTRACT_DATA FUNCTION PROVIDES A CLEAR SEPARATION BETWEEN DATA EXTRACTION WHICH MUST RUN WITHOUT EXCEPTION AS OPPOSED TO FLAGGING/CHECKS WHICH
    # CAN INCLUDE UNEXPECTED EDGE CASES BUT WILL SELF DOCUMENT ANY UNEXPECTED EXCEPTIONS ALONG WITH THE FULLER REPORT
    def extract_data(self):
        """ Includes the data extraction required, file searching is performed and data extraction from files """
        print(f"Searching for files in {self.vv_dir}")
        self.fs = FileSearcher(sp_config = self.sp_config_f, analysis_dir = self.vv_dir)
        self.fs.get_files()
        self.files = self.fs.files
        print(f"Found files:\n{self.files}")

        self.data = DATA # replace with actually parsing the files for data

    def run_function(self):
        # Init all checks, MUST include check_config as below
        tc1 = TCheck1(config=self.check_config)
        tc2 = TCheck2(config=self.check_config)
        tc3 = TCheck3(config=self.check_config)

        # Perform checks with appropriate arguments for the perform function (defined within the check)
        for sample, metrics in DATA.items():
            tc1.perform(sample=sample, max=metrics['max'])
            tc2.perform(sample=sample)
            tc3.perform(sample=sample)



class TProtocol2(BaseProtocol):
    protocolID = "TestProtocol2"
    description = "This protocol is used solely for testing this package and serves a template for writing production protocols"

    # OPTIONAL METHOD
    # METHOD IS USED FOR AUTOMATED DATA EXTRACTION AND LEVERAGES FILE SEARCHING
    # EXAMPLE OF PROTOCOLS THAT WOULDN'T USE THIS INCLUDE ONES THAT ARE SIMPLE ENOUGH TO INCLUDE IN RUN; HOEVER, FOR ANY LENGTHY PROTOCOL A SEPARATE 
    # EXTRACT_DATA FUNCTION PROVIDES A CLEAR SEPARATION BETWEEN DATA EXTRACTION WHICH MUST RUN WITHOUT EXCEPTION AS OPPOSED TO FLAGGING/CHECKS WHICH
    # CAN INCLUDE UNEXPECTED EDGE CASES BUT WILL SELF DOCUMENT ANY UNEXPECTED EXCEPTIONS ALONG WITH THE FULLER REPORT
    def extract_data(self):
        """ Includes the data extraction required, file searching is performed and data extraction from files """
        print(f"Searching for files in {self.vv_dir}")
        self.fs = FileSearcher(sp_config = self.sp_config_f, analysis_dir = self.vv_dir)
        self.fs.get_files()
        self.files = self.fs.files
        print(f"Found files:\n{self.files}")

        self.data = DATA # replace with actually parsing the files for data

    def run_function(self):
        # Init all checks, MUST include check_config as below
        tc3 = TCheck3(config=self.check_config)

        # Perform checks with appropriate arguments for the perform function (defined within the check)
        for sample, metrics in DATA.items():
            tc3.perform(sample=sample)
