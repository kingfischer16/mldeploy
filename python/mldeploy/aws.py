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
import json
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import os
from typing import NoReturn, Dict
from .utils import (
    _add_field_to_registry,
    _get_field_if_exists,
    _add_field_to_registry,
    _add_salt,
    _get_constant,
)


# =============================================================================
# CloudFormation template creation function, top level.
# -----------------------------------------------------------------------------
def _add_cloudformation_template(name: str) -> NoReturn:
    """
    Adds the CloudFormation template to the configuration folder.

    This function should be called during the build phase.

    Args:
        name (str): Name of the project to create the cloudformation file.
    """
    _create_cloudformation_file(name)
    _add_project_s3_bucket(name)
    _add_ec2_instance(name)


# =============================================================================
# Architecture setup.
# -----------------------------------------------------------------------------
def _create_cloudformation_file(name: str) -> NoReturn:
    """
    Creates and registers a CloudFormation JSON file.

    Args:
        name (str): Name of the project to create the cloudformation file.

    Raises:
        FileExistsError: If the CloudFormation template already exists.
         To prevent overwriting.
    """
    proj_folder = _get_field_if_exists(name, _get_constant("PROJ_FOLDER_KEY"))
    cf_filename = proj_folder + "/" + _get_constant("CLOUDFORMATION_FILE_NAME")
    if os.path.exists(cf_filename):
        raise FileExistsError(
            f"A CloudFormation template already exists at the location: {cf_filename}"
        )
    template_desc = f"CloudFormation template generated by MLDEPLOY for {name} project."
    file_contents = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": template_desc,
        "Resources": {},
        "Parameters": {},
        "Mappings": {},
        "Metadata": {},
    }
    yaml_obj = ryml.YAML()
    with open(cf_filename, "w") as f:
        yaml_obj.dump(file_contents, f)
    # Register the CloudFormation template file in the registry.
    _add_field_to_registry(
        name, _get_constant("CLOUDFORMATION_LOCATION_KEY"), cf_filename
    )
    # Register a project hash, for ensuring


def _create_stack_id(name: str) -> str:
    """
    Creates a stack name that should be unique within the region.

    Args:
        name (str): Name of the project for which to create the stack ID.

    Returns:
        (str): The generated stack name.
    """
    dt_string = datetime.now().strftime("%Y%m%d-%H%M%S")
    return name + "_" + dt_string


def _add_project_s3_bucket(name: str) -> NoReturn:
    """
    Adds a project bucket to the CloudFormation file with the naming
    convention:
        mldeploy_store_<project name>_<date>

    Args:
        name (str): Name of the project for which to create the bucket.
    """
    cf_data = _get_cloudformation_template_data(name)
    cf_data["Resources"][f"{_get_constant('S3_STORE_PREF')}{name}"] = {
        "Type": "AWS::S3::Bucket",
        "Properties": {
            "BucketName": f"{name}-store-{_get_field_if_exists(name, _get_constant('SALT_KEY'))}"
        },
    }
    _update_cloudformation_template_data(name, cf_data)


def _add_ec2_instance(name: str) -> NoReturn:
    """
    Sample function. Adds EC2 instance.
    """
    cf_data = _get_cloudformation_template_data(name)
    cf_data["Resources"][f"EC2{name}01"] = {
        "Type": "AWS::EC2::Instance",
        "Properties": {
            "InstanceType": "t3.micro",
            "ImageId": "ami-02cb52d7ba9887a93",
            "AvailabilityZone": "eu-north-1a",
        },
    }
    _update_cloudformation_template_data(name, cf_data)


# =============================================================================
# CloudFormation template manipulations.
# -----------------------------------------------------------------------------
def _get_cloudformation_template_data(name: str) -> Dict:
    """
    Returns the contents of the CloudFormation template file
    as a Python dictionary.

    Args:
        name (str): The project name.

    Returns:
        (dict): The contents of the JSON file as a dictionary.

    Raises:
        FileNotFoundError: If the project does not have an associated
         CloudFormation temppate in the registry.

        FileNotFoundError: If the CloudFormation template is registered but cannot be found.
    """
    cf_filepath = _get_field_if_exists(
        name, _get_constant("CLOUDFORMATION_LOCATION_KEY")
    )
    if cf_filepath == "(None)":
        raise FileNotFoundError(
            f"No CloudFormation template registered for project '{name}'."
        )
    if not os.path.exists(cf_filepath):
        raise FileNotFoundError(
            f"Registered CloudFormation tempalate for project '{name}' cannot be found at it's registered location: {cf_filepath}"
        )
    yaml_obj = ryml.YAML()
    with open(cf_filepath, "r") as f:
        data = yaml_obj.load(f)
    return data


