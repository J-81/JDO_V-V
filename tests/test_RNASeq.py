from VV import RNASeq_VV
from VV.utils import load_config, load_params
from VV import parameters

def test_RNASeq_VV():
    """ Checks that expected number of flags against test dataset
    is raised.
    """
    config = load_config(["config/python/test.config"])
    params = load_params(parameter_set = "DEFAULT")
    flagger = RNASeq_VV.main(config, params)
    assert flagger._flag_count == 851
