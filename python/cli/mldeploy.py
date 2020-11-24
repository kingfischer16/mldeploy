# =============================================================================
# MLDEPLOY_APP.PY
# -----------------------------------------------------------------------------
# The main code file for the CLI.
# 
#  
# The CLI is built using the following packages:
#   - fire: Google-supported, turns functions into CLI
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


# =============================================================================
# Constants.
# -----------------------------------------------------------------------------
CURR_DIR = os.getcwd()
REG_FILE_NAME = '.registry.json'


# =============================================================================
# CLI Functions - Commands to the user at the command line.
# -----------------------------------------------------------------------------
def test() -> str:
    """
    This is just a test of the CLI.

    Returns:
        (str): A test string.
    """
    return "This is a test. MLDeploy has installed successfully."

def cwd() -> str:
    """
    Returns the current working directory of the CLI code.
    """
    return f"Current directory: {CURR_DIR}"

def ls() -> NoReturn:
    """
    Lists all projects controlled by the CLI.
    """
    reg_data = _get_registry_data()
    print(f"Registered projects:\n\t(project name --> location)")
    for p, loc in reg_data.items():
        print(f"\t{p} --> {loc['location']}")
    print(highlight(pformat("--- (End of list) ---"), PythonLexer(), Terminal256Formatter()))

def create(name: str = 'mldeploy_project', path: str = CURR_DIR) -> NoReturn:
    """
    Creates a new project, including project folder, configuration file,
    and project registry.

    Args:
        name (str): The project name, which will also be the name of the folder.
        path (str): Optional. The path to where the project contents shall reside.
    """
    path_dir = path + '/' + name
    reg_data = _get_registry_data()
    if name in reg_data.keys():
        print(f"Cannot create project with name '{name}'. Project name already exists at location: '{reg_data[name]['location']}'")
    else:
        print(f"Creating project '{name}'...")
        _create_registry_file_if_not_exists()
        _add_project_to_registry(project_path = path_dir)
        print(f"\tProject registered successfully.")
        _create_new_project_folder(name)
        print(f"\tProject folder created.")
        _copy_and_update_config(name)
        print(f"\tConfiguration file created.")
        print(f"Successfully created project '{name}' in '{path_dir}'")


def delete(name: str) -> NoReturn:
    """
    Permanently deletes the local project files for the project.
    Note: this does not delete any project code outside of the 'mldeploy'
    project folder.

    Args:
        name (str): Name of the project to delete.
    """
    reg_path = CURR_DIR+'/'+REG_FILE_NAME
    with open(reg_path, 'r') as f:
        reg_data = json.load(f)
    if name not in reg_data.keys():
        print(f"Project with name '{name}' does not exist.")
    else:
        user_confirm = input("Confirm this action to PERMANENTLY delete the local project by typing the name again (or press <Enter> to cancel): ")
        if name == user_confirm:
            _delete_project_folder_and_registry(name)
            print(f"Contents for project '{name}' has been deleted.")
        else:
            print(f"Delete operation for project '{name}' has been aborted.")


# =============================================================================
# Hidden helper functions.
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
        os.mkdir(_get_project_folder(name))
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



# =============================================================================
# Main execution and function dictionary.
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    fire.Fire({
        'test': test,
        'cwd': cwd,
        'ls': ls,
        'create': create,
        'delete': delete
    })
