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
from .utils import _get_project_folder, APP_DIR_ON_IMAGE


# =============================================================================
# Dockerfile creation.
# -----------------------------------------------------------------------------
def _create_dockerfile(name: str) -> NoReturn:
    """
    Creates a new Dockerfile for the project.
    """
    # List holding the Dockerfile lines in order.
    dockerfile_list = []
    code_paths = _get_code_paths(name)

    # Start building Dockerfile.
    dockerfile_list.append(f"FROM {_get_docker_image_name(name)}")
    dockerfile_list.append(f"RUN apt-get update")
    dockerfile_list.append(f"RUN mkdir -p {APP_DIR_ON_IMAGE}")

    needs_git = any([c.endswith('.git') for c in code_paths])
    
    # Install Git only if needed.
    if needs_git: dockerfile_list.append(f"RUN apt-get install -y git")
    
    # Copy or clone user files.
    for code_file in code_paths:
        if code_file.endswith('.git'):
            dockerfile_list.append(f"RUN git clone {code_file}")
        else:
            dockerfile_list.append(f"COPY {code_file} /{APP_DIR_ON_IMAGE}")
    
    with open(_get_project_folder(name)+"/Dockerfile", 'w') as dfile:
        for line in dockerfile_list:
            dfile.write(line)


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
    
    return []
