terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure backend settings in terraform.tfvars or via CLI
    # bucket = "finops-copilot-terraform-state"
    # key    = "finops-copilot/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedBy   = "FinOps-Copilot"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# S3 bucket for deployment artifacts
resource "aws_s3_bucket" "deployment_artifacts" {
  bucket = "${var.project_name}-deployment-${data.aws_caller_identity.current.account_id}"
  
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "deployment_artifacts" {
  bucket = aws_s3_bucket.deployment_artifacts.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "deployment_artifacts" {
  bucket = aws_s3_bucket.deployment_artifacts.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket for API schemas
resource "aws_s3_bucket" "api_schemas" {
  bucket = "${var.project_name}-schemas-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "api_schemas" {
  bucket = aws_s3_bucket.api_schemas.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# CloudWatch Log Group for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset(var.lambda_functions)
  
  name              = "/aws/lambda/${var.project_name}-${each.key}"
  retention_in_days = var.log_retention_days
}

# SSM Parameters for MCP configuration
resource "aws_ssm_parameter" "mcp_endpoint" {
  name        = "/${var.project_name}/mcp/apptio/endpoint"
  description = "Apptio MCP server endpoint"
  type        = "String"
  value       = var.apptio_mcp_endpoint
}

resource "aws_ssm_parameter" "mcp_api_key" {
  name        = "/${var.project_name}/mcp/apptio/api-key"
  description = "Apptio API key"
  type        = "SecureString"
  value       = var.apptio_api_key
}

resource "aws_ssm_parameter" "mcp_env_id" {
  name        = "/${var.project_name}/mcp/apptio/env-id"
  description = "Apptio environment ID"
  type        = "String"
  value       = var.apptio_env_id
}