from pathlib import Path
import logging
# load module specific logger
log = logging.getLogger(__name__)

from gl4gl import VnV

__PACKAGED_CONFIG_DIR = Path(VnV.__path__[0], "configs")


def get_configs(configs_path: Path = __PACKAGED_CONFIG_DIR) -> [Path]:
    """Returns the a list of config files found in the supplied path.

    :param config_path: An optional path to search for config files, defaults to searching the packaged configs
    :type config_path: Path
    :return: The full path to the found config file
    :rtype: Path
    """
    log.info(f"Recursively searching {configs_path} for *.yaml files.")

    return list(configs_path.rglob("*.yaml"))