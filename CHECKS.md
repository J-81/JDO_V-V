# Checks and associated IDs performed during the VV

### ISA

- I_0001 (Implemented)
  - Check that ISA file exists at specified path.

- I_0002 (Implemented)
  - Check that valid experiment is described in ISA file.
    - Metadata: 'Study Assay Measurement Type' must include 'transcription profiling'
    - Metadata: 'Study Assay Technology Type' must include 'RNA Sequencing (RNA-Seq)'

### Raw Reads

- R_0001 (Implemented)
  - Check that raw reads exist for the samples described in ISA.
    - Input: SAMPLE, list of sample names.
    - Assumption for single end: File expected is {SAMPLE}_R1_raw.fastq.gz
    - Assumption for paired end: Files expected are {SAMPLE}_R1_raw.fastq.gz and {SAMPLE}_R2_raw.fastq.gz
    - Assumption: SAMPLE never includes "_R1_raw.fastq.gz" nor "_R2_raw.fastq.gz"

- R_0002 (Implemented)
  - Check that raw reads headers are present every 4 lines.
    - Configuration: By default, first 10,000,000 lines are checked.

- R_0003 (Implemented)
  - Check for outliers in terms of file size.
    - Assumption: Raw reads files should be comparable in terms of file size.

- R_1001 (Implemented)
  - Check that read counts between paired raw reads match.

- R_1002 (Implemented)
  - Sample-wise comparison check that read lengths are the same.

- R_1003 (Implemented)
  - Sample-wise comparison for duplication percentage outliers.
    - Global Threshold 1: 40 - 60% -> Warning - yellow
    - Global Threshold 2: 60%+ -> Warning - red
    - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- R_1004 (Implemented)
  - Sample-wise comparison for GC content outliers.
    - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- R_1005 (Implemented)
  - Sample-wise comparison for sequence quality by position.
  - Standard Deviation Threshold 1: 2 - 3 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 3+ deviations -> Warning - red

- R_1006 (Implemented)
  - Sample-wise comparison for sequence quality by sequence.
  - Standard Deviation Threshold 1: 2 - 3 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 3+ deviations -> Warning - red

- R_1007 (Implemented)
  - Sample-wise comparison for GC content in sequence position bins.
  - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- R_1008 (Implemented)
  - Sample-wise comparison for sequence duplication.
  - Standard Deviation Threshold 1: for any duplication level bin if 2+ deviations -> Warning - red

- R_1009 (Implemented)
  - Sample-wise comparison for N calls per position.
  - Standard Deviation Threshold 1: Summed N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: Summed N calls 2+ deviations -> Warning - red

- R_0010 (Implemented) [Change for globals below]
  - Global Threshold 1: NEW - Mean position value > 3% Prior(3% - 8% of total bases/read >80% of reads/sample) -> Warning - yellow
  - Global Threshold 2: NEW - Mean position value > 8% Prior(8%+ of total bases/read >80% of reads/sample) -> Warning - red

- R_0011 (Implemented)
  - Sample-wise comparison for Top overrepresented sequence percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

- R_0012 (Implemented)
  - Sample-wise comparison for Sum of  remaining overrepresented sequences percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

### Trimmed Reads

- T_0001 (Implemented)
  - Check that raw reads exist for the samples described in ISA.
    - Input: SAMPLE, list of sample names.
    - Assumption for single end: File expected is {SAMPLE}_R1_raw.fastq.gz
    - Assumption for paired end: Files expected are {SAMPLE}_R1_raw.fastq.gz and {SAMPLE}_R2_raw.fastq.gz
    - Assumption: SAMPLE never includes "_R1_raw.fastq.gz" nor "_R2_raw.fastq.gz"

- T_0002 (Implemented)
  - Check that raw reads headers are present every 4 lines.
    - Configuration: By default, first 10,000,000 lines are checked.

- T_0003 (Implemented)
  - Check for outliers in terms of file size.
    - Assumption: Raw reads files should be comparable in terms of file size.

- T_1001 (Implemented)
  - Check that read counts between paired read files match.

- T_1002 (Implemented) [Change to pass vs Warning-Yellow]
  - Sample-wise comparison check that read lengths are the similar.
    - passes if no outliers detected. No yellow warning in this case
      - rationale: some variation is okay as adapter trimming will yield different lengths depending on how much adapter contamination was in a given sequence

