# =============================================================================
# DOCKER.PY
# -----------------------------------------------------------------------------
# Code for handling the creation of the docker image for deployment.
# This code creates/updates a 'Dockerfile' and uses this to build.
# 
# ***This file MUST ONLY import from 'utils.py' for 'mldeploy' functions.***
#  
# The CLI is built using the following packages:
#   - docker: Constructs client for handling the docker-engine
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import os
import docker
from typing import NoReturn, List
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
from utils import (_get_project_folder, _get_config_data,
    APP_DIR_ON_IMAGE)


# =============================================================================
# Dockerfile creation.
# -----------------------------------------------------------------------------
def _get_or_create_dockerfile(name: str) -> NoReturn:
    """
    Gets and moves a custom Dockerfile if it exists, otherwise
    creates a Dockerfile from the configuration files in the
    project folder.

    Args:
        name (str): Project name.
    """
    user_dockerfile_found = _get_custom_dockerfile(name)
    if not user_dockerfile_found:
        _create_dockerfile(name)


def _create_dockerfile(name: str) -> NoReturn:
    """
    Creates a new Dockerfile for the project.
    """
    LEND = "\n"  # Line ender for Dockerfile.
    # List holding the Dockerfile lines in order.
    dockerfile_list = []
    code_paths = _get_code_paths(name)

    # Start building Dockerfile.
    dockerfile_list.append(f"FROM {_get_docker_image_name(name)}{LEND}")
    dockerfile_list.append(f"RUN apt-get update{LEND}")

    # Install Python.
    python_version = str(_get_config_data(name)['python-version'])
    dockerfile_list.append(f"RUN apt-get install -y python{python_version}{LEND}")

    # Create 'app' folder for application files.
    dockerfile_list.append(f"RUN mkdir -p {APP_DIR_ON_IMAGE}{LEND}")

    # Install Git only if needed.
    if len(code_paths) > 0:
        if any([c.endswith('.git') for c in code_paths]):
            dockerfile_list.append(f"RUN apt-get install -y git{LEND}")

    # Copy or clone user files.
    if len(code_paths) > 0:
        for code_file in code_paths:
            if code_file.endswith('.git'):
                dockerfile_list.append(f"RUN git clone {code_file} /{APP_DIR_ON_IMAGE}{LEND}")
            else:
                dockerfile_list.append(f"COPY {code_file} /{APP_DIR_ON_IMAGE}{LEND}")
    
    with open(_get_project_folder(name)+"/Dockerfile", 'w') as dfile:
        for line in dockerfile_list:
            dfile.write(line+LEND)


def _get_custom_dockerfile(name: str) -> bool:
    """
    Returns the path to a custom/user-defined Dockerfile if one has
    been provided and it exists. The Dockerfile will be copied to the
    project folder in place of a CLI created Dockerfile.
    
    Args:
        name (str): Poject name.
    
    Returns:
        (bool): True if a custom Dockerfile is found, False if none is found.
    """
    return False


def _build_docker_image(name: str) -> NoReturn:
    """
    Build the docker image from the information in the project
    folder.
    """


def _get_docker_image_name(name: str) -> str:
    """
    Get the name of the docker image to use for the project.

    Args:
        name (str): Project name.
    """
    yaml_obj = ryml.YAML()
    with open(_get_project_folder(name)+'/config.yml', 'r') as f:
        doc = yaml_obj.load(f)
    base_docker_image = doc['base-image']
    return base_docker_image


def _get_code_paths(name: str) -> List:
    """
    Returns the paths of the folders that must be copied or cloned
    into the image.
    """
    yaml_obj = ryml.YAML()
    with open(_get_project_folder(name)+'/config.yml', 'r') as f:
        doc = yaml_obj.load(f)
    file_list = doc['add-files'] if 'add-files' in doc.keys() else []
    if file_list is None:
        file_list = []
    else:
        file_list = [] if all([n is None for n in file_list]) else file_list
    return file_list
