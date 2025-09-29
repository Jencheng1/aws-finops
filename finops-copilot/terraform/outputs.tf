output "deployment_summary" {
  value = {
    region     = var.aws_region
    account_id = data.aws_caller_identity.current.account_id
    project    = var.project_name
  }
  description = "Deployment summary information"
}

output "lambda_functions" {
  value = {
    for k, v in aws_lambda_function.finops_functions :
    k => {
      name         = v.function_name
      arn          = v.arn
      last_modified = v.last_modified
    }
  }
  description = "Deployed Lambda functions"
}

output "streamlit_app_url" {
  value       = "https://${aws_apprunner_service.streamlit_frontend.service_url}"
  description = "URL for the Streamlit frontend application"
}

output "ecr_repository_url" {
  value       = var.create_ecr_repository ? aws_ecr_repository.streamlit_app[0].repository_url : null
  description = "ECR repository URL for Streamlit Docker images"
}

output "s3_buckets" {
  value = {
    deployment_artifacts = aws_s3_bucket.deployment_artifacts.id
    api_schemas         = aws_s3_bucket.api_schemas.id
  }
  description = "S3 buckets created for the project"
}

output "iam_roles" {
  value = {
    lambda_role           = aws_iam_role.lambda_role.arn
    bedrock_agent_role    = aws_iam_role.bedrock_agent_role.arn
    apprunner_build_role  = aws_iam_role.apprunner_build_role.arn
    apprunner_instance_role = aws_iam_role.apprunner_instance_role.arn
  }
  description = "IAM roles created for the project"
}

output "ssm_parameters" {
  value = {
    mcp_endpoint = aws_ssm_parameter.mcp_endpoint.name
    mcp_api_key  = aws_ssm_parameter.mcp_api_key.name
    mcp_env_id   = aws_ssm_parameter.mcp_env_id.name
  }
  description = "SSM parameters for MCP configuration"
}

output "cloudwatch_log_groups" {
  value = {
    for k, v in aws_cloudwatch_log_group.lambda_logs :
    k => v.name
  }
  description = "CloudWatch log groups for Lambda functions"
}

output "deployment_instructions" {
  value = <<-EOT
    FinOps Copilot Deployment Complete!
    
    Next Steps:
    1. Build and push Streamlit Docker image:
       - cd ../frontend
       - docker build -t ${var.create_ecr_repository ? aws_ecr_repository.streamlit_app[0].repository_url : "finops-streamlit"}:latest .
       - aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.create_ecr_repository ? aws_ecr_repository.streamlit_app[0].repository_url : "ECR_URL"}
       - docker push ${var.create_ecr_repository ? aws_ecr_repository.streamlit_app[0].repository_url : "finops-streamlit"}:latest
    
    2. Create Bedrock Agents in AWS Console:
       - Use the configuration in: bedrock_agent_configuration output
       - Agent Role ARN: ${aws_iam_role.bedrock_agent_role.arn}
       - API Schema Bucket: ${aws_s3_bucket.api_schemas.id}
    
    3. Configure Apptio MCP:
       - Update SSM parameters with actual Apptio credentials
       - Deploy MCP server with provided configuration
    
    4. Access the application:
       - Streamlit UI: https://${aws_apprunner_service.streamlit_frontend.service_url}
       - CloudWatch Logs: AWS Console > CloudWatch > Log Groups
    
    5. Monitor costs:
       - Enable Cost Allocation Tags in AWS Billing Console
       - Set up AWS Budgets for the project
  EOT
  description = "Post-deployment instructions"
}