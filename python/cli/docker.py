# =============================================================================
# DOCKER.PY
# -----------------------------------------------------------------------------
# Code for handling the creation of the docker image for deployment.
# This code creates/updates a 'Dockerfile' and uses this to build.
# 
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
from .startup import _get_project_folder


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
    dockerfile_list.append(f"FROM {_get_docker_image_name(name)}")
    dockerfile_list.append(f"RUN apk update")
    dockerfile_list.append(f"RUN apk add git")
    


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
