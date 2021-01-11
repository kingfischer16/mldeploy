# =============================================================================
# MLDEPLOY_FUNCTIONS.PY
# -----------------------------------------------------------------------------
# Holds the functions that execute the commands in the CLI.
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
import os
import sys
from typing import NoReturn, Dict

from .aws import _deploy_stack
from .docker_tools import _build_or_get_image
from .cleanup import _delete_project
from .startup import (
    _create_registry_file_if_not_exists,
    _add_project_to_registry,
    _create_new_project_folder,
    _copy_and_update_config,
    _create_requirements_file,
    _copy_dockerignore,
)
from .utils import (
    _get_registry_data,
    _get_project_folder,
    _get_registry_lists,
    _get_appdata_folder,
    CURR_DIR,
    MSG_PREFIX,
    FAIL_PREFIX,
    ACTION_PREFIX,
)
from .aws import _add_cloudformation_template


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
    header_string = "".join(headers)
    print(header_string)
    print("-" * len(header_string))
    for i in range(len(reg_lists[headers[0]])):
        proj_str = ""
        for k in headers:
            proj_str += reg_lists[k][i]
        print(proj_str)
    print(f"\n--- (End of list) ---\n")


def create(name: str, path: str = _get_appdata_folder()) -> NoReturn:
    """
    Creates a new project, including project folder, configuration file,
    and project registry.

    Args:
        name (str): The project name, which will also be the
         name of the folder.

        path (str): Optional. The path to where the project contents
         shall reside. Default is the local application data folder.
    """
    path_dir = path + name if path.endswith("/") else path + "/" + name
    reg_data = _get_registry_data()
    if name in reg_data.keys():
        print(
            f"{FAIL_PREFIX}Cannot create project with name '{name}'. Project name already exists at location: '{reg_data[name]['location']}'"
        )
        sys.exit()
    elif os.path.exists(path_dir):
        print(
            f"{FAIL_PREFIX}Cannot create project at specified path: {path_dir}. Folder already exists."
        )
    else:
        print(f"{MSG_PREFIX}Creating project '{name}'...")
        _create_registry_file_if_not_exists()
        _add_project_to_registry(project_path=path_dir)
        print(f"\tProject registered successfully.")
        _create_new_project_folder(name)
        print(f"\tProject folder created.")
        _copy_and_update_config(name)
        _copy_dockerignore(name)
        print(f"\tConfiguration file created.")
        _create_requirements_file(name)
        print(f"{MSG_PREFIX}Successfully created project '{name}' in '{path_dir}'")
        print(
            f"{ACTION_PREFIX}Edit configuration file '{_get_project_folder(name)+'/config.yml'}' to set deployment details."
        )


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
        user_confirm = input(
            f"{ACTION_PREFIX}Confirm this action to PERMANENTLY delete the local project by typing the name again (or press <Enter> to cancel): "
        )
        if name == user_confirm:
            _delete_project(name)
            print(f"{MSG_PREFIX}Contents for project '{name}' has been deleted.")
        else:
            print(
                f"{FAIL_PREFIX}Delete operation for project '{name}' was not completed."
            )


def build(name: str = "") -> NoReturn:
    """
    Builds the project's Docker image from configuration files or uses
    user-defined Dockerfile or Docker image.

    Args:
        name (str): Name of the project to delete.
    """
    proj_name = os.getcwd().rsplit("/", 1)[1] if len(name) <= 0 else name
    registerd_projects = list(_get_registry_data().keys())
    if proj_name not in registerd_projects:
        print(f"{FAIL_PREFIX}Project '{proj_name}' does not exist.")
        sys.exit()
    else:
        _build_or_get_image(proj_name)
        _add_cloudformation_template(proj_name)
        print(f"{MSG_PREFIX}Project build successful.")


def deploy(name: str = "") -> NoReturn:
    """
    Deploys the specified project to cloud resources.

    Args:
        name (str): Name of the project to deploy.
    """
    proj_name = os.getcwd().rsplit("/", 1)[1] if len(name) <= 0 else name
    registerd_projects = list(_get_registry_data().keys())
    if proj_name not in registerd_projects:
        print(f"{FAIL_PREFIX}Project '{proj_name}' does not exist.")
        sys.exit()
    else:
        print(f"{MSG_PREFIX}***PROJECT DEPLOYING***")
        _deploy_stack(name)


def update(name: str = "") -> NoReturn:
    """
    Updates the specified project stack.

    Args:
        name (str): Name of the project to update.
    """
    proj_name = os.getcwd().rsplit("/", 1)[1] if len(name) <= 0 else name
    registerd_projects = list(_get_registry_data().keys())
    if proj_name not in registerd_projects:
        print(f"{FAIL_PREFIX}Project '{proj_name}' does not exist.")
        sys.exit()
    else:
        print(f"{MSG_PREFIX}***PROJECT UPDATE PLACEHOLDER***")
