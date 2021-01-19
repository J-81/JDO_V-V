""" Validation and Verification Program For RNASeq Consenus Pipeline


"""
import os
import logging
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)

from VV import raw_reads

# TODO: convert to proper configuration
GLDS = 194
PARENT_PATH = "/data2/JO_Internship_2021/V-V_scripts"

DATA_PATH = os.path.join(PARENT_PATH, f"GLDS-{GLDS}")
PAIRED_END = True

def main():
    """ Calls raw and processed data V-V functions
    """
    log.info("Starting Raw Data V-V")
    raw_path = os.path.join(DATA_PATH, "00-RawData", "Fastq")
    log.debug(f"raw_path: {raw_path}")
    raw_results = raw_reads.validate_verify(input_path=raw_path,
                                            paired_end=PAIRED_END)
    log.info("Finished Raw Data V-V")

if __name__ == '__main__':
    main()
