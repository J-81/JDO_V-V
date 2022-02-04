import os
from pathlib import Path

from VV.file_search import path_annotate, get_listing

from VV import generate_publish_to_repo_excel, generate_md5sum_table
from VV.generate_md5sum_table import get_md5sum_on_file

try:
    TEST_ASSETS_DIR = os.environ["PTW_TEST_ASSETS"]
except KeyError as e:
    print("PTW user needs to set env variable: 'PTW_TEST_ASSETS' to indicate where test assets are stored")
    raise e

'''
def test_get_listing():
    """ Function to get a dataframe of all files and directories in a root directory """
    target_dir = Path(f"{TEST_ASSETS_DIR}/GLDS-123")
    df_listing = get_listing(target_dir)
    
    assert len(df_listing) == 26
    assert set(df_listing.columns) == {'fullPath','relativePath','annotations','pathObj','isDir'}

def test_GLDS_194():
    config_fs_f = "/global/scratch/joribell/local_repos/JDO_V-V/VV/RNASeq/Bulk_PI_Search_Patterns.yaml" 
    runsheet = Path(f"{TEST_ASSETS_DIR}/GLDS-194/Metadata/AST_autogen_template_RNASeq_RCP_GLDS-194_RNASeq_runsheet.csv")
    root_dir = Path(f"{TEST_ASSETS_DIR}/GLDS-194") 

    result = path_annotate(config_fs_f, runsheet, template='Bulk_RNASeq:PairedEnd', root_dir=root_dir)
    
    assert len(result) == 657
    assert set(result.columns) == {'annotations', 'pathObj', 'Excel Column', 'relativePath', 'Excel File', 'isDir', 'Excel Sheet', 'fullPath', 'search_pattern'}
'''
def test_generate_publish_to_repo_excel():
    config_fs_f = "/global/scratch/joribell/local_repos/JDO_V-V/VV/RNASeq/Bulk_PI_Search_Patterns.yaml" 
    runsheet = Path(f"/global/scratch/joribell/IyerMhatre_metadata.csv")
    root_dir = Path(f"{TEST_ASSETS_DIR}/IyerMhatre_FF_20211124") 

    result = generate_publish_to_repo_excel.main(root_dir, runsheet, template="Bulk_RNASeq:PairedEnd", config_fs_f=config_fs_f)
    # TODO: Fix assets

def test_generate_md5sum():
    test_file = Path(f"/global/scratch/joribell/IyerMhatre_metadata.csv")
    
    result = get_md5sum_on_file(test_file)
    assert result == "a0a74991e35eb277a0bb196e28786a4b"
    

def test_generate_md5sum_excel():
    config_fs_f = "/global/scratch/joribell/local_repos/JDO_V-V/VV/RNASeq/Bulk_PI_Search_Patterns.yaml" 
    runsheet = Path(f"/global/scratch/joribell/IyerMhatre_metadata.csv")
    root_dir = Path(f"{TEST_ASSETS_DIR}/IyerMhatre_FF_20211124") 

    result = generate_md5sum_table.main(root_dir, runsheet, template="Bulk_RNASeq:PairedEnd", config_fs_f=config_fs_f)



def test_GLDS_123():
    ...

def test_GLDS_1():
    ...

def test_GLDS_205():
    ...

def test_GLDS_271():
    ...

def test_GLDS_22():
    ...

def test_GLDS_28():
    ...
