#! /usr/bin/env python
""" This script generates excel files indicating the files to publish
"""
import sys
import re
from pathlib import Path
from typing import Tuple

import pandas as pd
from openpyxl.utils import get_column_letter

# from VV.file_search import get_annotated_paths_df
from gl4gl.PathAnnotate import get_annotated_paths_df


def infer_sample(path: Path, sample_list: list) -> str:
    """ Infers the sample based on the file path
    """
    inferred_sample = None
    for sample in sample_list:
        if sample in str(path):
            if not inferred_sample:
                inferred_sample = sample
            else:
                raise ValueError(
                    f"Inferred another sample: {sample} but already inferred {inferred_sample}"
                )
    if inferred_sample:
        return inferred_sample
    else:
        # print(f"No sample inferred from {str(path.path)}")
        # print("Returning '?'")
        return "All samples"


def get_samples(runsheet_path: Path) -> list:
    """ Returns a list of sample names from a given runsheet
    """
    df = pd.read_csv(runsheet_path)
    sample_col = [col for col in df.columns if "sample" in col.lower()][0]
    return list(df[sample_col])


def generate_files_reports(
    root_path: Path,
    runsheet_path: Path,
    template: str,
    config_fs_f: Path,
    expected_files: set = {"processed", "raw", "unpublished"},
    outputDir: Path = None,
) -> Tuple[Path, Path, Path]:
    """Generate excel files: raw_file_names.xlsx and processed_file_names.xlsx
    Based on GLDS-207 examples provided by DP lead.
    By default, following excel files are created:
    - processed_file_names.xlsx: A file with all processed files to be publish on the GeneLab repo
    - raw_file_names.xlsx: A file with all raw files to be published on the GeneLab repo
    - unpublished_file_names.xlsx: A file with all files that were generated but will not be published to the GeneLab repo

    :param root_path: Top level directory containing all files, e.g. GLDS-207
    :type root_path: Path
    :param runsheet_path: A csv file with requisite sample names and metadata
    :type runsheet_path: Path
    :param template: A string denoting the config keys to use, e.g. "Bulk_RNASeq:PairedEnd"
    :type template: str
    :param config_fs_f: A yaml config file used to annotate and ultimately direct files and paths in the final excel file
    :type config_fs_f: Path
    :param expected_files: The list of files to generate (based on 'Excel File' annotation column)
    :type expected_files: set
    :param outputDir: Output directory, defaults to None (Current working directory)
    :type outputDir: Path, optional
    :return: A tuple with the three output excel files
    :rtype: Tuple[Path, Path, Path]
    """

    samples = get_samples(runsheet_path)
    # create table
    df = get_annotated_paths_df(
        config_fs_f=config_fs_f,
        runsheet=runsheet_path,
        template=template,
        root_dir=root_path,
        expand_annotations=True,
    )
    df["Sample Name"] = df["fullPath"].apply(infer_sample, args=([samples]))

    # setting a filename column
    df["FileName"] = df["pathObj"].apply(lambda Path: Path.name)
    # Add '/' to start of directories to specify in the excel files
    df["FileName"] = df.apply(
        lambda row: f"/{row['FileName']}" if row["isDir"] else row["FileName"],
        axis="columns",
    )

    # ensure only the three files are generated
    expected_files = {"processed", "raw", "unpublished"}
    found_files = set(df["Excel File"].unique())
    assert (
        found_files == expected_files
    ), f"Expected only these 'Excel File' annotation values: {expected_files} but found {found_files}"

    output_files = list()
    # write to excel file
    SPACES_BETWEEN_SAMPLES = 1
    COLUMN_LENGTH_BUFFER = 8
    for excel_file in ["processed", "raw", "unpublished"]:
        print(excel_file)
        output_file = f"{excel_file}_file_names.xlsx"
        output_files.append(Path(output_file))
        options = {}
        options["strings_to_formulas"] = False
        options["strings_to_urls"] = False
        writer = pd.ExcelWriter(output_file, engine="openpyxl", options=options)
        df_file = df.loc[df["Excel File"] == excel_file]
        for SHEETNAME in df_file["Excel Sheet"].unique():
            print(f"Working on sheet name: {SHEETNAME}")
            df_file_sheet = df_file.loc[df_file["Excel Sheet"] == SHEETNAME]
            sample_dfs = list()
            dataset_df = None
            for i, (sample, gb) in enumerate(df_file_sheet.groupby("Sample Name")):
                columns = dict()
                for col in gb["Excel Column"].unique():
                    columns[col] = gb.loc[gb["Excel Column"] == col][
                        "FileName"
                    ].to_list()
                # extend columns to match length of longest column
                max_col = max([len(col) for col in columns.values()])
                for key, col in columns.items():
                    columns[key] = col + [""] * (
                        max_col - len(col) + SPACES_BETWEEN_SAMPLES
                    )
                # create sample column
                columns["Sample Name"] = [sample] + [""] * (
                    max_col - 1 + SPACES_BETWEEN_SAMPLES
                )

                # convert to dataframe
                sample_dfs.append(pd.DataFrame(columns))
            # collapse into All samples if all sample_dfs are equivalent (excluding sample name)
            if all(
                sample_df.drop("Sample Name", axis=1).equals(
                    sample_dfs[0].drop("Sample Name", axis=1)
                )
                for sample_df in sample_dfs
            ):
                all_samples_df = sample_dfs[0]
                all_samples_df["Sample Name"] = ["All Samples"] + all_samples_df[
                    "Sample Name"
                ].to_list()[1:]
                sample_dfs = [all_samples_df]
            for sample_df in sample_dfs:
                dataset_df = (
                    sample_df
                    if not isinstance(dataset_df, pd.DataFrame)
                    else pd.concat([dataset_df, sample_df])
                )

            dataset_df = dataset_df.reset_index(drop=True)
            proper_order = ["Sample Name"] + [
                col for col in dataset_df.columns if col != "Sample Name"
            ]
            dataset_df = dataset_df.reindex(columns=proper_order)
            print(f"Writing sheet {SHEETNAME} in file {output_file}")
            print(dataset_df.head(20))
            dataset_df.to_excel(writer, sheet_name=SHEETNAME, index=False, header=True)
            # autoresize based on items
            worksheet = writer.sheets[SHEETNAME]
            for idx, col in enumerate(dataset_df.columns):
                max_len = (
                    max((dataset_df[col].astype(str).map(len).max()), len(str(col)))
                    + COLUMN_LENGTH_BUFFER
                )  # max of either longest column value or column header plus a buffer character
                print(max_len, SHEETNAME)
                worksheet.column_dimensions[get_column_letter(idx + 1)].width = max_len
            writer.save()
    return output_files


if __name__ == "__main__":
    main(
        root_path=Path(sys.argv[1]),
        runsheet_path=Path(sys.argv[2]),
        template="Bulk_RNASeq:PairedEnd",
        config_fs_f=sys.argv[3],
    )

