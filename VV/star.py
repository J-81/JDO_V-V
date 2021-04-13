""" VV related to the output from STAR alignment
"""
import os
import subprocess
from pathlib import Path

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
                 dir_mapping: dict,
                 flagger: Flagger,
                 cutoffs: dict):
        print(f"Starting VV for STAR alignment output")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("STAR")

        self.cutoffs_subsection = "STAR"
        self.flagger = flagger
        self.cutoffs = cutoffs
        self.samples = list(dir_mapping.keys())
        # generate expected files in the main sample directory
        self.file_mapping = dict()
        for sample, directory in dir_mapping.items():
            self.file_mapping[sample] = dict()
            self.file_mapping[sample]["_Log.final.out"] = Path(directory) / f"{sample}_Log.final.out"
            self.file_mapping[sample]["_Log.out"] = Path(directory) / f"{sample}_Log.out"
            self.file_mapping[sample]["_Log.progress.out"] = Path(directory) / f"{sample}_Log.progress.out"
            self.file_mapping[sample]["_SJ.out.tab"] = Path(directory) / f"{sample}_SJ.out.tab"
            self.file_mapping[sample]["_Aligned.sortedByCoord.out.bam"] = Path(directory) / f"{sample}_Aligned.sortedByCoord.out.bam"
            self.file_mapping[sample]["_Aligned.toTranscriptome.out.bam"] = Path(directory) / f"{sample}_Aligned.toTranscriptome.out.bam"

        self.final = self._parse_log_final()
        self._validate_alignment_files()
        self._validate_additional_files()
        self._check_values()
        self._check_samples_proportions_for_dataset_flags()

    def _check_values(self):
        ################################################################
        # Checks for each sample:file_label vs all samples
        check_ids_to_keys = {"S_0003":"total_reads_mapped-Percentage",
                            "S_0004":"mapped_to_multiple_loci-Percentage",
                            }
        for check_id, key in check_ids_to_keys.items():
            # compile values for the key for all samples
            all_values = [sample_values[key] for sample_values in self.final.values()]

            # iterate through each sample
            # test against all values from all samples
            for sample in self.samples:
                value = self.final[sample][key]

                partial_check_args = dict()
                partial_check_args["check_id"] = check_id
                partial_check_args["entity"] = sample
                partial_check_args["outlier_comparison_type"] = "Across-Samples"
                file_path = self.file_mapping[sample]["_Log.final.out"]
                partial_check_args["full_path"] = Path(file_path).resolve()
                partial_check_args["filename"] = Path(file_path).name
                value_check_direct(partial_check_args = partial_check_args,
                                   check_cutoffs = self.cutoffs[self.cutoffs_subsection][key],
                                   value = value,
                                   all_values = all_values,
                                   flagger = self.flagger,
                                   value_alias = key,
                                   middlepoint = self.cutoffs[self.cutoffs_subsection]["middlepoint"],
                                  )


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
            file_path = self.file_mapping[sample]["_Log.final.out"]
            partial_check_args = dict()
            partial_check_args["check_id"] = "S_0001"
            partial_check_args["entity"] = sample
            self.flagger.flag_file_exists(check_file = file_path,
                                          partial_check_args = partial_check_args)

            # extract data from file
            with file_path.open() as f:
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
            partial_check_args = dict()
            partial_check_args["check_id"] = "S_0002"
            partial_check_args["entity"] = sample
            ####################################################################
            # Log.out.tab check
            EXPECTED_FIRSTLINE_START_SUBSTRING = "STAR version="
            EXPECTED_LASTLINE = "ALL DONE!"

            partial_check_args["debug_message"] = None # created as issues arise. Overridden if no issues
            file_map = self.file_mapping[sample]
            check_file = file_map["_Log.out"]
            partial_check_args["full_path"] = Path(check_file).resolve()
            partial_check_args["filename"] = Path(check_file).name
            self.flagger.flag_file_exists(check_file = check_file,
                                          partial_check_args = partial_check_args)

            # Check file looks corret
            partial_check_args["debug_message"] = ""
            with check_file.open() as f:
                lines = f.readlines()
            if not lines[0].strip().startswith(EXPECTED_FIRSTLINE_START_SUBSTRING):
                partial_check_args["debug_message"] += (f"First line does not "
                          f"start with {EXPECTED_FIRSTLINE_START_SUBSTRING}")
            if lines[-1].strip() != EXPECTED_LASTLINE:
                partial_check_args["debug_message"] += (f"Last line does not "
                          f"equal {EXPECTED_LASTLINE}")
            # flag if errors found
            if partial_check_args["debug_message"]:
                partial_check_args["user_message"] = f"Failed validation"
                partial_check_args["severity"] = 90
                self.flagger.flag(**partial_check_args)
                continue # check other samples
            else:
                partial_check_args["debug_message"] = f"Validated by checking start and end lines."
                partial_check_args["severity"] = 30
                self.flagger.flag(**partial_check_args)

            ####################################################################
            # SJ.out.tab check
            sj_out_file = self.file_mapping[sample]["_SJ.out.tab"]
            partial_check_args["full_path"] = Path(sj_out_file).resolve()
            partial_check_args["filename"] = Path(sj_out_file).name
            self.flagger.flag_file_exists(check_file = sj_out_file,
                                          partial_check_args = partial_check_args)
            # check file contents
            partial_check_args["debug_message"] = ""
            with sj_out_file.open() as f:
                for i, line in enumerate(f.readlines()):
                    if i % 100 == 0:
                        tokens = line.split()
                        if len(tokens)  != 9:
                            partial_check_args["debug_message"] = f"Line {i} does not look correct."
            # flag if errors found
            if partial_check_args["debug_message"]:
                partial_check_args["user_message"] = f"Failed validation"
                partial_check_args["severity"] = 90
                self.flagger.flag(**partial_check_args)
                continue # check other samples
            else:
                partial_check_args["debug_message"] = f"Validated by checking every 100th line has 9 values."
                partial_check_args["severity"] = 30
                self.flagger.flag(**partial_check_args)
            ####################################################################
            # _Log.progress.out check
            EXPECTED_HEADER = "Time    Speed        Read     Read   Mapped   Mapped   Mapped   Mapped Unmapped Unmapped Unmapped Unmapped"
            EXPECTED_LASTLINE = "ALL DONE!"


            log_progress_out_file = self.file_mapping[sample]["_Log.progress.out"]
            self.flagger.flag_file_exists(check_file = log_progress_out_file,
                                          partial_check_args = partial_check_args)
            # check file contents
            partial_check_args["debug_message"] = ""
            with log_progress_out_file.open() as f:
                lines = f.readlines()
            partial_check_args["full_path"] = Path(log_progress_out_file).resolve()
            partial_check_args["filename"] = Path(log_progress_out_file).name
            if not lines[0].strip().startswith(EXPECTED_HEADER):
                partial_check_args["debug_message"] += (f"First line does not "
                                                        f"start with {EXPECTED_HEADER}")

            if lines[-1].strip() != EXPECTED_LASTLINE:
                partial_check_args["debug_message"] += (f"Last line does not "
                                                        f"equal {EXPECTED_LASTLINE}")
            if partial_check_args["debug_message"]:
                partial_check_args["user_message"] = f"Failed validation"
                partial_check_args["severity"] = 90
                self.flagger.flag(**partial_check_args)
                continue # check other samples
            else:
                partial_check_args["debug_message"] = f"Validated by checking first and last line."
                partial_check_args["severity"] = 30
                self.flagger.flag(**partial_check_args)

    def _validate_alignment_files(self):
        """ Checks for existence of expected alignment files.

        Also checks using samtools quickcheck which should catch truncations and
            malformed header information. Source: http://www.htslib.org/doc/samtools-quickcheck.html
        """
        for sample in self.samples:
            samtools_flag = False
            partial_check_args = dict()
            partial_check_args["check_id"] = "S_0005"
            partial_check_args["entity"] = sample
            partial_check_args["debug_message"] = None # created as issues arise. Overridden if no issues
            file_map = self.file_mapping[sample]
            coord_file = file_map["_Aligned.sortedByCoord.out.bam"]
            partial_check_args["full_path"] = Path(coord_file).resolve()
            partial_check_args["filename"] = Path(coord_file).name
            self.flagger.flag_file_exists(check_file = coord_file,
                                          partial_check_args = partial_check_args)

            # check with coord file with samtools
            process = subprocess.Popen(['samtools', 'quickcheck', coord_file],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                partial_check_args["debug_message"] += (f"samtools quickcheck {coord_file}: {stdout}")
                samtools_flag = True

            # check transcriptome alignment file
            transcript_file = file_map["_Aligned.toTranscriptome.out.bam"]
            self.flagger.flag_file_exists(check_file = transcript_file,
                                          partial_check_args = partial_check_args)

            # check with coord file with samtools
            process = subprocess.Popen(['samtools', 'quickcheck', transcript_file],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                partial_check_args["debug_message"] += (f"samtools quickcheck {transcript_file}: {stdout}")
                samtools_flag = True

            if samtools_flag:
                partial_check_args["severity"] = 90
                self.flagger.flag(**partial_check_args)
            else:
                partial_check_args["debug_message"] = "BAM files look fine as per samtools quickcheck"
            self.flagger.flag(**partial_check_args)


    def _check_samples_proportions_for_dataset_flags(self):
        ### Check if any sample proportion related flags should be raised
        PROTOFLAG_MAP = {
            60 : [60],
            50 : [50, 60]
        }
        check_id_with_samples_proportion_threshold = {"S_0003":"total_reads_mapped-Percentage",
                                                     "S_0004":"mapped_to_multiple_loci-Percentage",
                                    }

        for check_id, cutoffs_key in check_id_with_samples_proportion_threshold.items():
            check_args = dict()
            check_args["check_id"] = check_id
            self.flagger.check_sample_proportions(check_args = check_args,
                                             check_cutoffs = cutoffs[cutoffs_subsection][cutoffs_key],
                                             protoflag_map = PROTOFLAG_MAP)
