#! /usr/bin/env python
""" Validation and Verification Program For RNASeq Consenus Pipeline

Called by V-V_Program.  Not intended for direct use.
"""
from pathlib import Path

from VV import raw_reads
from VV import trimmed_reads
from VV import fastqc
from VV.parameters import PARAMS as MODULEPARAMS
from VV.star import StarAlignments
from VV.data import Dataset
from VV.rnaseq_samplesheet import RNASeqSampleSheet
from VV.rsem import RsemCounts
from VV.deseq2 import Deseq2ScriptOutput
from VV.flagging import Flagger

def main(config, params):
    """ Calls raw and processed data V-V functions

    :param config: configuration object
    """
    program_header = "STARTING VV for Data Processed by RNASeq Consenus Pipeline"
    print(f"{'┅'*(len(program_header)+4)}")
    print(f"┇ {program_header} ┇")
    print(f"{'┅'*(len(program_header)+4)}")
    # set up flagger
    flagger = Flagger(__file__,
                      halt_level = config["Logging"].getint("HaltSeverity"))
    ########################################################################
    # ISA File parsing
    ########################################################################
    isa_zip_path = Path(config["Paths"].get("ISAZip"))
    isa = Dataset(isa_zip_path = isa_zip_path,
                  flagger = flagger,
                  entity = f"GLDS-{config['GLDS'].get('Number')}")
    isa.validate_verify(vv_for = "RNASeq")
    samples = isa.get_sample_names(assay_name = "transcription profiling by RNASeq")
    ########################################################################
    # RNASeqSampleSheet Parsing
    ########################################################################
    cross_checks = dict()
    samplesheet_path = Path(config["Paths"].get("SampleSheetPath"))
    samplesheet_cross_check = RNASeqSampleSheet(samplesheet = samplesheet_path).cross_check
    cross_checks["SampleSheet"] = samplesheet_cross_check
    ########################################################################
    # Raw Read VV
    ########################################################################
    raw_reads.validate_verify(raw_reads_dir = Path(config["Paths"].get("RawReadDir")),
                              samples = samples,
                              flagger = flagger,
                              params = params
                              )
    raw_reads.validate_verify_multiqc(multiqc_json = Path(config["Paths"].get("RawMultiQCDir")) / "multiqc_data.json",
                                      samples = samples,
                                      flagger = flagger,
                                      params = params,
                                      outlier_comparision_point = "median")


    ########################################################################
    # Trimmed Read VV
    ########################################################################
    trimmed_reads.validate_verify(raw_reads_dir = Path(config["Paths"].get("TrimmedReadDir")),
                              samples = samples,
                              flagger = flagger,
                              params = params
                              )
    trimmed_reads.validate_verify_multiqc(multiqc_json = Path(config["Paths"].get("TrimmedMultiQCDir")) / "multiqc_data.json",
                                      samples = samples,
                                      flagger = flagger,
                                      params = params,
                                      outlier_comparision_point = "median")
    ###########################################################################
    # STAR Alignment VV
    ###########################################################################
    StarAlignments(samples=samples,
                   dir_path=config['Paths'].get("StarParentDir"),
                   flagger = flagger,
                   params = params)
    ###########################################################################
    # RSEM Counts VV
    ###########################################################################
    rsem_cross_check =   RsemCounts(samples= samples,
                                   dir_path=config['Paths'].get("RsemParentDir"),
                                   flagger = flagger,
                                   params = params).cross_check
    cross_checks["RSEM"] = rsem_cross_check
    ###########################################################################
    # Deseq2 Normalized Counts VV
    ###########################################################################
    Deseq2ScriptOutput(samples = samples,
                       counts_dir_path = Path(config['Paths'].get("Deseq2NormCountsParentDir")),
                       dge_dir_path = Path(config['Paths'].get("Deseq2DGEParentDir")),
                       flagger = flagger,
                       params = params,
                       cross_checks = cross_checks)

    print(f"{'='*40}")
    print(f"VV complete: Full Results Saved To {flagger._log_file}")

    ###########################################################################
    # Generate derivative log files
    ###########################################################################
    for log_type in ["only-issues", "by-sample", "by-step"]:
        flagger.generate_derivative_log(log_type = log_type,
                                        samples = samples)
    # Return flagger at successful completion
    return flagger
