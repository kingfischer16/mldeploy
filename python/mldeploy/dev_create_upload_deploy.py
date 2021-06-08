# ============================================================================
# DEV_CREATE_UPLOAD_DEPLOY.PY
# -----------------
# Testing launching an S3 bucket for a project via Cloudformation
# and boto3, then uploading the templates to S3 and calling 'create stack'
# on
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

d_files = {
    "master.yml": "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/master.yml",
    "security.yml": "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/security.yml",
    "api.yml": "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/api.yml",
    "cluster.yml": "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/cluster.yml",
    "network.yml": "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/network.yml",
    "scaling.yml": "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/scaling.yml",
}

project_name = "nested-test4"
s3_stack_name = f"{project_name}-s3-stack"
master_stack_name = f"{project_name}-master-stack"
bucket_name = f"mldeploy-{project_name}"


if __name__ == "__main__":
    # Create S3 bucket.
    cfn_client = boto3.client("cloudformation")
    cfn_stack_create_complete_waiter = cfn_client.get_waiter(
        waiter_name="stack_create_complete"
    )
    d_s3_stack_id = cfn_client.create_stack(
        StackName=s3_stack_name,
        TemplateBody=cf_template,
        Parameters=[{"ParameterKey": "ProjectName", "ParameterValue": project_name}],
    )
    cfn_stack_create_complete_waiter.wait(StackName=s3_stack_name)

    print(f"S3 bucket stack ID: {d_s3_stack_id['StackId']}")

    # Upload nested template.
    s3_client = boto3.client("s3")
    for filename, filepath in d_files.items():
        s3_client.upload_file(filepath, bucket_name, f"cloudformation/{filename}")

    # create stack from api template.
    s3_folder = f"https://{bucket_name}.s3.eu-north-1.amazonaws.com"
    d_master_stack_id = cfn_client.create_stack(
        StackName=master_stack_name,
        TemplateURL=f"{s3_folder}/cloudformation/master.yml",
        Parameters=[
            {"ParameterKey": "ProjectName", "ParameterValue": project_name},
            {"ParameterKey": "S3TemplateBucketUrl", "ParameterValue": s3_folder},
        ],
        Capabilities=["CAPABILITY_NAMED_IAM"],
    )
    cfn_stack_create_complete_waiter.wait(StackName=master_stack_name)
    print(f"Master stack ID: {d_master_stack_id['StackId']}")
    print("Deployment complete.")
