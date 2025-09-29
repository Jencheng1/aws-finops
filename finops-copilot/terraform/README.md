# FinOps Copilot - Terraform Deployment

This directory contains the Terraform configuration for deploying the FinOps Copilot infrastructure on AWS.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- Python 3.9+ (for Lambda packaging)
- Docker (for Streamlit container)
- Lambda function packages built and placed in `lambda_packages/` directory

## Quick Start

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Copy and update the variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your specific values
   ```

3. **Review the deployment plan:**
   ```bash
   terraform plan
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Architecture Components

### Lambda Functions
- **Orchestrator Agent**: Coordinates all FinOps analysis requests
- **EC2 Agent**: Analyzes EC2 instance utilization and costs
- **S3 Agent**: Analyzes S3 storage usage and costs
- **RDS Agent**: Analyzes RDS database utilization and costs
- **RI/SP Agent**: Analyzes Reserved Instances and Savings Plans
- **Tagging Agent**: Analyzes resource tagging compliance
- **Apptio Integration**: Integrates with Apptio via MCP

### Frontend
- **Streamlit App**: Web UI deployed on AWS App Runner
- **ECR Repository**: Stores Docker images for the Streamlit app

### Storage
- **S3 Buckets**: 
  - Deployment artifacts
  - API schemas for Bedrock agents

### IAM Roles
- Lambda execution role
- Bedrock agent role
- App Runner roles (build and instance)

### Monitoring
- CloudWatch Log Groups for all Lambda functions
- Optional CloudWatch Events for scheduled analysis

## Configuration Variables

Key variables to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region for deployment | `us-east-1` |
| `project_name` | Name of the project | `finops-copilot` |
| `apptio_api_key` | Apptio API key (sensitive) | Required |
| `apptio_env_id` | Apptio environment ID | Required |
| `lambda_timeout` | Lambda function timeout | `300` seconds |
| `app_runner_cpu` | App Runner CPU configuration | `1 vCPU` |
| `app_runner_memory` | App Runner memory configuration | `2 GB` |

## Post-Deployment Steps

After Terraform deployment completes:

### 1. Build and Push Streamlit Docker Image

```bash
cd ../frontend
docker build -t <ECR_REPOSITORY_URL>:latest .
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ECR_REPOSITORY_URL>
docker push <ECR_REPOSITORY_URL>:latest
```

### 2. Create Bedrock Agents

Currently, Bedrock agents need to be created manually in the AWS Console:

1. Navigate to AWS Bedrock Console
2. Create agents using the configurations in `../bedrock-agents/`
3. Use the IAM role ARN from Terraform output
4. Link agents to their respective Lambda functions

### 3. Configure Apptio MCP

Update SSM parameters with actual Apptio credentials:
```bash
aws ssm put-parameter --name /finops-copilot/mcp/apptio/api-key --value "your-actual-api-key" --overwrite
aws ssm put-parameter --name /finops-copilot/mcp/apptio/env-id --value "your-actual-env-id" --overwrite
```

### 4. Deploy MCP Server

Deploy the Apptio MCP server and update the endpoint:
```bash
aws ssm put-parameter --name /finops-copilot/mcp/apptio/endpoint --value "https://your-mcp-endpoint" --overwrite
```

## Accessing the Application

After deployment:
- **Streamlit UI**: Check the `streamlit_app_url` output
- **CloudWatch Logs**: Available in AWS Console under CloudWatch > Log Groups
- **Lambda Functions**: Available in AWS Lambda Console

## Cost Optimization

The infrastructure includes several cost optimization features:
- Lambda functions with appropriate memory/timeout settings
- App Runner auto-scaling (1-3 instances)
- S3 lifecycle policies for ECR
- CloudWatch log retention policies

## Troubleshooting

Common issues:

1. **Lambda timeouts**: Increase `lambda_timeout` variable
2. **App Runner deployment failures**: Check ECR repository and image availability
3. **Bedrock agent issues**: Verify agent configuration matches Lambda ARNs
4. **MCP connection failures**: Check SSM parameters and network connectivity

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Note**: This will delete all resources including S3 buckets (if empty) and Lambda functions.

## Security Considerations

- All IAM roles follow least-privilege principle
- S3 buckets have encryption enabled
- Sensitive parameters stored in SSM Parameter Store
- App Runner instances run in isolated environment

## Support

For issues or questions:
1. Check CloudWatch logs for detailed error messages
2. Review Terraform state for resource details
3. Refer to the main project documentation