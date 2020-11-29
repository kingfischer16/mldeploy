# =============================================================================
# MLDEPLOY.PY
# -----------------------------------------------------------------------------
# The main code file for the CLI.
# 
# ***This file MAY import from all other 'mldeploy' files.***
#  
# The CLI is built using the following packages:
#   - fire: Google-supported, turns functions into CLI
#   - ruamel.yaml: Edit YAML files without affecting the structure or comments.
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import fire  # The python-fire CLI engine.
import json
import os
from pprint import pformat
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import shutil
import sys
from typing import NoReturn, Dict

from docker_tools import _build_or_get_image
from cleanup import _delete_project_folder_and_registry
from utils import (
    _get_registry_data, _get_project_folder, _get_registry_lists,
    CURR_DIR, REG_FILE_NAME,
    MSG_PREFIX, FAIL_PREFIX, ACTION_PREFIX
)
from startup import (
    _create_registry_file_if_not_exists, _add_project_to_registry,
    _create_new_project_folder, _copy_and_update_config, _create_requirements_file
)


# =============================================================================
# CLI Functions - Commands to the user at the command line.
# -----------------------------------------------------------------------------
def test() -> str:
    """
    This is just a test of the CLI.

    Returns:
        (str): A test string.
    """
    return f"{MSG_PREFIX}This is a test. MLDeploy has installed successfully."


def cwd() -> str:
    """
    Returns the current working directory of the CLI code.
    """
    return f"{MSG_PREFIX}Current directory: {CURR_DIR}"


def ls() -> NoReturn:
    """
    Lists all projects controlled by the CLI.
    """
    reg_lists = _get_registry_lists()
    print(f"{MSG_PREFIX}Registered projects:\n")
    headers = list(reg_lists.keys())
    header_string = ''.join(headers)
    print(header_string)
    print('-'*len(header_string))
    for i in range(len(reg_lists[headers[0]])):
        proj_str = ''
        for k in headers:
            proj_str += reg_lists[k][i]
        print(proj_str)
    print(f"\n--- (End of list) ---\n")


def create(name: str = 'mldeploy_project', path: str = CURR_DIR) -> NoReturn:
    """
    Creates a new project, including project folder, configuration file,
    and project registry.

    Args:
        name (str): The project name, which will also be the name of the folder.

        path (str): Optional. The path to where the project contents shall reside.
    """
    path_dir = path + name if path.endswith('/') else path + '/' + name
    reg_data = _get_registry_data()
    if name in reg_data.keys():
        print(f"{FAIL_PREFIX}Cannot create project with name '{name}'. Project name already exists at location: '{reg_data[name]['location']}'")
        sys.exit()
    elif os.path.exists(path_dir):
        print(f"{FAIL_PREFIX}Cannot create project at specified path: {path_dir}. Folder already exists.")
    else:
        print(f"{MSG_PREFIX}Creating project '{name}'...")
        _create_registry_file_if_not_exists()
        _add_project_to_registry(project_path = path_dir)
        print(f"\tProject registered successfully.")
        _create_new_project_folder(name)
        print(f"\tProject folder created.")
        _copy_and_update_config(name)
        print(f"\tConfiguration file created.")
        _create_requirements_file(name)
        print(f"{MSG_PREFIX}Successfully created project '{name}' in '{path_dir}'")
        print(f"{ACTION_PREFIX}Edit configuration file '{_get_project_folder(name)+'/config.yml'}' to set deployment details.")


def delete(name: str) -> NoReturn:
    """
    Permanently deletes the local project files for the project.
    Note: this does not delete any project code outside of the 'mldeploy'
    project folder.

    Args:
        name (str): Name of the project to delete.
    """
    reg_data = _get_registry_data()
    if name not in reg_data.keys():
        print(f"{FAIL_PREFIX}Project with name '{name}' does not exist.")
    else:
        user_confirm = input(f"{ACTION_PREFIX}Confirm this action to PERMANENTLY delete the local project by typing the name again (or press <Enter> to cancel): ")
        if name == user_confirm:
            _delete_project_folder_and_registry(name)
            print(f"{MSG_PREFIX}Contents for project '{name}' has been deleted.")
        else:
            print(f"{FAIL_PREFIX}Delete operation for project '{name}' was not completed.")


def build(name: str = '') -> NoReturn:
    """
    Builds the project's Docker image from configuration files or uses
    user-defined Dockerfile or Docker image.

    Args:
        name (str): Name of the project to delete.
    """
    proj_name = os.getcwd().rsplit('/', 1)[1] if len(name)<=0 else name
    registerd_projects = list(_get_registry_data().keys())
    if proj_name not in registerd_projects:
        print(f"{FAIL_PREFIX}Project '' does not exist.")
        sys.exit()
    else:
        _build_or_get_image(proj_name)



# =============================================================================
# Main execution and function dictionary.
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    fire.Fire({
        'test': test,
        'cwd': cwd,
        'ls': ls,
        'create': create,
        'delete': delete,
        'build': build
    })
