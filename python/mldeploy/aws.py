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
    _get_config_data,
    _get_field_if_exists,
    _add_field_to_registry,
    _get_project_folder,
    _add_salt,
    _get_constant,
)

# =============================================================================
# Deployment control.
# -----------------------------------------------------------------------------
def deploy_stack(name: str) -> NoReturn:
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
    # Don't deploy if the project is already deployed.
    deployed_status = _get_field_if_exists(name, _get_constant("DEPLOY_STATUS_KEY"))
    if deployed_status == _get_constant("STATUS_DEPLOYED"):
        print(
            f"{_get_constant('FAIL_PREFIX')}Deployment failed for project '{name}. A stack is already deployed for this project."
        )
        return

    # Create S3 bucket and upload template files.
    s3_bucket_name = (
        f"mldeploy-{name}-templates-{_add_salt(5)}"  # Project and bucket name.
    )
    s3_bucket_arn = _deploy_s3_bucket(s3_bucket_name)
    deploy_templates_folder = _get_constant("DEPLOY_TEMPLATES_FOLDER")
    templates_list = [
        "master.yml",
        "security.yml",
        "api.yml",
        "cluster.yml",
        "network.yml",
        "scaling.yml",
    ]
    _upload_files_to_s3(
        bucket_name=s3_bucket_name,
        files_dict={
            f"cloudformation/{f}": f"{deploy_templates_folder}/{f}"
            for f in templates_list
        },
    )
    # Get parameters for master stack from config file.
    d_config_params = _get_deployment_config_data(name)
    master_stack_name = f"mldeploy-{name}"
    s3_folder_url = (
        f"https://{s3_bucket_name}.s3.{d_config_params['aws-region']}amazonaws.com"
    )
    # Deploy master stack.
    cfn_client = boto3.client("cloudformation")
    cfn_stack_create_complete_waiter = cfn_client.get_waiter(
        waiter_name="stack_create_complete"
    )
    d_master_stack = cfn_client.create_stack(
        StackName=master_stack_name,
        TemplateURL=f"{s3_folder_url}/cloudformation/master.yml",
        Parameters=[
            {"ParameterKey": "ProjectName", "Parameter Value": name},
            {"ParameterKey": "S3TemplateBucketUrl", "Parameter Value": s3_folder_url},
            {
                "ParameterKey": "CustomApiKey",
                "Parameter Value": d_config_params["api-key"],
            },
            {
                "ParameterKey": "InstanceType",
                "Parameter Value": d_config_params["instance-type"],
            },
            {
                "ParameterKey": "DesiredCapacity",
                "Parameter Value": d_config_params["desired-instances"],
            },
            {
                "ParameterKey": "MaxSize",
                "Parameter Value": d_config_params["max-instances"],
            },
        ],
    )
    cfn_stack_create_complete_waiter.wait(StackName=master_stack_name)
    stack_id = d_master_stack["StackId"]
    print(
        f"{_get_constant('MSG_PREFIX')}Deployment created successfully for project '{name}'.\n\tStack ID: {stack_id}"
    )
    # Register stack.
    d_outputs = _get_stack_outputs(master_stack_name)
    _register_deployment(
        name,
        deployed=True,
        d_register_items={
            _get_constant("STACK_NAME_KEY"): master_stack_name,
            _get_constant("STACK_ID_KEY"): stack_id,
            _get_constant("SQS_URL_KEY"): d_outputs["QueueUrl"],
            _get_constant("API_URL_KEY"): d_outputs["RestApiUrl"],
            _get_constant("API_KEY_KEY"): d_outputs["RestApiKey"],
            _get_constant("SQS_ARN_KEY"): d_outputs["QueueArn"],
            _get_constant("S3_TEMPLATE_BUCKET"): s3_bucket_name,
        },
    )


def undeploy_stack(name: str) -> NoReturn:
    """
    Removes a deployed stack from AWS CloudFormation.

    Args:
        name (str): The project name.
    """
    # Do not continue if the stack is not currently deployed.
    deployed_status = _get_field_if_exists(name, _get_constant("DEPLOY_STATUS_KEY"))
    if deployed_status == _get_constant("STATUS_NOT_DEPLOYED"):
        print(
            f"{_get_constant('FAIL_PREFIX')}Undeploy action failed for project '{name}. Project has no stack deployed."
        )
        return
    # Get stack parameters.
    master_stack_name = _get_field_if_exists(name, _get_constant("STACK_NAME_KEY"))
    s3_template_bucket = _get_field_if_exists(name, _get_constant("S3_TEMPLATE_BUCKET"))
    # Clear the buckets.
    _clear_s3_bucket(s3_template_bucket)
    # Create client and waiter.
    cfn_client = boto3.client("cloudformation")
    cfn_stack_delete_complete_waiter = cfn_client.get_waiter(
        waiter_name="stack_delete_complete"
    )
    # Delete stacks.
    cfn_client.delete_stack(StackName=s3_template_bucket)
    cfn_client.delete_stack(StackName=master_stack_name)
    cfn_stack_delete_complete_waiter.wait(StackName=master_stack_name)
    print(f"{_get_constant('MSG_PREFIX')}Stack removed for project '{name}'.")
    # Register stack.
    _register_deployment(
        name,
        deployed=False,
        d_register_items={
            _get_constant("STACK_NAME_KEY"): "",
            _get_constant("STACK_ID_KEY"): "",
            _get_constant("SQS_URL_KEY"): "",
            _get_constant("API_URL_KEY"): "",
            _get_constant("API_KEY_KEY"): "",
            _get_constant("SQS_ARN_KEY"): "",
            _get_constant("S3_TEMPLATE_BUCKET"): "",
        },
    )


