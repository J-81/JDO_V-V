from __future__ import annotations
from pathlib import Path

from VV.flagging import Flagger
from VV.utils import filevalues_from_mapping, value_based_checks


class NormalizedFilesVV():
    def __init__(self,
                 normalized_file_dir: Path,
                 cutoffs: dict,
                 flagger: Flagger,
                 ):
        """ Performs VV for normalized files (reference: VV CHecklist #8,9,10
        """
        print("Running VV for Normalized Files")

        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("Normalized Files")
        cutoffs_subsection = "normalized_data"
        # generate expected files in the main sample directory

        for file, check_id in [
            (normalized_file_dir / "normalized-annotated.rda", "MICROARRAY_R_0008a"),
            (normalized_file_dir / "normalized-annotated.txt", "MICROARRAY_R_0008b"),
            (normalized_file_dir / "normalized_qa.html", "MICROARRAY_R_0008c"),
            (normalized_file_dir / "normalized.txt", "MICROARRAY_R_0008d"),
            (normalized_file_dir / "visualization_PCA_table.csv", "MICROARRAY_R_0008e"),
        ]:
            checkArgs = dict()
            checkArgs["check_id"] = check_id
            checkArgs["convert_sub_entity"] = False
            checkArgs["entity"] = "All_Samples"
            flagger.flag_file_exists(check_file = file,
                                     partial_check_args = checkArgs,
                                     optional = False)
