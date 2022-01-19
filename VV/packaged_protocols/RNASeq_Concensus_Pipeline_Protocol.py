import re
from pathlib import Path
from typing import List
import gzip

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

class R_0002(BaseCheck):
    checkID = "R_0002"
    description = "Check a sample of the raw read headers are in the expected locations and match expected format"

    def perform_function(self, sample: str, read_file: str, raw_fastq: Path):
        """
        sample: sample
        read_file: i.e. forward or reverse read file
        raw_fastq: path to file, the file must be gz compressed
        """
        count_lines_to_check = self.config['lines_to_check']
        lines_with_issues = list()

        data = dict()
        # truncated files raise EOFError
        try:
            with gzip.open(raw_fastq, "rb") as f:
                for i, line in enumerate(f):
                    # checks if lines counted equals the limit input
                    if i+1 == count_lines_to_check:
                        break

                    line = line.decode()
                    # every fourth line should be an identifier
                    expected_identifier_line = (i % 4 == 0)
                    # check if line is actually an identifier line
                    if (expected_identifier_line and line[0] != "@"):
                        lines_with_issues.append(i+1)
                        if not data.get('first_line_with_issue'):
                            data['first_line_with_issue'] = i
                    # update every 20,000,000 reads
                    if i % 20000000 == 0:
                        print(f"\t\t-Checked {i} lines for {raw_fastq}")
                        pass
            data['percent_of_lines_checked_with_issues'] = len(lines_with_issues)/count_lines_to_check*100
            if len(lines_with_issues) != 0:
                code = self.config['issues_fcode']
                msg = f"Found issues when checking headers. (see sample of lines with issues in data['problem_lines_sample'])"
            else:
                code = self.config['no_issues_fcode']
                msg = f"No issues found for headers checked"
        except EOFError:
            code = self.config['corrupt_fcode']
            msg = "EOFError raised, this indicates files may be corrupted"
        finally:
            return self.flag(code = code, msg = msg, entity = sample, sub_entity = read_file, data = data)
        
# Define the protocol to V&V the data extracted above.
class RNASeq_Concensus_Pipeline_Protocol(BaseProtocol):
    protocolID = "RNASeq_RCP_Protocol"
    description = "This V&V protocol verifies all expected output files from the RNASeq pipeline are generated.  It validates the contents of such files meets expectations based on the experiment science and flags data that is does not meet expectation."
    checks = [R_0001,R_0002]

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
            self.checks['R_0001'].perform(sample=sample, raw_fastqs=self.simple_files['forward_raw_fastq'] + self.simple_files['reverse_raw_fastq'])

        for sample in self.data['samples']:
            # matches general file format, subsets for forward and reverse controlled by sp config
            samplewise_re_pattern = f"{sample}{RE_SUFFIX_RAW_FASTQ}"
            # check forward reads
            for matching_path in [hit for hit in self.simple_files['forward_raw_fastq'] if re.match(samplewise_re_pattern, hit.name)]:
                self.checks['R_0002'].perform(sample=sample, read_file="forward_reads", raw_fastq=matching_path) 

            # check reverse reads
            for matching_path in [hit for hit in self.simple_files['reverse_raw_fastq'] if re.match(samplewise_re_pattern, hit.name)]:
                self.checks['R_0002'].perform(sample=sample, read_file="reverse_reads", raw_fastq=matching_path) 


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
