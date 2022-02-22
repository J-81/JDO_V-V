import logging

from gl4gl.PathAnnotate import get_configs, describe_config, get_templates


def test_configs(caplog):
    caplog.set_level(logging.INFO)
    confs = get_configs()

    test_conf = [conf for conf in confs if conf.name == "Bulk_Search_Patterns.yaml"][0]

    assert test_conf.name == "Bulk_Search_Patterns.yaml"

    # describe_config(test_conf)

    assert get_templates(test_conf) == ["Bulk_RNASeq:PairedEnd"]
