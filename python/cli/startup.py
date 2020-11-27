# =============================================================================
# STARTUP.PY
# -----------------------------------------------------------------------------
# Code for the basic creation of the deployment project. Includes creation
# of project folder, new configuration file and new requirements.txt file.
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
import sys
import shutil
import json
from typing import NoReturn, Dict
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.


# =============================================================================
# Constants.
# -----------------------------------------------------------------------------
CURR_DIR = os.getcwd()
REG_FILE_NAME = '.registry.json'
DEFAULT_PROJECT_MODULES = [
    'boto3'
]


# =============================================================================
# Helper functions for project creation.
# -----------------------------------------------------------------------------
def _get_registry_path() -> str:
    """
    Returns the full file path of the 'mldeploy' registry file.
    """
    return CURR_DIR+'/'+REG_FILE_NAME


def _create_registry_file_if_not_exists() -> NoReturn:
    """
    Creates a registry file in the central code location. Registry file
    is used to track the existence of projects on the local machine, as
    well as remember what is deployed and how.
    """
    if os.path.exists(_get_registry_path()):
        return
    else:
        data = {}
        with open(_get_registry_path(), 'w') as f:
            json.dump(data, f)
        return


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


def _add_project_to_registry(project_path: str) -> NoReturn:
    """
    Adds a new project entry to the registry file.

    Args:
        project_path (str): The path (including folder name) where
         the project will be located.
    """
    project_name = project_path.rsplit('/', 1)[1]
    data = _get_registry_data()
    data.update({f"{project_name}": {"location": project_path}})
    with open(_get_registry_path(), 'w') as f:
        json.dump(data, f)


def _delete_project_from_registry(name: str) -> NoReturn:
    """
    Deletes a project entry from the registry file.

    Args:
        name (str): The name of the project.
    """
    data = _get_registry_data()
    data.pop(name, None)
    with open(_get_registry_path(), 'w') as f:
        json.dump(data, f)


def _copy_and_update_config(name: str) -> NoReturn:
    """
    Copies and updates the YAML configuration file, customizing
    it for the new project.

    Args:
        name (str): The name of the project.
    """
    yaml_obj = ryml.YAML()
    project_path = _get_project_folder(name)
    config_file = project_path+'/config.yml'
    shutil.copy(src=CURR_DIR+'/default_config.yml', dst=config_file)
    with open(config_file, 'r') as f:
        doc = yaml_obj.load(f)
    doc['project-name'] = name
    with open(config_file, 'w') as f:
        yaml_obj.dump(doc, f)
    return


def _create_requirements_file(name: str) -> NoReturn:
    """
    Creates a new requirements file for the project.

    Args:
        name (str): The name of the project.
    """
    reqs_file_path = _get_project_folder(name)+'/requirements.txt'
    if not os.path.exists(reqs_file_path):
        print("\tCreating 'requirements.txt' file for project.")
        with open(reqs_file_path, 'w') as f:
            for module in DEFAULT_PROJECT_MODULES:
                f.write(module+"\n")


def _create_new_project_folder(name: str) -> NoReturn:
    """
    Creates a new project folder.

    Args:
        name (str): The name of the project.
    """
    if os.path.exists(_get_project_folder(name)):
        print(f"Folder for project '{name}' already exists: '{_get_project_folder(name)}'")
        _delete_project_from_registry(name)
        sys.exit()
    else:
        print(_get_project_folder(name))
        os.makedirs(_get_project_folder(name))
    return


def _get_project_folder(name: str) -> str:
    """
    Returns the full folder path of the named project.

    Args:
        name (str): The name of the project.
    """
    reg_data = _get_registry_data()
    return reg_data[name]['location']


def _delete_project_folder_and_registry(name: str) -> NoReturn:
    """
    Permanently deletes the project folder and registry.

    Args:
        name (str): The name of the project.
    """
    if os.path.exists(_get_project_folder(name)):
        shutil.rmtree(_get_project_folder(name))
    _delete_project_from_registry(name)
