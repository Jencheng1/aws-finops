variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "finops-copilot"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "lambda_functions" {
  description = "List of Lambda function names"
  type        = list(string)
  default = [
    "orchestrator_agent",
    "ec2_agent",
    "s3_agent",
    "rds_agent",
    "ri_sp_agent",
    "tagging_agent",
    "apptio_integration"
  ]
}

variable "lambda_runtime" {
  description = "Runtime for Lambda functions"
  type        = string
  default     = "python3.9"
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Apptio MCP Configuration
variable "apptio_mcp_endpoint" {
  description = "Apptio MCP server endpoint"
  type        = string
  default     = "http://localhost:8000"
}

variable "apptio_api_key" {
  description = "Apptio API key"
  type        = string
  sensitive   = true
}

variable "apptio_env_id" {
  description = "Apptio environment ID"
  type        = string
}

# ECR Configuration for Streamlit
variable "create_ecr_repository" {
  description = "Whether to create ECR repository for Streamlit app"
  type        = bool
  default     = true
}

variable "ecr_image_tag_mutability" {
  description = "ECR image tag mutability setting"
  type        = string
  default     = "MUTABLE"
}

variable "ecr_scan_on_push" {
  description = "Enable ECR image scanning on push"
  type        = bool
  default     = true
}

# App Runner Configuration
variable "app_runner_cpu" {
  description = "CPU configuration for App Runner"
  type        = string
  default     = "1 vCPU"
}

variable "app_runner_memory" {
  description = "Memory configuration for App Runner"
  type        = string
  default     = "2 GB"
}

variable "app_runner_port" {
  description = "Port for Streamlit application"
  type        = string
  default     = "8501"
}

# Cost Optimization Settings
variable "enable_cost_allocation_tags" {
  description = "Enable cost allocation tags"
  type        = bool
  default     = true
}

variable "required_tags" {
  description = "Required tags for compliance"
  type        = list(string)
  default     = ["Environment", "Owner", "Project", "CostCenter", "Application"]
}

# Optional VPC Configuration
variable "create_vpc_connector" {
  description = "Whether to create VPC connector for App Runner"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID for App Runner VPC connector"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for App Runner VPC connector"
  type        = list(string)
  default     = []
}

# Optional Custom Domain
variable "custom_domain" {
  description = "Custom domain for Streamlit app"
  type        = string
  default     = ""
}

# Optional Bedrock via CloudFormation
variable "create_bedrock_agents_via_cfn" {
  description = "Whether to create Bedrock agents via CloudFormation"
  type        = bool
  default     = false
}