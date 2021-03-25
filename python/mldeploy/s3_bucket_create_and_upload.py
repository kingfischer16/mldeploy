# ============================================================================
# S3_BUCKET_CREATE.PY
# -----------------
# Testing launching an S3 bucket for a project via Cloudformation
# and boto3.
#
# ============================================================================

import io
import boto3
import json
import ruamel.yaml as ryml

yaml_obj = ryml.YAML()
yaml_obj.preserve_quotes = True
template_str = io.StringIO()

cf_filepath = r"/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/create_s3_bucket.yml"

with open(cf_filepath, "r") as f:
    cf_template_yaml = yaml_obj.load(f)

yaml_obj.dump(cf_template_yaml, template_str)
cf_template = template_str.getvalue()

if __name__ == "__main__":
    # Create S3 bucket.
    cfn_client = boto3.client("cloudformation")
    cfn_stack_create_complete_waiter = cfn_client.get_waiter(
        waiter_name="stack_create_complete"
    )

    project_name = "s3-multistep"
    stack_name = f"{project_name}-stack"

    d_s3_stack_id = cfn_client.create_stack(
        StackName=stack_name,
        TemplateBody=cf_template,
        Parameters=[{"ParameterKey": "ProjectName", "ParameterValue": project_name}],
    )

    cfn_stack_create_complete_waiter.wait(StackName=stack_name)

    print(f"S3 bucket stack ID: {d_s3_stack_id['StackId']}")

    # Upload api template
    bucket_name = f"mldeploy-{project_name}"
    file_name = (
        "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/api.yml"
    )

    s3_client = boto3.client("s3")
    s3_client.upload_file(file_name, bucket_name, "api.yml")

    # create stack from api template.
    d_s3_stack_id = cfn_client.create_stack(
        StackName="sqs-boto-demo",
        TemplateURL=f"https://{bucket_name}.s3.eu-north-1.amazonaws.com/api.yml",
        Parameters=[
            {"ParameterKey": "EnvironmentName", "ParameterValue": "sqs-api-via-boto"}
        ],
        Capabilities=["CAPABILITY_NAMED_IAM"],
    )
