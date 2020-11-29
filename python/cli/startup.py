# =============================================================================
# STARTUP.PY
# -----------------------------------------------------------------------------
# Code for the basic creation of the deployment project. Includes creation
# of project folder, new configuration file and new requirements.txt file.
# 
# ***This file MUST ONLY import from 'utils.py' for 'mldeploy' functions.***
#  
# The CLI is built using the following packages:
#   - ruamel.yaml: Edit YAML files without affecting the structure or comments.
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import json
import os
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import shutil
from typing import NoReturn

from utils import (_get_project_folder, _get_registry_data, _get_registry_path, _get_appdata_folder,
    CURR_DIR, DEFAULT_PROJECT_MODULES)


# =============================================================================
# Helper functions for project creation.
# -----------------------------------------------------------------------------
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
        if not os.path.exists(_get_appdata_folder()):
            os.makedirs(_get_appdata_folder())
        with open(_get_registry_path(), 'w') as f:
            json.dump(data, f)
        return


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
        raise ValueError(f"Project folder for '{name}' already exists.")
    else:
        print(_get_project_folder(name))
        os.makedirs(_get_project_folder(name))
    return

