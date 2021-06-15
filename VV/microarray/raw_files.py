from __future__ import annotations

from VV.flagging import Flagger
from VV.utils import filevalues_from_mapping, value_based_checks


class RawFilesVV():
    def __init__(self,
                 file_mapping: dict,
                 cutoffs: dict,
                 flagger: Flagger,
                 ):
        """ Performs VV for trimmed reads for checks involving trimmed reads files directly
        """
        print("Running VV for Raw Files <INCOMPLETE IMPLEMENTATION>")

        ##############################################################
        # SET FLAGGING OUTPUT ATTRIBUTES
        ##############################################################
        flagger.set_script(__name__)
        flagger.set_step("Raw Files")
        cutoffs_subsection = "raw_files"
        # generate expected files in the main sample directory
        self.file_mapping = file_mapping
        ###################################################################
        # PERFROM CHECKS
        ###################################################################
        ### UNIQUE IMPLEMENTATION CHECKS ##################################
        # T_0001 ##########################################################
        for sample, file_map in file_mapping.items():
            checkArgs = dict()
            checkArgs["check_id"] = "MICROARRAY_R_0001"
            checkArgs["convert_sub_entity"] = False
            checkArgs["entity"] = sample
            missing_files = list()
            for filelabel, file in file_map.items():
                checkArgs["sub_entity"] = filelabel
                flagger.flag_file_exists(check_file = file,
                                         partial_check_args = checkArgs)


        # R_0003 ##########################################################
        partial_check_args = dict()
        partial_check_args["check_id"] = "MICROARRAY_R_0003"
        partial_check_args["convert_sub_entity"] = False
        def file_size(file: Path):
            """ Returns filesize for a Path object
            """
            return file.stat().st_size/float(1<<30)
        # compute file sizes
        filesize_mapping, all_filesizes = filevalues_from_mapping(file_mapping, file_size)

        metric = "file_size"
        value_based_checks(partial_check_args = partial_check_args,
                           check_cutoffs = cutoffs[cutoffs_subsection],
                           value_mapping = filesize_mapping,
                           all_values = all_filesizes,
                           flagger = flagger,
                           value_alias = metric,
                           middlepoint = cutoffs[cutoffs_subsection]["middlepoint"]
                           )
