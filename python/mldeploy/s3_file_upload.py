# ============================================================================
# S3_FILE_UPLOAD.PY
# -----------------
# Testing file uploads to S3 using boto3.
#
# ============================================================================

import io
import boto3


if __name__ == "__main__":
    cfn_client = boto3.client("cloudformation")
    project_name = "s3-testing"
    bucket_name = f"mldeploy-{project_name}"
    file_name = (
        "/home/lee/GitProjects/mldeploy/python/mldeploy/deploy_templates/api.yml"
    )

    s3_client = boto3.client("s3")
    s3_client.upload_file(file_name, bucket_name, "api.yml")

    s3_bucket_waiter = s3_client.get_waiter("bucket_exists")
