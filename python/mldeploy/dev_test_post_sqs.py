# ============================================================================
# DEV_TEST_POST_SQS.PY
# ----------------------------------------------------------------------------
# Posts a certain number of integers to a REST API for testing
# the SQS queue and execution chain.
#
# ============================================================================

# Imports.
from datetime import datetime
import numpy as np
import requests
import json

AWS_SQS_URL = (
    "https://n123k4vv68.execute-api.eu-north-1.amazonaws.com/DeploymentStage/sqs"
)
NUM_INTEGERS = 10
API_KEY = "A1B2C3D4E5F6G7H8I9J0"

if __name__ == "__main__":
    # Generate X integers to post.
    integer_list = [int(i * 1e7) for i in np.random.uniform(size=NUM_INTEGERS)]
    for integer in integer_list:
        # Populate data for PUT.
        data = {
            "Date": datetime.now().strftime("%Y-%m-%m %H:%M:%S"),
            "Integer": integer,
            "Source": "DEV_TEST_POST_SQS.PY",
        }

        # Setup authorization.
        auth = requests.auth.HTTPBasicAuth("apikey", API_KEY)

        # Populate headers.
        headers = {"x-api-key": API_KEY, "Content-type": "application/json"}

        # Make the POST request.
        resp = requests.post(AWS_SQS_URL, data=json.dumps(data), headers=headers)

        print(
            f"POST request made with number: {integer}.\n\tResponse: {resp.text}\n\tStatus Code: {resp.status_code}\n\tJSON: {json.dumps(data)}"
        )
