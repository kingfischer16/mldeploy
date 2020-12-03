# =============================================================================
# CLEANUP.PY
# -----------------------------------------------------------------------------
# Code for stopping, removing, and deleting a 'mldeploy' project.
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
import shutil
from typing import NoReturn

from .utils import (_get_registry_data, _get_registry_path, _get_project_folder,
    _delete_docker_image)


# =============================================================================
# Cleanup functions.
# -----------------------------------------------------------------------------
def _delete_project(name: str) -> NoReturn:
    """
    Permanently deletes all components of a project.

    Args:
        name (str): Project name.
    """
    _delete_docker_image(name, deleting_project=True)
    _delete_project_folder_and_registry(name)
    

def _delete_project_folder_and_registry(name: str) -> NoReturn:
    """
    Permanently deletes the project folder and registry.

    Args:
        name (str): The name of the project.
    """
    if os.path.exists(_get_project_folder(name)):
        shutil.rmtree(_get_project_folder(name))
    _delete_project_from_registry(name)


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
