""" Module that handles packaged yaml files and includes utility functions for exploring such files """
from pathlib import Path
import logging
from typing import List

import yaml

from gl4gl import PathAnnotate

__PACKAGED_CONFIG_DIR = Path(PathAnnotate.__path__[0], "configs")


def get_configs(configs_path: Path = __PACKAGED_CONFIG_DIR) -> [Path]:
    """Returns the a list of config files found in the supplied path.

    :param config_path: An optional path to search for config files, defaults to searching the packaged configs
    :type config_path: Path
    :return: The full path to the found config file
    :rtype: Path
    """
    logging.info(f"Recursively searching {configs_path} for *.yaml files.")

    return list(configs_path.rglob("*.yaml"))


def get_templates(config_fs_f: Path) -> List[str]:
    """Returns template keys present in the config file

    :param config_fs_f: A config file with search patterns
    :type config_fs_f: Path
    :return: The template names available in the config file
    :rtype: list[str]
    """
    with open(config_fs_f, "r") as f:
        config = yaml.safe_load(f)

    templates = list()
    for top_key, top_dict in config.items():
        for bottom_key, bottom_dict in top_dict.items():
            templates.append(f"{top_key}:{bottom_key}")

    return templates


def describe_config(config_fs_f: Path):
    """Print out a description of the config file

    :param config_fs_f: The full path to the config file to describe
    :type config_fs_f: Path
    """
    logging.info(f"Generating summary description for: {config_fs_f}")
    logging.warning(f"NOT IMPLEMENTED")
