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
import os
import sys
import shutil
import json
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pprint import pformat
from typing import NoReturn, Dict
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import fire  # The python-fire CLI engine.

from utils import (_get_registry_data, _get_project_folder,
    CURR_DIR, REG_FILE_NAME,
    MSG_PREFIX, FAIL_PREFIX, ACTION_PREFIX)
from startup import (_create_registry_file_if_not_exists, _add_project_to_registry,
    _create_new_project_folder, _copy_and_update_config, _create_requirements_file,
    _delete_project_folder_and_registry)
from docker_tools import _get_or_create_dockerfile


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
    reg_data = _get_registry_data()
    print(f"{MSG_PREFIX}Registered projects (project name --> location):")
    for p, loc in reg_data.items():
        print(f"\t{p} --> {loc['location']}")
    print(f"--- (End of list) ---")


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
    Builds the project's docker image from configuration files.

    Args:
        name (str): Name of the project to delete.
    """
    proj_name = os.getcwd().rsplit('/', 1)[1] if len(name)<=0 else name
    registerd_projects = list(_get_registry_data().keys())
    if proj_name not in registerd_projects:
        print(f"{FAIL_PREFIX}Project '' does not exist.")
        sys.exit()
    else:
        _get_or_create_dockerfile(proj_name)
    
    print(f"{MSG_PREFIX}Docker image built for project '{name}'.")


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
