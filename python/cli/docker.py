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
from typing import NoReturn
from startup import _get_project_folder


# =============================================================================
# Dockerfile creation.
# -----------------------------------------------------------------------------
def _create_dockerfile(name: str) -> NoReturn:
    """
    Creates a new Dockerfile for the project.
    """