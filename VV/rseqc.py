""" VV related to the output from RSeQC
"""
import os
import subprocess
from pathlib import Path
from statistics import mean

from VV.utils import filevalues_from_mapping, value_based_checks, check_fastq_headers, general_mqc_based_check
from VV.utils import value_check_direct
from VV.flagging import Flagger
from VV import multiqc

class Rseqc():
    """ Representation of RSeQC output results data.
    """
    def __init__(self,
                 multiqc_json: Path,
                 samples: list,
                 flagger: Flagger,
                 cutoffs: dict,
                 outlier_comparision_point: str = "median"):
        print(f"Starting VV for RSeQC based on MultiQC file")
        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("RSeQC [MultiQC]")
        cutoffs_subsection = "rseqc"
        ##############################################################
        # STAGE MULTIQC DATA FROM JSON
        ############################################################## 
        # TODO: replace after general MQC parsing rework
        samples = [f"{sample}_infer_experiment" for sample in samples]
        file_mapping = {sample:{"infer_experiment":Path(f"01-TG_Preproc/RSeQC_Reports/{sample}_infer_experiment.out")} for sample in samples}
                
        mqc = multiqc.MultiQC(multiQC_json = multiqc_json,
                              file_mapping = file_mapping,
                              outlier_comparision_point = outlier_comparision_point)


        check_specific_args = [
            ("RS_1001", {"mqc_base_key":"rseqc_infer_experiment_plot-Sense"}),
            ("RS_1002", {"mqc_base_key":"rseqc_infer_experiment_plot-Antisense"}),
            ("RS_1003", {"mqc_base_key":"rseqc_infer_experiment_plot-Undetermined"}),
            ]

        for check_id, mqc_check_args in check_specific_args:
            check_args = {"convert_sub_entity":False}
            check_args["check_id"] = check_id
            check_args["full_path"] = Path(multiqc_json).resolve()
            check_args["filename"] = Path(multiqc_json).name
            general_mqc_based_check(check_args = check_args,
                                    samples = samples,
                                    mqc = mqc,
                                    cutoffs = cutoffs[cutoffs_subsection],
                                    flagger = flagger,
                                    **mqc_check_args)


        ## Aggregate assignment check
        check_args = {"convert_sub_entity":False, "entity":"All-Samples"}
        check_args["check_id"] = "RS_1004"
        check_args["full_path"] = Path(multiqc_json).resolve()
        check_args["filename"] = Path(multiqc_json).name
        average_sense = mean([mqc.data[sample]["infer_experiment-rseqc_infer_experiment_plot-Sense"].value for sample in samples])
        average_antisense = mean([mqc.data[sample]["infer_experiment-rseqc_infer_experiment_plot-Antisense"].value for sample in samples])
        average_undetermined = mean([mqc.data[sample]["infer_experiment-rseqc_infer_experiment_plot-Undetermined"].value for sample in samples])

        main_selection = max([average_sense, average_antisense])
        if average_sense > average_antisense:
            main_selection = (average_sense, "sense")
        elif average_antisense > average_sense:
            main_selection = (average_antisense, "antisense")
        # off chance of tie
        else:
            main_selection = (average_sense, "none")

        if main_selection[0] > 0.75:
           check_args["severity"] = 30
           check_args["debug_message"] = f"Mean {main_selection[1]}  strand selection > 0.75"
        elif 0.75 > main_selection[0] > 0.65:
           check_args["severity"] = 50
           check_args["debug_message"] = f"Mean {main_selection[1]}  strand selection between 0.75 and 0.65"
        else:
           check_args["severity"] = 90
           check_args["debug_message"] = f"Mean {main_selection[1]}  strand selection less than 0.65"
        flagger.flag(**check_args)
