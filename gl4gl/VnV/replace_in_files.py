""" This tool replaces strings from files """
import sys
import re
from pathlib import Path

import yaml
import pandas as pd

from VV.file_search import path_annotate

def generate_new_script(orig_script: Path, new_script: Path, config_remap: dict) -> None:
    """ Generates new scripts 
    Params:
    orig_script: the original script file
    new_script: location for the new script file after replacing substrings
    config_remap: {original_substring:new_substring} to remap globally
    """
    def iter_remap(orig: str, remapper: dict) -> str:
        remap = [None for i in range(10)]
        for block, remap_set in remapper.items():
            remap[int(remap_set['order'])] = remap_set 
        
        # remove unused order slots
        remap = [remap_set for remap_set in remap if remap_set]
        
        # remap substrings
        new_string = None
        for remap_set in remap:
            for old_subs, new_subs in remap_set.items():
                if old_subs == "order":
                    continue
                new_string =  new_string.replace(old_subs,new_subs) if new_string else  orig.replace(old_subs,new_subs)
        return new_string

    # read in original lines    
    with open(orig_script, "r") as f:
        orig_lines = f.readlines()

    # remap lines with remapper dict
    new_lines = [iter_remap(line, config_remap) for line in orig_lines]

    print(new_script)
    print("".join(new_lines))
    print("----")

    # rewrite to the new path
    # create dirs as needed
    new_script.parent.mkdir(parents=True, exist_ok=True)
    with open(new_script, "w") as f:
        for line in new_lines:
            f.write(f"{line}")

def main(root_dir: Path, runsheet: Path, template: str, config_fs_f: Path, config_remap_f: Path, outputDir: Path = None):
    """
    Params:
        root_dir: top level directory for a dataset
        runsheet: metadata csv file that MUST contain a column 'sample_name' denoting the sample IDs
        template: A string denoting the top two keys in the config file search yaml, these denote assay main technology and sub_technology. e.g. 'Bulk_RNASeq:PairedEnd'
        config_fs_f: the file search config yaml
        config_remap_f: the remap config yaml indicating what substrings to replace and how
    """
    NEW_SCRIPTS_PATH = "processing_scripts_NOpaths"
    ORIG_SCRIPTS_PATH = "processing_scripts"

    # load remapper config
    with open(config_remap_f, "r") as f:
        config_remap =  yaml.safe_load(f)

    # create dataframe of annotated paths
    df = path_annotate(config_fs_f = config_fs_f, runsheet = runsheet, template = template, root_dir = root_dir, expand_annotations=True) 

    # filter to just scripts
    df = df.loc[df['needsRemap'] == True]

    # create target paths for all files
    df['new_path'] = df['fullPath'].apply(lambda path: Path(str(path).replace(ORIG_SCRIPTS_PATH,NEW_SCRIPTS_PATH)))


    df.apply(lambda row: generate_new_script(orig_script = row["pathObj"], new_script = row['new_path'], config_remap = config_remap), axis="columns")

    print(df.head())

    return df

if __name__ == '__main__':
    main(root_dir = Path(sys.argv[1]), runsheet = Path(sys.argv[2]), template = "Bulk_RNASeq:PairedEnd", config_fs_f=sys.argv[3], config_remap_f=sys.argv[4] )
