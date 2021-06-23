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
import io
import json
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
import os
from typing import NoReturn, Dict
from .utils import (
    _add_field_to_registry,
    _get_field_if_exists,
    _add_field_to_registry,
    _get_project_folder,
    _add_salt,
    _get_constant,
)

# =============================================================================
# Deployment control.
# -----------------------------------------------------------------------------
def _deploy_stack(name: str) -> NoReturn:
    """
    Deploys the stack to AWS for the given project using CloudFormation.

    Deploying the stack should consist of:
        - creating the temporary S3 bucket for template upload
        - upload docker image (stage 2)
        - uploading the template files
        - get parameters from config: S3 data bucket, cluster size, EC2 type,
        - create the master stack
        - wait for the stack creation to finish --> "waiter"
        - register: queue url, api key, api key
        - remove temporary S3 bucket (if not being used for docker repo)

    Args:
        name (str): The project name.
    """
    deployed_status = _get_field_if_exists(name, _get_constant("DEPLOY_STATUS_KEY"))
    if deployed_status == _get_constant("STATUS_DEPLOYED"):
        print(
            f"{_get_constant('FAIL_PREFIX')}Deployment failed for project '{name}. A stack is already deployed for this project."
        )
        return
    # Prepare parameters for stack creation.
    master_stack_name = f"mldeploy-{name}"
    s3_stack_name, s3_bucket_name = _deploy_s3_bucket(name)

    # Get parameters from config file.

    # Create
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


# =============================================================================
# Deployment subfunctions.
# -----------------------------------------------------------------------------
def _deploy_s3_bucket(name: str) -> str:
    """
    Deploys a S3 bucket to contain the templates for the CloudFormation
    deployment.

    Args:
        name (str): The project name.

    Returns:
        (str): The S3 bucket stack name and bucket name.
    """
    s3_stack_name = f"mldeploy-s3-templates-{name}"
    bucket_name = f"mldeploy-s3-{name}"

    yaml_obj = ryml.YAML()
    yaml_obj.preserve_quotes = True
    template_str = io.StringIO()

    cf_filepath = "./deploy_templates/create_s3_bucket.yml"

    with open(cf_filepath, "r") as f:
        cf_template_yaml = yaml_obj.load(f)

    yaml_obj.dump(cf_template_yaml, template_str)
    cf_template = template_str.getvalue()

    cfn_client = boto3.client("cloudformation")
    cfn_stack_create_complete_waiter = cfn_client.get_waiter(
        waiter_name="stack_create_complete"
    )
    d_s3_stack_id = cfn_client.create_stack(
        StackName=s3_stack_name,
        TemplateBody=cf_template,
        Parameters=[
            {"ParameterKey": "ProjectName", "ParameterValue": name},
            {"ParameterKey": "S3BucketName", "ParameterValue": bucket_name},
        ],
    )
    cfn_stack_create_complete_waiter.wait(StackName=s3_stack_name)

    print(
        f"{_get_constant('MSG_PREFIX')}S3 Bucket successfully deployed. Stack Id: {d_s3_stack_id['StackId']}"
    )
    return s3_stack_name, bucket_name


def _upload_files_to_s3(bucket_name: str, files_dict: dict) -> NoReturn:
    """
    Uploads a series of files to a specified S3 bucket.

    Args:
        bucket_name (str): The S3 bucket name.

        files_dict (dict): Key-value pairs of the form:
            - key: desired file name on S3
            - value: complete file path and name on local machine
    """
    s3_client = boto3.client("s3")
    for filename, filepath in files_dict.items():
        s3_client.upload_file(filepath, bucket_name, filename)


def _create_cloudformation_file(name: str) -> NoReturn:
    """
    ### CHANGE TO METHOD - NO MORE CHANGING TEMPLATE FILE ###
    Template file remains unchanged. Any mods are passed as parameters to master stack creation.


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
    ### CHANGE TO METHOD - NO MORE CHANGING TEMPLATE FILE ###
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
    ### CHANGE TO METHOD - NO MORE CHANGING TEMPLATE FILE ###
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
# CloudFormation template creation function, top level.
# -----------------------------------------------------------------------------
def _add_cloudformation_template(name: str) -> NoReturn:
    """
    Adds the CloudFormation template to the configuration folder.

    This function should be called during the build phase.

    Args:
        name (str): Name of the project to create the cloudformation file.
    """
    if os.path.exists(
        _get_field_if_exists(name, _get_constant("CLOUDFORMATION_LOCATION_KEY"))
    ):
        print(
            f"{_get_constant('MSG_PREFIX')}CloudFormation template already exists for project '{name}'. Existing template was not overwritten."
        )
    else:
        _create_cloudformation_file(name)
        _add_project_s3_bucket(name)
        _add_ec2_instance(name)


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


# ============================================================================
# Registration functions.
def _register_stack_data(name: str):
    """"""
    keys_list = ["RestApiUrl", "RestApiKey", "QueueUrl"]


def _get_stack_output(stack_name: str, output_key: str):
    """
    Gets the output value for a given stack and key.

    Args:
        stack_name (str): Name of the master stack.

        output_key (str): The output key of the value to be retrieved.

    Returns:
        (str): The value of the output.

    Raises:
        ValueError: If the output key is not found for the specified stack.
    """
    cfn_client = boto3.client("cloudformation")
    rsp = cfn_client.describe_stacks(StackName=stack_name)
    output_list = rsp["Stacks"][0]["Outputs"]
    output_value = None
    for list_item in output_list:
        if list_item["OutputKey"] == output_key:
            output_value = list_item["OutputValue"]
            break
    if not output_value:
        raise ValueError(f"Output key [{output_key}] not found in stack [{stack_name}]")
    else:
        return output_value
