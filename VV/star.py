""" VV related to the output from STAR alignment
"""
import os
import subprocess

from VV.utils import value_check_direct
from VV.flagging import Flagger

class StarAlignments():
    """ Representation of Star Alignment output results data.
    Includes parsing for:
      - <sample>_Log.final.out
      - <sample>_Aligned.sortedByCoord.out.bam
      - <sample>_Aligned.toTranscriptome.out.bam
    """
    def __init__(self,
                 samples: str,
                 dir_path: str,
                 flagger: Flagger,
                 params: dict):
        print(f"Starting VV for STAR alignment output")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("STAR")
        self.flagger = flagger
        self.params = params
        self.samples = samples
        self.dir_path = dir_path
        self.final = self._parse_log_final()
        self._validate_alignment_files()
        self._validate_additional_files()
        self._check_values()
        self._check_samples_proportions_for_dataset_flags()

    def _check_values(self):
        ################################################################
        # Checks for each sample:file_label vs all samples
        checkIDs_to_keys = {"S_0003":"total_reads_mapped-Percentage",
                            "S_0004":"mapped_to_multiple_loci-Percentage",
                            }
        for checkID, key in checkIDs_to_keys.items():
            # compile values for the key for all samples
            all_values = [sample_values[key] for sample_values in self.final.values()]

            # iterate through each sample
            # test against all values from all samples
            for sample in self.samples:
                value = self.final[sample][key]
                value_check_direct(value = value,
                                   all_values = all_values,
                                   check_params = self.params["STAR"][key],
                                   flagger = self.flagger,
                                   checkID = checkID,
                                   entity = sample,
                                   value_alias = key,
                                   middlepoint = self.params["middlepoint"],
                                   message_prefix = "Sample vs Samples")

    def __repr__(self):
        return f"Star Alignment Results: <{self.samples}>"

    def _parse_log_final(self):
        """ Parses <sample>_Log.final.out file

        Example:
                                 Started job on |	Oct 17 14:54:28
                             Started mapping on |	Oct 17 17:48:01
                                    Finished on |	Oct 17 22:04:45
       Mapping speed, Million of reads per hour |	27.49

                          Number of input reads |	117627693
                      Average input read length |	275
                                    UNIQUE READS:
                   Uniquely mapped reads number |	86205864
                        Uniquely mapped reads % |	73.29%
                          Average mapped length |	274.08
                       Number of splices: Total |	55999786
            Number of splices: Annotated (sjdb) |	55997549
                       Number of splices: GT/AG |	55176898
                       Number of splices: GC/AG |	678230
                       Number of splices: AT/AC |	57224
               Number of splices: Non-canonical |	87434
                      Mismatch rate per base, % |	0.46%
                         Deletion rate per base |	0.02%
                        Deletion average length |	2.68
                        Insertion rate per base |	0.04%
                       Insertion average length |	3.30
                             MULTI-MAPPING READS:
        Number of reads mapped to multiple loci |	15196585
             % of reads mapped to multiple loci |	12.92%
        Number of reads mapped to too many loci |	96603
             % of reads mapped to too many loci |	0.08%
                                  UNMAPPED READS:
  Number of reads unmapped: too many mismatches |	0
       % of reads unmapped: too many mismatches |	0.00%
            Number of reads unmapped: too short |	15652272
                 % of reads unmapped: too short |	13.31%
                Number of reads unmapped: other |	476369
                     % of reads unmapped: other |	0.40%
                                  CHIMERIC READS:
                       Number of chimeric reads |	0
                            % of chimeric reads |	0.00%
        """
        final_data = dict()
        for sample in self.samples:
            # create entry for sample
            final_data[sample] = dict()
            file_path = os.path.join(self.dir_path,sample,f"{sample}_Log.final.out")
            checkID = "S_0001"
            if not os.path.isfile(file_path):
                message = f"Could not find {file_path}"
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 90,
                                  checkID = checkID)
                continue
            else:
                message = f"Found {file_path}"
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 30,
                                  checkID = checkID)
            with open(file_path, "r") as f:
                for line in f.readlines():
                    # Data lines contain '|''
                    if "|" in line:
                        metric, data = line.split("|")
                        # strip whitespace
                        metric = metric.strip()

                        # if metric is in this list, skip
                        if metric in ["Started job on","Started mapping on","Finished on"]:
                            continue

                        # clean data, convert to float
                        data = float(data.replace("%",""))

                        # add to dictionary
                        final_data[sample][metric] = data
            # add additional data keys from combining base keys
            final_data[sample]["total_reads_mapped-Percentage"] = sum((final_data[sample]["Uniquely mapped reads %"],
                                                     final_data[sample]["% of reads mapped to multiple loci"])
                                                     )
            final_data[sample]["mapped_to_multiple_loci-Percentage"] = sum((final_data[sample]["% of reads mapped to multiple loci"],
                                                           final_data[sample]["% of reads mapped to too many loci"])
                                                           )
        return final_data

    def _validate_additional_files(self):
        """ Checks for existence of the following files:
        - <sample>_Log.out
            - First line condition:
                - Starts with "STAR version="
            - Last line conditin:
                - ALL DONE!
        - <sample>_SJ.out.tab
            - Condition for every 100 lines
                - 9 tokens per line upon split (correct number of columns)
        - <sample>_Log.progress.out
            First line condition:
                - is the following:
                - Time    Speed        Read     Read   Mapped   Mapped   Mapped   Mapped Unmapped Unmapped Unmapped Unmapped
            - Last line condition:
                - ALL DONE!
        """
        for sample in self.samples:
            # Log.out check
            log_out_file = os.path.join(self.dir_path,
                                    sample,
                                    f"{sample}_Log.out")
            expected = "STAR version="

            with open(log_out_file, "r") as f:
                lines = f.readlines()
            error = None
            if not lines[0].strip().startswith(expected):
                error = (f"First line does not "
                         f"start with {expected}")

            expected = "ALL DONE!"
            if lines[-1].strip() != expected:
                error = (f"Last line does not "
                         f"equal {expected}")
            # flag if errors found
            checkID = "S_0002"
            if error:
                message = f"{log_out_file} has issue: {error}"
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 90,
                                  checkID = checkID)
                continue
            else:
                message = f"{log_out_file}, no issues found"
                self.flagger.flag(entity = sample,
                                  message = message,
                                  severity = 30,
                                  checkID = checkID)


             # SJ.out.tab check
            sj_out_file = os.path.join(self.dir_path,
                                    sample,
                                    f"{sample}_SJ.out.tab")

            with open(sj_out_file, "r") as f:
                for i, line in enumerate(f.readlines()):
                    if i % 100 == 0:
                        tokens = line.split()
                        if len(tokens)  != 9:
                            print(f"FAIL: {sj_out_file} line {i} does not look correct: {line}")

            # _Log.progress.out check
            log_progress_out_file = os.path.join(self.dir_path,
                                    sample,
                                    f"{sample}_Log.progress.out")
            expected = "Time    Speed        Read     Read   Mapped   Mapped   Mapped   Mapped Unmapped Unmapped Unmapped Unmapped"

            with open(log_progress_out_file, "r") as f:
                lines = f.readlines()
            error = None
            if not lines[0].strip().startswith(expected):
                error = (f"First line does not "
                         f"start with {expected}")

            expected = "ALL DONE!"
            if lines[-1].strip() != expected:
                error = (f"Last line does not "
                         f"equal {expected}")
            if error:
                print(f"FAIL: {log_progress_out_file} has issue: {error}")

    def _validate_alignment_files(self):
        """ Checks for existence of expected alignment files.

        Also checks using samtools quickcheck which should catch truncations and
            malformed header information. Source: http://www.htslib.org/doc/samtools-quickcheck.html
        """
        checkID = "S_0005"
        for sample in self.samples:
            error_message = ""
            coord_file = os.path.join(self.dir_path,
                                      sample,
                                      f"{sample}_Aligned.sortedByCoord.out.bam")
            if not os.path.isfile(coord_file):
                error_message += (f"*_Aligned.sortedByCoord.out.bam file missing")

            # check with coord file with samtools
            process = subprocess.Popen(['samtools', 'quickcheck', coord_file],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                error_message += (f"FAIL: samtools quick checkout output for on {coord_file}: {stdout}")

            # check transcriptome alignment file
            transcript_file = os.path.join(self.dir_path,
                                      sample,
                                      f"{sample}_Aligned.toTranscriptome.out.bam")
            if not os.path.isfile(transcript_file):
                error_message += (f"*_Aligned.toTranscriptome.out.bam file missing")

                continue
            # check with coord file with samtools
            process = subprocess.Popen(['samtools', 'quickcheck', transcript_file],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                error_message += (f"FAIL: samtools quick checkout output for on {transcript_file}: {stdout}")

            if error_message:
                self.flagger.flag(entity = sample,
                                  message = error_message,
                                  severity = 90,
                                  checkID = checkID
                                  )
            else:
                self.flagger.flag(entity = sample,
                                  message = "Both bam files exist and raise not issues with samtools quickcheck",
                                  severity=30,
                                  checkID = checkID
                                  )

    def _check_samples_proportions_for_dataset_flags(self):
        ### Check if any sample proportion related flags should be raised
        PROTOFLAG_MAP = {
            60 : [60],
            50 : [50, 60]
        }
        checkID_with_samples_proportion_threshold = {"S_0003":"total_reads_mapped-Percentage",
                                                     "S_0004":"mapped_to_multiple_loci-Percentage",
                                    }
        for checkID, params_key in checkID_with_samples_proportion_threshold.items():
            self.flagger.check_sample_proportions(checkID,
                                                  self.params["STAR"][params_key],
                                                  PROTOFLAG_MAP)
