#! /usr/bin/env python
""" This script generates excel files indicating the files to publish
"""
import sys
import re
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter

from VV.microarray.file_search import path_annotate

def infer_sample(path: Path, sample_list: list) -> str:
    """ Infers the sample based on the file path
    """
    inferred_sample = None
    for sample in sample_list:
        if sample in str(path):
            if not inferred_sample:
                inferred_sample = sample
            else:
                raise ValueError(f"Inferred another sample: {sample} but already inferred {inferred_sample}")
    if inferred_sample:
        return inferred_sample
    else:
        #print(f"No sample inferred from {str(path.path)}")
        #print("Returning '?'")
        return 'All samples'

def get_samples(runsheet_path: Path) -> list:
    """ Returns a list of sample names from a given runsheet
    """
    df = pd.read_csv(runsheet_path)
    sample_col = [col for col in df.columns if "sample" in col.lower()][0]
    return list(df[sample_col])

def main(root_path, runsheet_path, template, config_fs_f: Path, outputDir: Path = None):
    samples = get_samples(runsheet_path)
    # create table
    df_assigned = path_annotate(config_fs_f = config_fs_f, runsheet = runsheet_path, platform = template, root_dir = root_path, expand_annotations=True)
    df_assigned["Sample Name"] = df_assigned["fullPath"].apply(infer_sample, args=([samples]))
    
    # setting a filename column
    df_assigned["FileName"] = df_assigned['pathObj'].apply(lambda Path: Path.name)
    # Add '/' to start of directories to specify in the excel files
    df_assigned["FileName"] = df_assigned.apply(lambda row: f"/{row['FileName']}" if row['isDir'] else row['FileName'], axis="columns" )
    
    # write to excel file
    SPACES_BETWEEN_SAMPLES = 1
    COLUMN_LENGTH_BUFFER = 8
    for excel_file in df_assigned["Excel File"].unique():
        print(excel_file)
        output_file = f"{excel_file}_file_names.xlsx"
        options = {}
        options['strings_to_formulas'] = False
        options['strings_to_urls'] = False
        writer = pd.ExcelWriter(output_file, engine='openpyxl', options=options)
        df_file = df_assigned.loc[df_assigned["Excel File"] == excel_file]
        for SHEETNAME in df_file["Excel Sheet"].unique():
            print(f"Working on sheet name: {SHEETNAME}")
            df_file_sheet = df_file.loc[df_file["Excel Sheet"] == SHEETNAME]
            sample_dfs = list()
            dataset_df = None
            for i, (sample, gb) in enumerate(df_file_sheet.groupby("Sample Name")):
                columns = dict()
                for col in gb["Excel Column"].unique():
                    columns[col] = gb.loc[gb["Excel Column"] == col]["FileName"].to_list()
                # extend columns to match length of longest column
                max_col = max([len(col) for col in columns.values()])
                for key, col in columns.items():
                    columns[key] = col + [''] * (max_col - len(col) + SPACES_BETWEEN_SAMPLES)
                # create sample column
                columns["Sample Name"] = [sample] +  [''] * (max_col - 1 + SPACES_BETWEEN_SAMPLES)
                
                # convert to dataframe
                sample_dfs.append(pd.DataFrame(columns))
            # collapse into All samples if all sample_dfs are equivalent (excluding sample name)
            if (all(sample_df.drop("Sample Name", axis=1).equals(sample_dfs[0].drop("Sample Name", axis=1)) for sample_df in sample_dfs)):
                all_samples_df = sample_dfs[0]
                all_samples_df["Sample Name"] = ["All Samples"] + all_samples_df["Sample Name"].to_list()[1:]
                sample_dfs = [all_samples_df]
            for sample_df in sample_dfs:
                dataset_df = sample_df if not isinstance(dataset_df, pd.DataFrame)  else pd.concat([dataset_df, sample_df])
            
            dataset_df = dataset_df.reset_index(drop=True)
            proper_order = ["Sample Name"] + [col for col in dataset_df.columns if col != "Sample Name"]
            dataset_df = dataset_df.reindex(columns=proper_order)
            print(f"Writing sheet {SHEETNAME} in file {output_file}")
            print(dataset_df.head(20))
            dataset_df.to_excel(writer, sheet_name=SHEETNAME, index=False, header=True)
            # autoresize based on items
            worksheet = writer.sheets[SHEETNAME]
            for idx, col in enumerate(dataset_df.columns):
                max_len = max((dataset_df[col].astype(str).map(len).max()), len(str(col))) + COLUMN_LENGTH_BUFFER # max of either longest column value or column header plus a buffer character
                print(max_len, SHEETNAME)
                worksheet.column_dimensions[get_column_letter(idx+1)].width = max_len
            writer.save()
    return df_assigned 

if __name__ == '__main__':
    main(root_path = Path(sys.argv[1]), runsheet_path = Path(sys.argv[2]), template = "Bulk_RNASeq:PairedEnd", config_fs_f=sys.argv[3])
