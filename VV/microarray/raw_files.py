from __future__ import annotations
from pathlib import Path

from VV.flagging import Flagger
from VV.utils import filevalues_from_mapping, value_based_checks


class RawFilesVV():
    def __init__(self,
                 file_mapping: dict,
                 raw_file_dir: Path,
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
        ###################################################################
        ### UNIQUE IMPLEMENTATION CHECKS ##################################
        # T_0001 ##########################################################
        file = self.check_for_annotation_file(raw_file_dir)
        checkArgs["check_id"] = "MICROARRAY_R_0003"
        checkArgs["convert_sub_entity"] = False
        checkArgs["entity"] = sample
        checkArgs["sub_entity"] = filelabel
        flagger.flag_file_exists(check_file = file,
                                 partial_check_args = checkArgs,
                                 optional = True)
        ###################################################################
        ### UNIQUE IMPLEMENTATION CHECKS ##################################
        # T_0001 ##########################################################
        file = self.check_for_raw_qa_file(raw_file_dir)
        checkArgs["check_id"] = "MICROARRAY_R_0004"
        checkArgs["convert_sub_entity"] = False
        checkArgs["entity"] = sample
        checkArgs["sub_entity"] = filelabel
        flagger.flag_file_exists(check_file = file,
                                 partial_check_args = checkArgs,
                                 optional = False)

        # R_0003 ##########################################################
        partial_check_args = dict()
        partial_check_args["check_id"] = "MICROARRAY_R_0002"
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

    def check_for_annotation_file(self, path):
        """ Checklist #3
        """
        putative_file = list(path.glob("*annotation.adf.txt"))
        assert len(putative_file) < 2
        return putative_file if putative_file else path / "*annotation.adf.txt"

    def check_for_raw_qa_file(self, path):
        """ Checklist #4
        """
        return path / "raw_qa.html"
