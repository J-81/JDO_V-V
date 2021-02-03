""" VV related to the output from STAR alignment
"""
import os
import subprocess
import logging
log = logging.getLogger(__name__)

from VV.utils import bytes_to_gb

class StarAlignments():
    """ Representation of Star Alignment output results data.
    Includes parsing for:
      - <sample>_Log.final.out
      - <sample>_Aligned.sortedByCoord.out.bam
      - <sample>_Aligned.toTranscriptome.out.bam
    """
    def __init__(self,
                 samples: str,
                 dir_path: str):
        log.debug(f"Checking STAR Alignment Results")
        self.samples = samples
        self.dir_path = dir_path
        self.final = self._parse_log_final()
        self._validate_alignment_files()

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
            if not os.path.isfile(file_path):
                log.error(f"FAIL: {sample} does not have *_Log.final.out file")
                continue
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
        return final_data

    def _validate_alignment_files(self):
        """ Checks for existence of expected alignment files.

        Also checks using samtools quickcheck which should catch truncations and
            malformed header information. Source: http://www.htslib.org/doc/samtools-quickcheck.html
        """
        for sample in self.samples:
            log.debug(f"Checking Star Alignment Files for {sample}")
            coord_file = os.path.join(self.dir_path,
                                      sample,
                                      f"{sample}_Aligned.sortedByCoord.out.bam")
            if not os.path.isfile(coord_file):
                log.error(f"FAIL: {sample} does not "
                           "have *_Aligned.sortedByCoord.out.bam file")
                continue

            # check with coord file with samtools
            process = subprocess.Popen(['samtools', 'quickcheck', coord_file],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                print(f"FAIL: samtools quick checkout output for {sample} on {coord_file}: {stdout}")

            # check transcriptome alignment file
            transcript_file = os.path.join(self.dir_path,
                                      sample,
                                      f"{sample}_Aligned.toTranscriptome.out.bam")
            if not os.path.isfile(transcript_file):
                log.error(f"FAIL: {sample} does not "
                           "have *_Aligned.toTranscriptome.out.bam")
                continue
            # check with coord file with samtools
            process = subprocess.Popen(['samtools', 'quickcheck', transcript_file],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                print(f"FAIL: samtools quick checkout output for {sample} on {transcript_file}: {stdout}")

            log.debug(f"Finished Checking Star Alignment Files for {sample}")
