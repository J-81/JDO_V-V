# Checks and associated IDs performed during the VV

### ISA

- S_0001 (Implemented)
  - Check that ISA file exists at specified path.

- S_0002 (Implemented)
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
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red


- R_0012 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for N calls per position.
  - Global Threshold 1: 3% - 8% of total bases/read >80% of reads/sample -> Warning - yellow
  - Global Threshold 2: 8%+ of total bases/read >80% of reads/sample -> Warning - red

- R_0014 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for Top overrepresented sequence percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

- R_0015 (To be staged -> validate_verify_multiqc)
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

- T_1002 (Implemented)
  - Sample-wise comparison check that read lengths are the same.

- T_0007 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for duplication percentage outliers.
    - Global Threshold 1: 40 - 60% -> Warning - yellow
    - Global Threshold 2: 60%+ -> Warning - red
    - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_0007 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for GC content outliers.
    - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
    - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_0008 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for sequence quality by position.
  - Standard Deviation Threshold 1: 2 - 3 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 3+ deviations -> Warning - red

- T_0009 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for sequence quality by sequence.
  - Standard Deviation Threshold 1: 2 - 3 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 3+ deviations -> Warning - red

- T_0010 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for GC content in sequence position bins.
  - Standard Deviation Threshold 1: 2 - 4 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: 4+ deviations -> Warning - red

- T_0011 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for N calls per position.
  - Global Threshold 1: 3% - 8% of total bases/read >80% of reads/sample -> Warning - yellow
  - Global Threshold 2: 8%+ of total bases/read >80% of reads/sample -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

- T_0012 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for sequence duplication.
  - Standard Deviation Threshold 1: for any duplication level bin if 2+ deviations -> Warning - red


- T_0013 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for Top overrepresented sequence percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red


- T_0014 (To be staged -> validate_verify_multiqc)
  - Sample-wise comparison for Sum of  remaining overrepresented sequences percent of total sequences.
  - Global Threshold 1: 40% - 60% duplication percent/ in >80% of samples -> Warning - yellow
  - Global Threshold 2: 60%+ duplication percent/ in >80% of samples -> Warning - red
  - Standard Deviation Threshold 1: aggregate N calls 1 - 2 deviations -> Warning - yellow
  - Standard Deviation Threshold 2: aggregate N calls 2+ deviations -> Warning - red

- T_0015 (To be staged -> validate_verify_multiqc)
  - Sample-wise adapters should be removed.
  - Global Threshold 1: 1% - 3% sequences with detected adapter content in >80% of samples -> Warning - yellow
  - Global Threshold 2: 3%+ sequences with detected adapter content in >80% of samples -> Warning - red

### FastQC

 - F_0001 (Implemented)
   - Check if expected FastQC files exist based on samples
    - zip and html file should exist for each sample

### Deseq2

D_0001
Check that samples is SampleTable.csv match samples parsed from ISA

D_0002
Check that SampleTable.csv file exists

D_0003
Check that samples is Unnormalized_Counts.csv match samples parsed from ISA

D_0004
Check that Unnormalized_Counts.csv file exists

D_0005
Check that samples is Normalized_Counts.csv match samples parsed from ISA

D_0006
Check that Normalized_Counts.csv file exists

D_0007
Check that samples is ERCC_Normalized_Counts.csv match samples parsed from ISA

D_0008
Check that ERCC_Normalized_Counts.csv file exists

D_0009
For datasets with ERCC, check that normalized counts table has fewer genes than unnormalized counts table.
This is because ERCC genes should be removed from normalized counts but left in unnormalized counts.

D_0010
Check that normalized counts table has fewer values differ from unnormalized counts table values.
This is performed by checking the first gene with the same name in both tables and ensuring the values do not match.

###
