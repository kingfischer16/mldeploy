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
import pathlib
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import shutil
import sys
from typing import NoReturn, List, Union, Dict, Any


# =============================================================================
# Constants.
# -----------------------------------------------------------------------------
CURR_DIR = str(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_FOLDER = CURR_DIR + '/config_templates'
REG_FILE_NAME = '.registry.json'
DEFAULT_PROJECT_MODULES = [
    'boto3'
]
APP_DIR_ON_IMAGE = "app"
MSG_PREFIX = "\033[1;36;40m MLDeploy Message:: \033[m"
FAIL_PREFIX = "\033[1;31;40m MLDeploy Failure:: \033[m"
ACTION_PREFIX = "\033[1;33;40m MLDeploy Action Required:: \033[m"
PLATFORM = sys.platform


# =============================================================================
# Registry utilities.
# -----------------------------------------------------------------------------
def _get_appdata_folder() -> str:
    """
    Gets the folder location on the local machine where 'mldeploy'
    can store application-wide data, such as the '.registry.json'
    file.
    """
    user_home = pathlib.Path.home()
    if PLATFORM == "linux":
        appdata_folder = user_home / ".local/share"
    elif PLATFORM == "win32":
        appdata_folder = user_home / "AppData/Roaming"
    else:
        raise ValueError(f"Unknown operating system: {PLATFORM}")
    return str(appdata_folder) + "/mldeploy"


def _get_registry_path() -> str:
    """
    Returns the full file path of the 'mldeploy' registry file.
    """
    appdata_folder = _get_appdata_folder()
    return appdata_folder+'/'+REG_FILE_NAME


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
        raise ValueError(f"Project '{name}' not found in registry.")
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
# Docker image handling utilities.
# -----------------------------------------------------------------------------
def _delete_docker_image(name: str, deleting_project: bool=False) -> NoReturn:
    """
    Deletes the currently registered image from the local Docker
    engine. Custom images are not deleted, and built images are only
    deleted if replacement is set in the configuration file.

    Args:
        name (str): Project name.

        deleting_project (bool): Set to True to bypass the rebuild checks
         and delete the image when permanently deleting the project. Default
         is False which lets the checks happen.
    """
    # Get Docker image name.
    reg_data = _get_registry_data()
    config_data = _get_config_data(name)
    if 'docker-image' in reg_data[name].keys():
        reg_docker_image = reg_data[name]['docker-image']
    else:
        # Exit function if no registered docker image.
        return
    base_docker_image = config_data['base-image']

    if 'docker-image' in config_data.keys():
        custom_image = config_data['docker-image']
    else:
        custom_image = ''
    
    delete_existing = False
    # Check if this is part of removing a project.
    if deleting_project:
        if (reg_docker_image != base_docker_image) & (reg_docker_image != custom_image):
            delete_existing = True
        else:
            delete_existing = False
    else:
        # Check if image should be deleted: if rebuild is not allowed
        # or custom image is found.
        if 'replace-image-on-rebuild' in config_data.keys():
            delete_existing = config_data['replace-image-on-rebuild']
        else:
            delete_existing = False
        if (len(custom_image) > 0) | (custom_image == reg_docker_image):
            delete_existing = False
    
    # Execute delete if allowed.
    if delete_existing:
        client = docker.from_env()
        im_list = [im.tags[0] for im in client.images.list()]
        if reg_docker_image in im_list:
            client.images.remove(reg_docker_image)
            print(f"{MSG_PREFIX}Deleting existing project image: {reg_docker_image}")
        else:
            print(f"{FAIL_PREFIX}Project image '{reg_docker_image}' not found.")
    else:
        print(f"{MSG_PREFIX}Project image '{reg_docker_image}' was not deleted.")


# =============================================================================
# File handling utilities.
# -----------------------------------------------------------------------------
def _temp_copy_local_files(name: str) -> NoReturn:
    """
    Temporarily copies the files (ignores repos to clone) to the
    project folder /tmp directory. This must be done because the Docker
    build command uses only the relative path and cannot pull files from
    local root.

    Args:
        name (str): Project name.
    
    Raises:
        ValueError: If the object to copy is neither a file nor a directory.
    """
    # Get files to copy from the project's config file.
    conf_data = _get_config_data(name)
    if 'add-files' in conf_data.keys():
        if conf_data['add-files'] is not None:
            local_files = [f for f in conf_data['add-files'] if not f.endswith('.git')]
            # Project folder gets a tmp folder.
            dst = _get_project_folder(name)+'/tmp'
            if not os.path.exists(dst):
                os.mkdir(dst)
            for src_i in local_files:
                # Check if file or folder and copy appropriately.
                dst_i = dst + '/' + src_i.rsplit('/', 1)[1]
                if os.path.isdir(src_i):
                    shutil.copytree(src_i, dst_i)
                elif os.path.isfile(src_i):
                    shutil.copy(src_i, dst_i)
                else:
                    raise ValueError(f"{FAIL_PREFIX}Unknown object to copy: {src_i}")


def _remove_temp_files(name: str) -> NoReturn:
    """
    Delete everything in the /tmp folder of the project directory.
    
    Args:
        name (str): Project name.
    """
    temp_loc = _get_project_folder(name) + '/tmp'
    if os.path.exists(temp_loc):
        shutil.rmtree(temp_loc)


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

