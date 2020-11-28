# =============================================================================
# DOCKER_TEST.PY
# -----------------------------------------------------------------------------
# Test file for using the Docker Python SDK.
#
# Note:
#   Since docker requires 'sudo' permissions, you will need to run the
#   Python file from bash by explicit reference to the virtualenv::
#       >>> sudo ~/pyenv/python-cli/bin/python docker_test.py
#
# =============================================================================


import docker
import ruamel.yaml as ryml  # Allows modification of YAML file without disrupting comments.
from .mldeploy import *

print("\n\t\t\t--- Starting 'docker_test.py' script. ---\n")

base_image = 'python:3.8-alpine3.11'
print(f"Selected base image: {base_image}")

#client = docker.from_env()
#print(client)

print("\n\t\t\t--- 'docker_test.py' script complete. ---\n")
