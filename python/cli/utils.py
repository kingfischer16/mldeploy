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
from collections import OrderedDict
import docker
import json
import os
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import sys
from typing import NoReturn, List, Union, Dict


# =============================================================================
# Constants.
# -----------------------------------------------------------------------------
CURR_DIR = os.getcwd()
REG_FILE_NAME = '.registry.json'
DEFAULT_PROJECT_MODULES = [
    'boto3'
]
APP_DIR_ON_IMAGE = "app"
MSG_PREFIX = "\033[1;36;40m MLDeploy Message:: \033[m"
FAIL_PREFIX = "\033[1;31;40m MLDeploy Failure:: \033[m"
ACTION_PREFIX = "\033[1;33;40m MLDeploy Action Required:: \033[m"


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


def _add_field_to_registry(name: str, field_name: str,
    contents: str) -> NoReturn:
    """
    Adds or updates a field to the '.registry.json' file for
    the specified project.

    Args:
        name (str): Project name.

        field_name (str): The name of the field to add or update.

        contents (str): The value field to add or update in the registry.
    """
    reg_data = _get_registry_data()
    if name not in reg_data.keys():
        print(f"{FAIL_PREFIX}Project '{name}' not found in registry.")
        sys.exit()
    reg_data[name][field_name] = contents
    with open(_get_registry_path(), 'w') as f:
        json.dump(reg_data, f)
    


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


# =============================================================================
# Display utilities.
# -----------------------------------------------------------------------------
def _get_field_if_exists(name: str, field: str) -> str:
    """
    Returns the contents of the field if it exists, otherwise returns
    a string '(None)'

    Args:
        name (str): Project name.

        field (str): Field name to get.
    
    Returns:
        (str): The contents of the field, or '(None)'.
    """
    reg_data = _get_registry_data()
    if name not in reg_data.keys():
        raise ValueError(f"Project '{name}' not found in registry.")
    contents = "(None)"
    if field in reg_data[name].keys():
        contents = reg_data[name][field]
    return contents


def _get_registry_lists() -> Dict:
    """
    Returns a dictionary with lists of field contents from
    the registry.
    """
    fnames = {
        'name': 'Project Name',
        'folder': 'Project Folder',
        'image': 'Docker Image'
    }
    d_reg = OrderedDict()
    d_reg[fnames['name']] = []
    d_reg[fnames['folder']] = []
    d_reg[fnames['image']] = []
    
    # Build project field list.
    project_names = list(_get_registry_data().keys())
    for pname in project_names:
        d_reg[fnames['name']].append(pname)
        d_reg[fnames['folder']].append(_get_field_if_exists(pname, 'location'))
        d_reg[fnames['image']].append(_get_field_if_exists(pname, 'docker-image'))
    
    # Pad strings.
    d_flen = { k:0 for k in d_reg.keys()}
    d_output = OrderedDict()
    for k in d_reg.keys():
        d_flen[k] = max([len(s) for s in [k]+d_reg[k]]) + 3
        d_reg[k] = [s.ljust(d_flen[k]) for s in d_reg[k]]
        d_output[k.ljust(d_flen[k])] = d_reg[k]
    
    return d_output

