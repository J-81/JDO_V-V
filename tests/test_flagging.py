# test flagging module including outputs to file and loading
import pandas as pd

from VV.flagging import Flag
from VV.checks import DummyCheck

dCheck = DummyCheck()
def test_flags_recorded():
    Flag.dump(purge_flags=True)
    flagTest = Flag(code=10, check=dCheck)
    
    assert len(Flag.allFlags) == 1

    Flag.dump(purge_flags=True)
    for i in range(10):
        flagTest = Flag(code=10, check=dCheck)
    assert len(Flag.allFlags) == 10

  
def test_dumped_tsv(): 
    Flag.dump(purge_flags=True)
    flagTest = Flag(code=10, check=dCheck, data={"random":1})
    flagTest = Flag(code=105, check=dCheck, data={'filter_value':100})
    flagTest = Flag(code=10, check=dCheck, data={'filter_value':1, 'random':2})
    flagTest = Flag(code=10, check=dCheck, data={'filter_value':100, 'random':2})

    original_df = Flag.to_df()
    output_path = Flag.dump()
    assert len(original_df) == 4
    assert output_path == "DEFAULT_VV_LOG.tsv"
    with open(output_path, "r") as f:
        lines = f.readlines()
    
    for line in lines:
        print(line.split('\t'))
    
    assert original_df.iloc[1]["severity"] == 105

    df = Flag.to_df(data_to_column = ['filter_value'])
    assert len(df.loc[df["filter_value"] == 100]) == 2
    # check column order is consistent
    assert list(df.columns) == ['sample', 'sub_entity', 'severity', 'flag_id', 'step', 'script', 'user_message', 'debug_message', 'check_id', 'data', 'filter_value']
    
    assert lines[-1].split('\t') == ['none supplied', 'none supplied', '10', '10', 'No Step Defined', 'No Step Defined', 'No Message Supplied', 'No Message Supplied', 'DUMMY_000C', "{'filter_value': 100, 'random': 2}\n"] 

def test_dump_in_append_mode():
    output_path = Flag.dump(append=False)
    with open(output_path, "r") as f:
        original_report_len = len(f.readlines())

    output_path = Flag.dump(append=True)
    with open(output_path, "r") as f:
        appended_report_len = len(f.readlines())

    assert original_report_len == 10
    assert appended_report_len == 20


