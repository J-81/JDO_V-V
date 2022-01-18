import re
from pathlib import Path
from typing import List

from VV.protocol import BaseProtocol
from VV.checks import BaseCheck
from VV.file_search import FileSearcher

RE_SUFFIX_RAW_FASTQ = r"_R._raw\.fastq\.gz"

class R_0001(BaseCheck):
    checkID = "R_0001"
    description = "Check that raw reads exist for the all samples. In paired end experiement, this includes checking for both forward and reverse read files"

    def perform_function(self, sample: str, raw_fastqs: List[Path]):
        """
        sample: the name to query against all raw fastq filenames
        raw_fastqs: a list of filepaths to query
        """
        expected_num_files = self.config['expected_number_read_files']

        samplewise_re_pattern = f"{sample}{RE_SUFFIX_RAW_FASTQ}"
        matching_paths = [hit for hit in raw_fastqs if re.match(samplewise_re_pattern, hit.name)]
        if len(matching_paths) != expected_num_files:
            msg = f"Incorrect number of raw read files found: Found {len(matching_paths)} Expected {expected_num_files}"
            code = self.config["bad_num_fcode"]
        else:
            msg = "Found correct number of raw read files"
            code = self.config["match_num_fcode"]
        return self.flag(code = code, msg = msg, entity = sample, data = {"filepaths": matching_paths, 'querypaths': raw_fastqs, 're_query' : samplewise_re_pattern} )

# Define the protocol to V&V the data extracted above.
class RNASeq_Concensus_Pipeline_Protocol(BaseProtocol):
    protocolID = "RNASeq_RCP_Protocol"
    description = "This V&V protocol verifies all expected output files from the RNASeq pipeline are generated.  It validates the contents of such files meets expectations based on the experiment science and flags data that is does not meet expectation."
    checks = [R_0001]

    # OPTIONAL METHOD
    # METHOD IS USED FOR AUTOMATED DATA EXTRACTION AND LEVERAGES FILE SEARCHING
    # EXAMPLE OF PROTOCOLS THAT WOULDN'T USE THIS INCLUDE ONES THAT ARE SIMPLE ENOUGH TO INCLUDE IN RUN; HOEVER, FOR ANY LENGTHY PROTOCOL A SEPARATE 
    # EXTRACT_DATA FUNCTION PROVIDES A CLEAR SEPARATION BETWEEN DATA EXTRACTION WHICH MUST RUN WITHOUT EXCEPTION AS OPPOSED TO FLAGGING/CHECKS WHICH
    # CAN INCLUDE UNEXPECTED EDGE CASES BUT WILL SELF DOCUMENT ANY UNEXPECTED EXCEPTIONS ALONG WITH THE FULLER REPORT
    def extract_data(self, samples):
        """ Includes the data extraction required, file searching is performed and data extraction from files """
        print(f"Searching for files in {self.vv_dir}")
        self.fs = FileSearcher(sp_config = self.sp_config_f, analysis_dir = self.vv_dir)
        self.fs.get_files()
        self.files = self.fs.files
        self.simple_files = self.fs.simple_files
        print(f"Found files:\n{self.files}")

        self.data = {'samples':samples}

    def run_function(self):
        # Perform checks with appropriate arguments for the perform function (defined within the check)
        print(self.checks)
        for sample in self.data['samples']:
            self.checks['R_0001'].perform(sample=sample, raw_fastqs=self.simple_files['raw_fastq'])


def start_protocol(vv_dir: str, samples: List[str]) -> str:
    """ runs this protocol and returns the output file
    vv_dir: the directory to run the search patterns and V&V on
    samples: the samples to V&V
    """
    from VV.protocol import get_configs 
    configs = get_configs()
    proto = RNASeq_Concensus_Pipeline_Protocol(
                check_config = configs['checks']['RNASeq_Concensus_Pipeline_checks.yml'], 
                sp_config = configs['sp']['RNASeq_sp.yml'],
                vv_dir = vv_dir)

    proto.extract_data(samples = samples)

    return proto.run()

if __name__ == "__main__":
    start_protocol()