- T_1003 (Implemented)
  - Sample-wise comparison for duplication percentage outliers.
    - Global Threshold 1: 40 - 60% -> Warning - yellow
    - Global Threshold 2: 60%+ -> Warning - red
    - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_1004 (Implemented)
  - Sample-wise comparison for GC content outliers.
    - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_1005 (Implemented)
  - Sample-wise comparison for Top overrepresented sequence percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_1006 (Implemented)
  - Sample-wise comparison for Sum of  remaining overrepresented sequences percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

- T_1007 (Implemented)
  - Sample-wise comparison for sequence quality by position.
  - Standard Deviation Threshold 1: 2 - 3 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 3+ deviations -> Warning - red

- T_1008 (Implemented)
  - Sample-wise comparison for sequence quality by sequence.
  - Standard Deviation Threshold 1: 2 - 3 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 3+ deviations -> Warning - red

- T_1009 (Implemented)
  - Sample-wise comparison for GC content in sequence bins.
  - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_1010 (Implemented)
  - Sample-wise comparison for sequence duplication.
  - Standard Deviation Threshold 1: for any duplication level bin if 2+ deviations -> Warning - red

- T_1011 (Implemented)
  - Sample-wise comparison for N calls per position.
    - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

- T_1012 (Implemented)
  - Sample-wise comparison for N calls per position.
    - Global Threshold 1: NEW - Mean position value > 3% Prior(3% - 8% of total bases/read >80% of reads/sample) -> Warning - yellow
    - Global Threshold 2: NEW - Mean position value > 8% Prior(8%+ of total bases/read >80% of reads/sample) -> Warning - red

- T_1013 (Implemented) [Changed]
  - Sample-wise adapters should be removed.
    - Global Threshold 1: greater than 80% of samples have at least 0.1% adaptor content -> Warning - red

### FastQC

 - F_0001 (Implemented)
   - Check if expected FastQC files exist based on samples
    - zip and html file should exist for each sample

### STAR

- S_0001 (Implemented)
 - Check *_Log.final.out exists and looks correct (checked by data parsing)

- S_0002 (Implemented)
  - Check *_Log.out exists and looks correct
    - Checks first line starts with "STAR version=" and last line is "ALL DONE!"

- S_0003 (Implemented)
 - Total Reads (Uniquely mapped reads % + % of reads mapped to multiple loci) check
   - Warning-Yellow : 70% < value < 50%
   - Warning-Red : value < 50%
   - DATASETWISE : >80% of samples flagged

- S_0004 (Implemented)
 - Multiple Loci check (% of reads mapped to multiple loci + Number of reads mapped to too many loci)
   - Warning-Yellow : 30% < value < 15%
   - Warning-Red : value < 30%
   - DATASETWISE : >80% of samples flagged

### RSEM

- M_0001 (Implemented)
  - Check that gene counts files exists

- M_0002 (Implemented)
  - Check that isform counts files exists

- M_0003 (Implemented)
    - Under average flags (does not include ERCC)
      - Warning-Yellow : value < average of counts

- M_0004 (Implemented)
    - Under average flags (does not include ERCC)
      - Warning-Yellow : value < average of counts


- M_0005 (Implemented)
  - Check for counts for unique gene
    - Outliers (with ERCC genes included)
      - Warning-Yellow : 4 < value < 2
      - Warning-Red : 4+

- M_0006 (Implemented)
  - Check for counts for unique transcripts
    - Outliers (with ERCC isoforms included)
      - Warning-Yellow : 4 < value < 2
      - Warning-Red : 4+

- M_0007 (Implemented)
  - Check for ERCC genes
    - Outlier
      - Warning-Yellow : 4 < value < 2
      - Warning-Red : 4+
    - Minimum threshold
      - Warning-Red  : 1

### Deseq2

- D_0001 (Implemented)
  - Check that SampleTable.csv file exists and samples match what is expected (likely as parsed from the ISA files)

- D_0002 (Implemented)
  - Check that Unnormalized_Counts.csv file exists and samples match what is expected (likely as parsed from the ISA files)

- D_0003 (Implemented)
  - Check that Normalized_Counts.csv file exists and samples match what is expected (likely as parsed from the ISA files)

- D_0004 (Implemented)
  - Check that ERCC_Normalized_Counts.csv file exists and samples match what is expected (likely as parsed from the ISA files)
