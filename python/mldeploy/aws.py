# =============================================================================
# AWS.PY
# -----------------------------------------------------------------------------
# Functions used to interact with Amazon Web Services.
# 
# ***This file may only import from the 'utils' file.***
# 
#  
# The CLI is built using the following packages:
#   - boto3: Python SDK for AWS
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import boto3
from datetime import datetime
from typing import NoReturn
from .utils import _add_field_to_registry


# =============================================================================
# Architecture setup.
# -----------------------------------------------------------------------------
def _create_cloudformation_file(name: str) -> NoReturn:
    """
    Creates and registers a CloudFormation JSON file.

    Args:
        name (str): Name of the project to create the cloudformation file.
    """


def _create_stack_id(name: str) -> str:
    """
    Creates a stack name that should be unique within the region.

    Args:
        name (str): Name of the project for which to create the stack ID.
    
    Returns:
        (str): The generated stack name.
    """
    dt_string = datetime.now().strftime("%Y%m%d-%H%M%S")
    return name + '_' + dt_string