def _update_cloudformation_template_data(name: str, data: Dict) -> NoReturn:
    """
    Given the name of the project and the Python dictionary of updated contents,
    this function writes the data to the registered JSON CloudFormation template
    file path for the specified project.

    Note that this function will overwrite whatever is there with the entire new
    dictionary, so this function should be used in conjunction with
    '_get_cloudformation_template_data' to first pull in the current data in
    the template, modify it, then push it.

    Args:
        name (str): Project name.

        data (dict): The data dictionary to use to update the template.
    """
    cf_filepath = _get_field_if_exists(
        name, _get_constant("CLOUDFORMATION_LOCATION_KEY")
    )
    yaml_obj = ryml.YAML()
    with open(cf_filepath, "w") as f:
        yaml_obj.dump(data, f)


# =============================================================================
# Deployment control.
# -----------------------------------------------------------------------------
def _deploy_stack(name: str) -> NoReturn:
    """
    Deploys the stack to AWS for the given project using CloudFormation.

    Args:
        name (str): The project name.
    """
    deployed_status = _get_field_if_exists(name, _get_constant("DEPLOY_STATUS_KEY"))
    if deployed_status == _get_constant("STATUS_DEPLOYED"):
        print(
            f"{_get_constant('FAIL_PREFIX')}Deployment failed for project '{name}. A stack is already deployed for this project."
        )
        return
    # Create stack name.
    stack_name = (
        f"{name}-mldeploy-{_get_field_if_exists(name, _get_constant('SALT_KEY'))}"
    )
    # Get template.
    yaml_obj = ryml.YAML()
    cf_filepath = _get_field_if_exists(
        name, _get_constant("CLOUDFORMATION_LOCATION_KEY")
    )
    with open(cf_filepath, "r") as f:
        cf_template_yaml = yaml_obj.load(f)
    cf_template = json.dumps(cf_template_yaml)
    # Create client.
    client = boto3.client("cloudformation")
    # Create stack.
    d_stack_id = client.create_stack(StackName=stack_name, TemplateBody=cf_template)
    stack_id = d_stack_id["StackId"]
    print(
        f"{_get_constant('MSG_PREFIX')}Deployment created successfully for project '{name}'.\n\tStack ID: {stack_id}"
    )
    # Register stack.
    _register_deployment(name, stack_name, stack_id, deployed=True)


def _undeploy_stack(name: str) -> NoReturn:
    """
    Removes a deployed stack from AWS CloudFormation.

    Args:
        name (str): The project name.
    """
    deployed_status = _get_field_if_exists(name, _get_constant("DEPLOY_STATUS_KEY"))
    if deployed_status == _get_constant("STATUS_NOT_DEPLOYED"):
        print(
            f"{_get_constant('FAIL_PREFIX')}Undeploy action failed for project '{name}. Project has no stack deployed."
        )
        return
    # Create stack name.
    stack_name = _get_field_if_exists(name, _get_constant("STACK_NAME_KEY"))
    # Create client.
    client = boto3.client("cloudformation")
    # Create stack.
    client.delete_stack(StackName=stack_name)
    print(f"{_get_constant('MSG_PREFIX')}Stack removed for project '{name}'.")
    # Register stack.
    _register_deployment(name, "", "", deployed=False)


def _register_deployment(
    name: str, stack_name: str, stack_id: str, deployed: bool
) -> NoReturn:
    """
    Registers or deregisteres the stack ID of the deployment in
    the project registry and sets the 'deployment_status' of the project.

    Args:
        name (str): The project name.

        stack_name (str): The name of the CloudFormation stack to register.

        stack_id (str): The CloudFormation ID of the deployed stack.

        deployed (bool): Set True if stack is deployed and being registered,
         set False if the stack is being removed and being deregistered.
    """
    _add_field_to_registry(name, _get_constant("STACK_NAME_KEY"), stack_name)
    _add_field_to_registry(name, _get_constant("STACK_ID_KEY"), stack_id)
    deploy_status = (
        _get_constant("STATUS_DEPLOYED")
        if deployed
        else _get_constant("STATUS_NOT_DEPLOYED")
    )
    _add_field_to_registry(name, _get_constant("DEPLOY_STATUS_KEY"), deploy_status)
