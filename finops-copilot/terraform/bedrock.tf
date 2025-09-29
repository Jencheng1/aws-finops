# Note: As of the knowledge cutoff, Bedrock Agent creation via Terraform might have limitations
# This file provides the foundation for Bedrock agent configuration
# You may need to create agents manually or use AWS CDK/CloudFormation

# Upload API schemas to S3
resource "aws_s3_object" "orchestrator_api_schema" {
  bucket = aws_s3_bucket.api_schemas.id
  key    = "orchestrator-api-schema.yaml"
  source = "${path.module}/../bedrock-agents/orchestrator-api-schema.yaml"
  etag   = filemd5("${path.module}/../bedrock-agents/orchestrator-api-schema.yaml")
  
  content_type = "application/x-yaml"
}

resource "aws_s3_object" "service_agent_api_schema" {
  bucket = aws_s3_bucket.api_schemas.id
  key    = "service-agent-api-schema.yaml"
  source = "${path.module}/../bedrock-agents/service-agent-api-schema.yaml"
  etag   = filemd5("${path.module}/../bedrock-agents/service-agent-api-schema.yaml")
  
  content_type = "application/x-yaml"
}

# S3 bucket policy to allow Bedrock access
resource "aws_s3_bucket_policy" "api_schemas" {
  bucket = aws_s3_bucket.api_schemas.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.api_schemas.arn}/*"
      }
    ]
  })
}

# Outputs for manual Bedrock agent configuration
output "bedrock_agent_configuration" {
  value = {
    agent_role_arn = aws_iam_role.bedrock_agent_role.arn
    api_schema_bucket = aws_s3_bucket.api_schemas.id
    lambda_functions = {
      for k, v in aws_lambda_function.finops_functions :
      k => {
        arn  = v.arn
        name = v.function_name
      }
    }
  }
  
  description = "Configuration details for setting up Bedrock agents"
}

# CloudFormation stack for Bedrock agents (alternative approach)
resource "aws_cloudformation_stack" "bedrock_agents" {
  count = var.create_bedrock_agents_via_cfn ? 1 : 0
  
  name = "${var.project_name}-bedrock-agents"
  
  template_body = jsonencode({
    AWSTemplateFormatVersion = "2010-09-09"
    Description = "Bedrock Agents for FinOps Copilot"
    
    Resources = {
      OrchestratorAgent = {
        Type = "AWS::Bedrock::Agent"
        Properties = {
          AgentName = "${var.project_name}-orchestrator-agent"
          AgentResourceRoleArn = aws_iam_role.bedrock_agent_role.arn
          Description = "Orchestrator agent for FinOps analysis"
          FoundationModel = "anthropic.claude-v2"
          Instruction = "You are the FinOps Orchestrator Agent responsible for coordinating cost optimization analysis across AWS services."
          ActionGroups = [
            {
              ActionGroupName = "OrchestratorActions"
              ActionGroupExecutor = {
                Lambda = aws_lambda_function.finops_functions["orchestrator_agent"].arn
              }
              ApiSchema = {
                S3 = {
                  S3BucketName = aws_s3_bucket.api_schemas.id
                  S3ObjectKey = "orchestrator-api-schema.yaml"
                }
              }
            }
          ]
        }
      }
    }
  })
  
  capabilities = ["CAPABILITY_IAM"]
  
  depends_on = [
    aws_s3_object.orchestrator_api_schema,
    aws_lambda_permission.bedrock_invoke
  ]
}