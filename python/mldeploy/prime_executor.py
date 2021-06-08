# ============================================================================
# PRIME_EXECUTOR.PY
# ----------------------------------------------------------------------------
# A test script for developing the deployment interface and architecture.
#
# This script should do a few things in order:
#   1. Loop infinitely.
#   2. Poll an SQS service for messages.
#   3. Process the message and return a result if found (largest prime number)
#   4. Wait X seconds if no message found.
#
# This script will be divided into a "runner" and an "executor" script
# when changing to a more flexible build. This script is intended to be a
# sample load only.
#
# ============================================================================

# Imports.
import boto3
import math
import numpy as np
import time

# Constants.
AWS_SQS_QUEUE = None
LOOP_WAIT_SECONDS = 10

# Sample functions.
def max_prime(n):
    """
    Calculates all prime numbers up to 'n'.
    """
    max_input = 2e6
    n = int(n) if n < max_input else int(max_input)
    largest_prime = 0
    for ni in range(2, n + 1):
        max_n = math.ceil(math.sqrt(ni))
        max_n = max_n if max_n != ni else max_n - 1
        ni_is_prime = True
        for div in range(2, max_n + 1):
            if ni % div == 0:
                ni_is_prime = False
                break
        if ni_is_prime:
            largest_prime = ni
    return largest_prime


# Main loop.
if __name__ == "__main__":
    # Use Cloudformation client to get SQS locations.
    cfn_client = boto3.client("cloudformation")
    q_url = "cfn_client.get_params().QueueUrl"

    # Create the client for the SQS queue to poll.
    sqs_client = boto3.client("sqs")

    # Infinite loop to pickup messages.
    while True:
        # poll SQS
        msg = sqs_client.receive_message(
            QueueUrl=q_url,
            AttributeNames=["All"],
            MessageAttributeNames=[
                "string",
            ],
            MaxNumberOfMessages=1,
            VisibilityTimeout=15,
            WaitTimeSeconds=10,
        )
        if msg:
            # execute
            prime_num = max_prime(int(msg.data))
        else:
            # Wait if nothing is found.
            time.sleep(LOOP_WAIT_SECONDS)
