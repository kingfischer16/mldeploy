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
from .utils import _add_field_to_registry


# =============================================================================
# Architecture setup.
# -----------------------------------------------------------------------------
def _create_cloudformation_file(name: str) -> NoReturn:
    """
    Creates and registers