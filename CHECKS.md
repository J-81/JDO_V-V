# Checks and associated IDs performed during the VV

### FastQC

F_0001
Check if expected FastQC files exist based on samples

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
