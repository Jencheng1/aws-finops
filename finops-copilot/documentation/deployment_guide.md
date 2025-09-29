# FinOps Copilot Deployment Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Local Deployment](#local-deployment)
5. [AWS Deployment](#aws-deployment)
6. [Configuration](#configuration)
7. [Testing the Deployment](#testing-the-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance and Updates](#maintenance-and-updates)
10. [Security Considerations](#security-considerations)

## Introduction

This guide provides instructions for deploying the FinOps Copilot system, an AI-powered AWS cost optimization solution built on AWS Bedrock. The system can be deployed locally for development and testing purposes, or to AWS for production use.

## Prerequisites

### General Requirements

- Git
- Python 3.8 or higher
- Node.js 14 or higher
- AWS CLI configured with appropriate credentials
- AWS account with appropriate permissions

### AWS Permissions

The following AWS permissions are required for deployment:

- IAM: Create roles and policies
- Lambda: Create and manage functions
- API Gateway: Create and manage APIs
- App Runner: Create and manage services
- S3: Create and manage buckets
- DynamoDB: Create and manage tables
- CloudWatch: Create and manage logs and metrics
- Secrets Manager: Create and manage secrets
- Bedrock: Access to foundation models and agent capabilities

### Required Software

- AWS CLI v2
- AWS SAM CLI
- Python 3.8+
- Node.js 14+
- Docker (for local testing and SAM builds)

## Deployment Options

The FinOps Copilot system can be deployed in two ways:

1. **Local Deployment**: Deploy the system locally for development and testing purposes.
2. **AWS Deployment**: Deploy the system to AWS for production use.

## Local Deployment

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/finops-copilot.git
cd finops-copilot
```

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Install Frontend Dependencies

```bash
cd frontend
pip install -r requirements.txt
cd ..
```

### Step 4: Configure AWS Credentials

Ensure your AWS credentials are configured correctly:

```bash
aws configure
```

Enter your AWS Access Key ID, Secret Access Key, default region, and output format.

### Step 5: Set Up Local Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# AWS Configuration
AWS_REGION=us-east-1

# API Configuration
API_PORT=8080

# Frontend Configuration
STREAMLIT_PORT=8501

# External API Keys (if needed)
CLOUDHEALTH_API_KEY=your_cloudhealth_api_key
CLOUDABILITY_API_KEY=your_cloudability_api_key
SPOTIO_API_KEY=your_spotio_api_key
```

### Step 6: Start the Backend Services

Start the local API server:

```bash
cd backend
python local_server.py
```

This will start the API server on port 8080 (or the port specified in your `.env` file).

### Step 7: Start the Frontend

In a new terminal window, start the Streamlit frontend:

```bash
cd frontend
streamlit run app.py
```

This will start the Streamlit application on port 8501 (or the port specified in your `.env` file).

### Step 8: Access the Application

Open your web browser and navigate to:

```
http://localhost:8501
```

You should now see the FinOps Copilot dashboard.

## AWS Deployment

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/finops-copilot.git
cd finops-copilot
```

### Step 2: Configure Deployment Parameters

Edit the `deployment/config.json` file to set your deployment parameters:

```json
{
  "StackName": "finops-copilot",
  "Region": "us-east-1",
  "Parameters": {
    "Environment": "prod",
    "ApiStageName": "v1",
    "DashboardName": "FinOpsCopilot",
    "CloudHealthApiKeySecretName": "cloudhealth-api-key",
    "CloudabilityApiKeySecretName": "cloudability-api-key",
    "SpotioApiKeySecretName": "spotio-api-key"
  }
}
```

### Step 3: Store API Keys in AWS Secrets Manager

Store your external API keys in AWS Secrets Manager:

```bash
# CloudHealth API Key
aws secretsmanager create-secret \
  --name cloudhealth-api-key \
  --secret-string '{"api_key":"your_cloudhealth_api_key"}'

# Cloudability API Key
aws secretsmanager create-secret \
  --name cloudability-api-key \
  --secret-string '{"api_key":"your_cloudability_api_key"}'

# Spot.io API Key
aws secretsmanager create-secret \
  --name spotio-api-key \
  --secret-string '{"api_key":"your_spotio_api_key"}'
```

### Step 4: Deploy the CloudFormation Stack

Run the deployment script:

```bash
cd deployment
./deploy.sh
```

This script will:

1. Package the Lambda functions
2. Deploy the CloudFormation stack
3. Deploy the Streamlit frontend to AWS App Runner

### Step 5: Monitor the Deployment

You can monitor the deployment progress in the AWS CloudFormation console:

```bash
aws cloudformation describe-stacks --stack-name finops-copilot
```

### Step 6: Access the Application

Once the deployment is complete, the script will output the URL of the Streamlit dashboard. Open this URL in your web browser to access the FinOps Copilot dashboard.

## Configuration

### AWS Bedrock Agents Configuration

The AWS Bedrock agents are configured using the following files:

- `deployment/cloudformation/templates/agents.yaml`: CloudFormation template for creating the agents
- `deployment/agent-definitions/`: JSON files defining the agent configurations

To customize the agents, edit the JSON files in the `deployment/agent-definitions/` directory.

### API Configuration

The API is configured using the following files:

- `deployment/cloudformation/templates/api.yaml`: CloudFormation template for creating the API
- `backend/config.py`: Configuration file for the API

To customize the API, edit these files.

### Frontend Configuration

The Streamlit frontend is configured using the following files:

- `frontend/config.py`: Configuration file for the frontend
- `frontend/.streamlit/config.toml`: Streamlit configuration file

To customize the frontend, edit these files.

## Testing the Deployment

### Running Tests

To run the tests, use the test runner script:

```bash
cd tests
./run_tests.py --all
```

This will run all tests and generate a report in the `tests/reports/` directory.

To run specific tests, use the following options:

```bash
# Run unit tests
./run_tests.py --unit

# Run integration tests
./run_tests.py --integration

# Run end-to-end tests
./run_tests.py --e2e

# Run performance tests
./run_tests.py --performance

# Run security tests
./run_tests.py --security
```

### Verifying the Deployment

To verify that the deployment was successful, check the following:

1. **API Health Check**: Send a request to the health check endpoint:

```bash
curl https://your-api-endpoint/health
```

You should receive a response with status code 200 and a JSON body containing `{"status": "healthy"}`.

2. **Dashboard Access**: Open the dashboard URL in your web browser. You should see the FinOps Copilot dashboard.

3. **CloudWatch Logs**: Check the CloudWatch logs for any errors:

```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/finops-copilot
```

## Troubleshooting

### Common Issues

#### API Gateway Errors

If you encounter errors with API Gateway, check the following:

1. **CloudWatch Logs**: Check the Lambda function logs in CloudWatch.
2. **API Gateway Configuration**: Verify that the API Gateway configuration is correct.
3. **IAM Permissions**: Verify that the Lambda functions have the necessary permissions.

#### Lambda Function Errors

If you encounter errors with Lambda functions, check the following:

1. **CloudWatch Logs**: Check the Lambda function logs in CloudWatch.
2. **IAM Permissions**: Verify that the Lambda functions have the necessary permissions.
3. **Environment Variables**: Verify that the environment variables are set correctly.

#### Streamlit Dashboard Errors

If you encounter errors with the Streamlit dashboard, check the following:

1. **App Runner Logs**: Check the App Runner service logs.
2. **API Endpoint Configuration**: Verify that the API endpoint is configured correctly in the frontend.
3. **CORS Configuration**: Verify that CORS is configured correctly in the API.

### Getting Help

If you encounter issues that you cannot resolve, please:

1. Check the [GitHub repository issues](https://github.com/yourusername/finops-copilot/issues) to see if the issue has already been reported.
2. If not, create a new issue with a detailed description of the problem, including error messages and steps to reproduce.

## Maintenance and Updates

### Updating the System

To update the system, follow these steps:

1. Pull the latest changes from the repository:

```bash
git pull origin main
```

2. Redeploy the system:

```bash
cd deployment
./deploy.sh
```

### Monitoring

The system includes monitoring using CloudWatch. You can view the following metrics:

- **Lambda Function Metrics**: Invocations, errors, duration, etc.
- **API Gateway Metrics**: Requests, latency, errors, etc.
- **App Runner Metrics**: CPU, memory, requests, etc.

To view these metrics, go to the CloudWatch console in the AWS Management Console.

### Backups

The system stores data in DynamoDB tables. To back up these tables, you can use DynamoDB's built-in backup and restore functionality:

```bash
# Create a backup
aws dynamodb create-backup \
  --table-name finops-copilot-state \
  --backup-name finops-copilot-state-backup

# List backups
aws dynamodb list-backups

# Restore from a backup
aws dynamodb restore-table-from-backup \
  --target-table-name finops-copilot-state-restored \
  --backup-arn arn:aws:dynamodb:us-east-1:123456789012:table/finops-copilot-state/backup/01234567890123456789012345678901
```

## Security Considerations

### IAM Permissions

The system uses IAM roles with least privilege permissions. The roles are defined in the CloudFormation templates in the `deployment/cloudformation/templates/` directory.

### API Authentication

The API uses API Gateway's built-in authentication mechanisms. The API requires an API key for access, which is generated during deployment.

### Data Encryption

All data is encrypted in transit using HTTPS and at rest using AWS's built-in encryption mechanisms.

### Secrets Management

Sensitive information such as API keys is stored in AWS Secrets Manager.

### Security Best Practices

The system follows AWS security best practices, including:

- Least privilege permissions
- Encryption in transit and at rest
- Secure API authentication
- Regular security updates
- Monitoring and logging

For more information on security best practices, see the [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/) documentation.
