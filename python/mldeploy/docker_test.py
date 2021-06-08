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

# from .mldeploy import *

print("\n\t\t\t--- Starting 'docker_test.py' script. ---\n")

base_image = "python:3.8-slim-buster"
new_image_name = "my-docker-image:20201130"
print(f"Selected base image: {base_image}")

client = docker.from_env()
print(f"Docker client: {client}")
print(f"Images:")

for im in client.images.list():
    print(im.tags[0])

# new_image, _ = client.images.build(
#    path='/home/lee/.local/share/mldeploy/dogs/',
#    tag=new_image_name, rm=True, forcerm=True
# )
# new_image_id = new_image.id
# new_image_tag = new_image.tags

# print(new_image_id, new_image_tag)

# base_im = client.images.get(base_image)
# print(f"Base image: {base_im.id}, {base_im.tag}")

# client.images.remove(new_image_name)
# client.images.remove(base_image)


print("\n\t\t\t--- 'docker_test.py' script complete. ---\n")
