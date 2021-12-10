# test flagging module including outputs to file and loading
import pandas as pd

from VV.flagging import Flag
from VV.checks import DummyCheck

dCheck = DummyCheck()
def test_flags_recorded():
    Flag.dump(purge_flags=True)
    flagTest = Flag(code=10, check=dCheck)
    
    assert len(Flag.allFlags) == 1

def test_dumped_tsv_is_reloadable(): 
    flagTest = Flag(code=10, check=dCheck, data={"random":1})
    flagTest = Flag(code=10, check=dCheck)
    flagTest = Flag(code=10, check=dCheck)

    original_df = Flag.to_df()
    output_path = Flag.dump(purge_flags=True)
    loaded_df = Flag.load(tsv_path=output_path)
    assert original_df == loaded_df