def _register_deployment(
    name: str,
    deployed: bool,
    d_register_items: Dict = {},
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

        d_register_items (dict):
    """
    # Add stack deployment status.
    deploy_status = (
        _get_constant("STATUS_DEPLOYED")
        if deployed
        else _get_constant("STATUS_NOT_DEPLOYED")
    )
    _add_field_to_registry(name, _get_constant("DEPLOY_STATUS_KEY"), deploy_status)
    # Add deployment details to registry.
    if deployed and d_register_items:
        for reg_key, reg_item in d_register_items.items():
            _add_field_to_registry(name, reg_key, reg_item)


# =============================================================================
# Deployment subfunctions.
# -----------------------------------------------------------------------------
def _deploy_s3_bucket(bucket_name: str) -> str:
    """
    Deploys a S3 bucket to contain the templates for the CloudFormation
    deployment.

    Args:
        bucket_name (str): The name of the S3 bucket to deploy.

    Returns:
        (str): The S3 bucket ARN.
    """
    yaml_obj = ryml.YAML()
    yaml_obj.preserve_quotes = True
    template_str = io.StringIO()
    cf_filepath = f"{_get_constant('DEPLOY_TEMPLATES_FOLDER')}/create_s3_bucket.yml"
    with open(cf_filepath, "r") as f:
        cf_template_yaml = yaml_obj.load(f)

    yaml_obj.dump(cf_template_yaml, template_str)
    cf_template = template_str.getvalue()

    cfn_client = boto3.client("cloudformation")
    cfn_stack_create_complete_waiter = cfn_client.get_waiter(
        waiter_name="stack_create_complete"
    )
    d_s3_stack_id = cfn_client.create_stack(
        StackName=bucket_name,
        TemplateBody=cf_template,
        Parameters=[
            {"ParameterKey": "ProjectName", "ParameterValue": bucket_name},
            {"ParameterKey": "S3BucketName", "ParameterValue": bucket_name},
        ],
    )
    cfn_stack_create_complete_waiter.wait(StackName=bucket_name)
    print(
        f"{_get_constant('MSG_PREFIX')}S3 Bucket successfully deployed. Stack Id: {d_s3_stack_id['StackId']}"
    )
    return _get_stack_outputs(bucket_name)["ProjectBucketArn"]


def _upload_files_to_s3(bucket_name: str, files_dict: Dict) -> NoReturn:
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
    print(
        f"{_get_constant('MSG_PREFIX')}Template files successfully uploaded to S3 bucket."
    )


def _clear_s3_bucket(bucket_name: str) -> NoReturn:
    """
    Clears the specified bucket of all files, which
    is needed before disposal.

    Args:
        bucket_name (str): Name of the bucket to clear.
    """
    s3 = boto3.resource("s3")
    s3_bucket = s3.Bucket(bucket_name)
    s3_bucket.objects.all().delete()


def _get_deployment_config_data(name: str) -> Dict:
    """
    Returns the following data from a project config file:
        - Region
        - custom API key
        - desired number of instances in cluster
        - maximum allowed number of instances in cluster
        - cluster type (Fargate or EC2)
        - instance type (if EC2 cluster)

    Args:
        name (str): Name of the project.

    Returns:
        (dict): Key-value pairs of parameters for deployment.
    """
    d_config = _get_config_data(name)
    config_param_keys = [
        "aws-region",
        "deployment-type",
        "api-key",
        "desired-instances",
        "max-instances",
        "ec2-instance-type",
    ]
    d_deploy_params = {
        k: d_config[k] for k in config_param_keys if k in d_config.keys()
    }
    return d_deploy_params


def _get_stack_outputs(stack_name: str) -> Dict:
    """
    Returns the outputs of the specified stack as a dictionary.

    Args:
        stack_name (str): Name of the stack for which to get outputs.

    Returns:
        (dict): OutputKey-OutputValue pairs.
    """
    cfn_client = boto3.client("cloudformation")
    rsp = cfn_client.describe_stacks(StackName=stack_name)
    output_list = rsp["Stacks"][0]["Outputs"]
    d_outputs = {x["OutputKey"]: x["OutputValue"] for x in output_list}
    return d_outputs
