""" This script generates the md5sum table excel file as well as a csv file containing all md5sum info """
import sys
import re
from pathlib import Path
import hashlib
from typing import List

import pandas as pd
from openpyxl.utils import get_column_letter

# from VV.file_search import path_annotate
from gl4gl.PathAnnotate import get_annotated_paths_df

MD5SUM_CACHE_FILE = Path("md5sum_cache.csv")


def __get_md5sum_on_file(file: Path, cache: dict) -> str:
    """ Generates the md5sum of a file
    Params:
        file: the file to generate an md5sum hash for
        cache: {fullpath:md5sum} cached md5sums to prevent unneeded recomputation
    """
    if (cached_md5sum := cache.get(str(file))) :
        print(f"Cache hit '{file}' : {cached_md5sum}")
        md5sum = cached_md5sum
    else:
        print(f"Generating md5sum for file:\t\t{file}")
        md5sum = hashlib.md5(file.open("rb").read()).hexdigest()
        cache[str(file)] = md5sum
    return md5sum


def __write_md5sum_excel(df: pd.DataFrame, output_file: Path) -> Path:
    """
    Params:
        df: the annotated dataframe to write an excel file with
        output_file: the path to the excel file
    Returns:
        Path denoting the newly written md5sum excel file
    """
    COLUMN_LENGTH_BUFFER = 8
    print(f"Generating file: {output_file}")

    # set up excel writer
    options = {}
    options["strings_to_formulas"] = False
    options["strings_to_urls"] = False
    writer = pd.ExcelWriter(output_file, engine="openpyxl", options=options)

    # filter and reformat for output
    # save all paths that don't end up in excel file for reference
    df.loc[df["md5sum Excel Sheet"].isnull()].to_csv("Unpublished_md5sum.csv")

    df = df.loc[
        ~df["md5sum Excel Sheet"].isnull()
    ]  # removes all files without a sheet target
    df["fileName"] = df["pathObj"].apply(lambda path: path.name)

    # use modified relative path to change 'processing_scripts_noPaths' to 'processing_scripts', this reflect final AWS locations
    df["filepath"] = df["relativePath"].str.replace(
        "processing_scripts_NOpaths", "processing_scripts"
    )

    # based on 'md5sum Excel Sheet' key
    for sheet in df["md5sum Excel Sheet"].unique():
        print(f"Working on sheet name: {sheet}")
        df_file_sheet = df.loc[df["md5sum Excel Sheet"] == sheet][
            ["filepath", "fileName", "md5sum"]
        ]
        df_file_sheet.to_excel(writer, sheet_name=sheet, index=False, header=True)
        # autoresize based on items
        worksheet = writer.sheets[sheet]
        for idx, col in enumerate(df_file_sheet.columns):
            max_len = (
                max((df_file_sheet[col].astype(str).map(len).max()), len(str(col)))
                + COLUMN_LENGTH_BUFFER
            )  # max of either longest column value or column header plus a buffer character
            print(f"AutoSpacing: {max_len} sheet:{sheet} col:{col}")
            worksheet.column_dimensions[get_column_letter(idx + 1)].width = max_len
        writer.save()


def __generate_dataframe(
    config_fs_f, runsheet, template, root_dir, cache, annotations_keys
):
    """ Generates annotated dataframe. Removes directories and generates md5sum hashs for all files
    Params:
        config_fs_f: the file search config yaml
        root_dir: top level directory for a dataset
        template: A string denoting the top two keys in the config file search yaml, these denote assay main technology and sub_technology. e.g. 'Bulk_RNASeq:PairedEnd'
        runsheet: metadata csv file that MUST contain a column 'sample_name' denoting the sample IDs
    """
    # create dataframe of annotated paths
    df = get_annotated_paths_df(
        config_fs_f=config_fs_f,
        runsheet=runsheet,
        template=template,
        root_dir=root_dir,
        expand_annotations=True,
        annotations_keys=annotations_keys,
    )

    # filter to just files
    df = df.loc[df["isDir"] == False]

    # generate md5sums for all files and store as a column
    df["md5sum"] = df["pathObj"].apply(__get_md5sum_on_file, args=[cache])

    # save cache
    with open(MD5SUM_CACHE_FILE, "w") as f:
        for key, value in cache.items():
            f.write(f"{key},{value}\n")

    return df


def general_excel(
    root_dir: Path,
    runsheet: Path,
    template: str,
    config_fs_f: Path,
    annotations_keys: List,
    outputDir: Path = None,
) -> Path:
    """
    Params:
        root_dir: top level directory for a dataset
        runsheet: metadata csv file that MUST contain a column 'sample_name' denoting the sample IDs
        template: A string denoting the top two keys in the config file search yaml, these denote assay main technology and sub_technology. e.g. 'Bulk_RNASeq:PairedEnd'
        config_fs_f: the file search config yaml
    """
    md5sum_table_file = Path(f"{root_dir.name}_md5sum_table.csv")

    if md5sum_table_file.exists():
        print(f"Found existing md5sum table: {md5sum_table_file}")
        df = pd.read_csv(md5sum_table_file)
        # ensure correct setting of this to Path
        df["pathObj"] = df["pathObj"].apply(lambda path_str: Path(path_str))
    else:
        print(f"Did not find  existing md5sum table: {md5sum_table_file}")
        # input("USER: Hit any key to continue generating md5sum table. Note: This will generate md5sum hashs and is computationally heavy")

        # load cache file if it exists
        cache = dict()
        if MD5SUM_CACHE_FILE.exists():
            print(f"Loading existing md5sum cache file: {MD5SUM_CACHE_FILE}")
            with open(MD5SUM_CACHE_FILE, "r") as f:
                for line in f.readlines():
                    fullPath, md5sum = line.split(",")
                    cache[fullPath] = md5sum.strip()  # remove newlines

        df = __generate_dataframe(
            config_fs_f=config_fs_f,
            runsheet=runsheet,
            template=template,
            root_dir=root_dir,
            cache=cache,
            annotations_keys=annotations_keys,
        )

        # save this table to csv,
        # since md5sum is the expensive operation this file
        # can be used to generate the excel file without rehashing
        print(f"Writing: {md5sum_table_file}")
        df.to_csv(md5sum_table_file)

    # write to excel file
    #   the relative filepath, filename and md5sum
    #   locate in proper sheet using 'Excel sheet' annotation
    excel_output_file = md5sum_table_file.with_suffix(".xlsx")
    __write_md5sum_excel(df, output_file=excel_output_file)
    return Path(excel_output_file)


if __name__ == "__main__":
    general_excel(
        root_dir=Path(sys.argv[1]),
        runsheet=Path(sys.argv[2]),
        template="Bulk_RNASeq:PairedEnd",
        config_fs_f=sys.argv[3],
    )

