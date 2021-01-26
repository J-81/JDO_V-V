""" Validation and Verification Program For RNASeq Consenus Pipeline

Terminology:
- SampleWise: Describes metric based on entire sample
- ReadsWise: Describes metrics based on a read file (forward and reverse reads
    for the same samples are distinct entities in when this term is used)
- DatasetWise: Describes metric based on all samples in set
- PASS: Indicates the data has passed a V&V condition
- FAIL: Indicates the data has failed a V&V condition and will need further manually assessment
- WARN: Indicates the data has an anomoly.  In aggregate, this may indicate
    further manual assessment but by taken itself should not require such measures 
"""
import os
import sys
import logging
# TODO: replace with proper argpase
print(sys.argv)
if len(sys.argv) == 2:
    if sys.argv[1] in ["INFO","DEBUG","WARNING"]:
        log_levels = {"INFO":20,"DEBUG":10,"WARNING":30}
        logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            level=log_levels[sys.argv[1]])
    else:
        print("Logging level must be one of the following: <INFO,DEBUG,WARNING>")
        sys.exit()

else:
    print("Using INFO logging level by default")
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        level=logging.INFO)

log = logging.getLogger(__name__)

from VV import raw_reads, parse_isa, fastqc, multiqc

# TODO: convert to proper configuration
GLDS = 194
# oberyn
PARENT_PATH = "/data2/JO_Internship_2021/V-V_scripts"
# local
# PARENT_PATH = "/home/joribello/Documents/OneDrive/NASA/Fall2020/project/V-V_scripts"

DATA_PATH = os.path.join(PARENT_PATH, f"GLDS-{GLDS}")
PAIRED_END = True

### Raw Read Parameters
AVG_SEQUENCE_LENGTH_TOLERANCE = 0.1

def main():
    """ Calls raw and processed data V-V functions
    """

    log.info("Parsing ISA and Extracting Sample Names")
    isa_zip_path = os.path.join(DATA_PATH,
                                "Metadata",
                                f"GLDS-{GLDS}_metadata_GLDS-{GLDS}-ISA.zip")
    samples_dict = parse_isa.get_sample_names(isa_zip_path)
    isa_raw_sample_names = set([sample
                            for study in samples_dict.values()
                            for assay_samples in study.values()
                            for sample in assay_samples])
    log.debug(f"Full Sample Name Dict: {samples_dict}")
    log.info(f"{len(isa_raw_sample_names)} "
             f"Total Unique Samples Found: {isa_raw_sample_names}")

    log.info("Starting Raw Data V-V")
    raw_path = os.path.join(DATA_PATH, "00-RawData")
    log.debug(f"raw_path: {raw_path}")
    raw_results = raw_reads.validate_verify(input_path=raw_path,
                                            paired_end=PAIRED_END,
                                            check_lines=False)
    log.info("Finished Raw Data V-V")

    log.info("Starting Check Raw FastQC and MultiQC files")
    fastqc_path = os.path.join(DATA_PATH, "00-RawData", "FastQC_Reports")
    log.debug(f"fastQC_path: {fastqc_path}")
    fastqc.validate_verify(samples=isa_raw_sample_names,
                           input_path=fastqc_path,
                           paired_end=PAIRED_END,
                           expected_suffix="_raw_fastqc")

    multiqc_path = os.path.join(DATA_PATH,
                                "00-RawData",
                                "FastQC_Reports",
                                "raw_multiqc_report",
                                "raw_multiqc_data.zip")
    multiqc.validate_verify(multiQC_zip_path=multiqc_path,
                            paired_end=PAIRED_END,
                            sequence_length_tolerance=AVG_SEQUENCE_LENGTH_TOLERANCE)
    log.info("Finished Check Raw FastQC and MultiQC files")

    log.debug(f"Results from Raw VV: {raw_results}")

    log.info(f"Checking if sample names from raw reads folder match ISA file")
    sample_names_match = raw_results.sample_names == isa_raw_sample_names
    checkname = "ISA sample names should match raw reads folder"
    if sample_names_match:
        log.info(f"PASS: {checkname}")
    else:
        log.error(f"FAIL: {checkname}: "
                  f"ISA: {isa_raw_sample_names}"
                  f"RawReads Folder: {raw_results.sample_names}")


if __name__ == '__main__':
    main()
