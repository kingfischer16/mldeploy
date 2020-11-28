# =============================================================================
# UTILS.PY
# -----------------------------------------------------------------------------
# Common functions used by other files.
# 
# ***This file MUST NOT import from other 'mldeploy' files.***
# 
#  
# The CLI is built using the following packages:
#   - ruamel.yaml: Edit YAML files without affecting the structure or comments.
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import os
import json
import docker
from typing import NoReturn, List, Union, Dict
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.


# =============================================================================
# Constants.
# -----------------------------------------------------------------------------
CURR_DIR = os.getcwd()
REG_FILE_NAME = '.registry.json'
DEFAULT_PROJECT_MODULES = [
    'boto3'
]
APP_DIR_ON_IMAGE = "app"
MSG_PREFIX = "\033[1;36;40m MLDeploy Message:: \033[0;37;40m "
FAIL_PREFIX = "\033[1;31;40m MLDeploy Failure:: \033[0;37;40m "
ACTION_PREFIX = "\033[1;33;40m MLDeploy Action Required:: \033[0;37;40m "


# =============================================================================
# Registry utilities.
# -----------------------------------------------------------------------------
def _get_registry_path() -> str:
    """
    Returns the full file path of the 'mldeploy' registry file.
    """
    return CURR_DIR+'/'+REG_FILE_NAME


def _get_registry_data() -> Dict:
    """
    Returns the registry data as a Python dictionary.
    """
    try:
        with open(_get_registry_path(), 'r') as f:
            data = json.load(f)
    except:
        data = {}
    return data


# =============================================================================
# Project folder utilities.
# -----------------------------------------------------------------------------
def _get_project_folder(name: str) -> str:
    """
    Returns the full folder path of the named project.

    Args:
        name (str): The name of the project.
    """
    reg_data = _get_registry_data()
    return reg_data[name]['location']


# =============================================================================
# Configuration file utilities.
# -----------------------------------------------------------------------------
def _get_config_data(name: str) -> Dict:
    """
    Given the project name and the field name(s), returns a dictionary
    with the contents of the 'config.yml' file.

    Args:
        name (str): Project name.
    
    Returns:
        (dict): Contents of 'config.yml'.
    """
    yaml_obj = ryml.YAML()
    project_path = _get_project_folder(name)
    config_file = project_path+'/config.yml'
    with open(config_file, 'r') as f:
        doc = yaml_obj.load(f)
    return doc
