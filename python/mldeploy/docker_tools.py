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
from datetime import datetime
import docker
import os
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import shutil
from typing import NoReturn, List, Iterator

from .utils import (
    _get_project_folder,
    _get_config_data,
    _add_field_to_registry,
    _get_registry_data,
    _delete_docker_image,
    _temp_copy_local_files,
    _remove_temp_files,
    _get_constant,
)


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

    Currently the base image should contain the Python language
    installation and the Dockerfile creation is used to add
    files and install Python packages.
    """
    print(
        f"{_get_constant('MSG_PREFIX')}Building Dockerfile from project configuration."
    )

    LEND = "\n"  # Line ender for Dockerfile.
    # List holding the Dockerfile lines in order.
    dockerfile_list = []
    code_paths = _get_code_paths(name)

    # Start building Dockerfile.
    dockerfile_list.append(f"FROM {_get_base_image_name(name)}{LEND}")
    dockerfile_list.append(f"RUN apt-get update{LEND}")

    # Create 'app' folder for application files.
    dockerfile_list.append(f"RUN mkdir -p {_get_constant('APP_DIR_ON_IMAGE')}{LEND}")

    # Install Git only if needed.
    if len(code_paths) > 0:
        if any([c.endswith(".git") for c in code_paths]):
            dockerfile_list.append(f"RUN apt-get install -y git{LEND}")

    # Copy 'requirements.txt' file and run.
    dockerfile_list.append(
        f"COPY requirements.txt /{_get_constant('APP_DIR_ON_IMAGE')}{LEND}"
    )
    dockerfile_list.append(
        f"RUN pip install -r /{_get_constant('APP_DIR_ON_IMAGE')}/requirements.txt"
    )

    # Copy or clone user files.
    if len(code_paths) > 0:
        for code_file in code_paths:
            if code_file.endswith(".git"):
                code_folder = code_file.rsplit("/", 1)[1].rsplit(".", 1)[0]
                dockerfile_list.append(
                    f"RUN git clone {code_file} ./{_get_constant('APP_DIR_ON_IMAGE')}/{code_folder} {LEND}"
                )
            else:
                code_folder = code_file.rsplit("/", 1)[1]
                dockerfile_list.append(
                    f"COPY /tmp/{code_file.rsplit('/', 1)[1]} ./{_get_constant('APP_DIR_ON_IMAGE')}/{code_folder}{LEND}"
                )

    with open(_get_project_folder(name) + "/Dockerfile", "w") as dfile:
        for line in dockerfile_list:
            dfile.write(line + LEND)

    # Register Dockerfile.
    _add_field_to_registry(
        name, "dockerfile", _get_project_folder(name) + "/Dockerfile"
    )


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
    # Find Dockerfile.
    data = _get_config_data(name)
    if "docker-file" in data.keys():
        docker_file_loc = data["docker-file"]
        if docker_file_loc is None:
            return False
        if not os.path.exists(docker_file_loc):
            return False
    else:
        return False

    # Copy Dockerfile to project folder.
    print(
        f"{_get_constant('MSG_PREFIX')}Copying user-defined Dockerfile to project folder."
    )
    proj_folder = _get_project_folder(name)
    shutil.copy(src=docker_file_loc, dst=proj_folder + "/Dockerfile")

    # Register Dockerfile.
    _add_field_to_registry(
        name, "dockerfile", _get_project_folder(name) + "/Dockerfile"
    )
    return True


# =============================================================================
# Docker image creation.
# -----------------------------------------------------------------------------
def _build_or_get_image(name: str) -> NoReturn:
    """
    Decides whether to get a user-defined Docker image or to
    build one from the registered Dockerfile.
    """
    conf_data = _get_config_data(name)
    if "docker-image" in conf_data.keys():
        image_name = conf_data["docker-image"]
        if image_name is not None:
            # Register Docker image.
            print(
                f"{_get_constant('MSG_PREFIX')}Using user-defined Docker image: {image_name}"
            )
            _add_field_to_registry(name, "docker-image", image_name)
            return
    _get_or_create_dockerfile(name)
    _build_docker_image(name)


def _build_docker_image(name: str) -> NoReturn:
    """
    Build the docker image from the information in the project
    folder.
    """
    print(f"{_get_constant('MSG_PREFIX')}Building Docker image from Dockerfile...")
    dockerfile_path = _get_registry_data()[name]["dockerfile"]
    # Clear temp files if any left from previous or failed build.
    _remove_temp_files(name)
    # Temporarily copy files to be transferred.
    _temp_copy_local_files(name)
    # Remove existing project image if allowed.
    _delete_docker_image(name)
    image_name = _generate_image_name(name)
    client = docker.from_env()
    d_image, logs = client.images.build(
        path=dockerfile_path.rsplit("/", 1)[0],
        # fileobj=dockerfile_path,
        tag=image_name,
        pull=True,
        rm=True,
        forcerm=True,
    )
    # Delete temporary files after successful build.
    _remove_temp_files(name)
    # Register Docker image.
    print(f"{_get_constant('MSG_PREFIX')}Docker image build succeeded: {image_name}")
    _add_field_to_registry(name, "docker-image", image_name)
    # Send logs to file.
    _save_build_logs_to_file(name, logs)


# =============================================================================
# Dockerfile helper functions.
# -----------------------------------------------------------------------------
def _get_base_image_name(name: str) -> str:
    """
    Get the name of the docker image to use for the project.

    Args:
        name (str): Project name.
    """
    yaml_obj = ryml.YAML()
    with open(_get_project_folder(name) + "/config.yml", "r") as f:
        doc = yaml_obj.load(f)
    base_docker_image = doc["base-image"]
    return base_docker_image


def _get_code_paths(name: str) -> List:
    """
    Returns the paths of the folders that must be copied or cloned
    into the image.
    """
    yaml_obj = ryml.YAML()
    with open(_get_project_folder(name) + "/config.yml", "r") as f:
        doc = yaml_obj.load(f)
    file_list = doc["add-files"] if "add-files" in doc.keys() else []
    if file_list is None:
        file_list = []
    else:
        file_list = [] if all([n is None for n in file_list]) else file_list
    return file_list


def _generate_image_name(name: str) -> str:
    """
    Generates a Docker image name from the project name. The naming
    convention uses datetime as follows:
        <project-name>_mldeploy:YYYYMMDD-HHMMSS

    Args:
        name (str): Project name.
    """
    dt_string = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{name}_mldeploy:{dt_string}"


# =============================================================================
# Docker logging.
# -----------------------------------------------------------------------------
def _save_build_logs_to_file(name: str, logs_iter: Iterator[str]) -> NoReturn:
    """
    Saves the docker build logs to a .txt file.

    Args:
        name (str): Project name.
    """
    # Setup file and folder names.
    log_filename = (
        name
        + _get_constant("DOCKER_LOG_FILE_TAG")
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".txt"
    )
    folder_location = (
        _get_project_folder(name) + "/" + _get_constant("DOCKER_LOG_FOLDER") + "/"
    )
    # Create folder if it does not exist.
    if not os.path.exists(folder_location):
        os.makedirs(folder_location)
    with open(folder_location + log_filename, "w") as f:
        for log in logs_iter:
            if "stream" in log:
                f.write(str(log["stream"]))
    print(
        f"{_get_constant('MSG_PREFIX')}View Docker build log: {folder_location}{log_filename}"
    )
