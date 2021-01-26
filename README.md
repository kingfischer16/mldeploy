# **`{ml}deploy`**
## Deploy ML to the cloud as a REST API for inference and training

<img src="https://img.shields.io/badge/python%20-%2314354C.svg?&style=for-the-badge&logo=python&logoColor=white"/> <img src="https://img.shields.io/badge/docker%20-%230db7ed.svg?&style=for-the-badge&logo=docker&logoColor=white"/> <img src="https://img.shields.io/badge/AWS%20-%23FF9900.svg?&style=for-the-badge&logo=amazon-aws&logoColor=white"/> <img src="https://img.shields.io/badge/{REST:API}%20-%238CC63F.svg?&style=for-the-badge&logo=rest&logoColor=white"/>

---

**`{ml}deploy`** is a Python-based CLI tool and library for quickly containerizing and deploying your machine learning models to cloud services as a REST API.

Code can be local or pulled directly from a GitHub repository. Applications are deployed on cloud services (AWS) within custom generated Docker containers. Using AWS Lambda, AWS SQS, and AWS API Gateway a REST API is exposed for interacting with the deployed application. This can be used for:
 * **Inference:** A deployed model is used to make a prediction given some input data.
 * **Training:** A deployed model framework can be passed different training data, data augmentations, or model architectures for hyperparameter searching.
 
---

## Current status
This is a pre-release work-in-progress. Currently the tool can:
 * Setup project folders with configuration files and registry
 * Create a Dockerfile and build a Docker image from specified configuration
 * Create an AWS ECS cluster via CloudFormation template

---

#### Disclaimer
The code within this repository is provided as is, for use as dictated by the LICENSE file. Any charges incurred from cloud resources as a result of deploying code is soley the responsibility of the end user. Please be responsible and monitor your resource usage to avoid unwanted or excessive charges.
 