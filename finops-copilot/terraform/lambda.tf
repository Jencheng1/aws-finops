# Lambda Layer for common dependencies
resource "aws_lambda_layer_version" "finops_dependencies" {
  filename            = "${path.module}/lambda_layer.zip"
  layer_name          = "${var.project_name}-dependencies"
  compatible_runtimes = [var.lambda_runtime]
  description         = "Common dependencies for FinOps Lambda functions"
  
  lifecycle {
    create_before_destroy = true
  }
}

# Lambda Functions
resource "aws_lambda_function" "finops_functions" {
  for_each = toset(var.lambda_functions)
  
  function_name = "${var.project_name}-${each.key}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "${path.module}/lambda_packages/${each.key}.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_packages/${each.key}.zip")
  
  layers = [aws_lambda_layer_version.finops_dependencies.arn]
  
  environment {
    variables = {
      PROJECT_NAME = var.project_name
      AWS_REGION   = var.aws_region
      LOG_LEVEL    = "INFO"
    }
  }
  
  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]
  
  tags = {
    Function = each.key
    Type     = "Lambda"
  }
}

# Lambda Permissions for Bedrock Invocation
resource "aws_lambda_permission" "bedrock_invoke" {
  for_each = aws_lambda_function.finops_functions
  
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:agent/*"
}

# Lambda Permissions for Orchestrator to invoke other functions
resource "aws_lambda_permission" "orchestrator_invoke" {
  for_each = {
    for k, v in aws_lambda_function.finops_functions :
    k => v if k != "orchestrator_agent"
  }
  
  statement_id  = "AllowOrchestratorInvoke"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.finops_functions["orchestrator_agent"].arn
}

# Lambda Aliases for versioning
resource "aws_lambda_alias" "finops_functions_live" {
  for_each = aws_lambda_function.finops_functions
  
  name             = "live"
  description      = "Live version of ${each.key}"
  function_name    = each.value.function_name
  function_version = "$LATEST"
}

# CloudWatch Event Rule for scheduled analysis (optional)
resource "aws_cloudwatch_event_rule" "daily_analysis" {
  name                = "${var.project_name}-daily-analysis"
  description         = "Trigger daily cost analysis"
  schedule_expression = "cron(0 8 * * ? *)"  # 8 AM UTC daily
  is_enabled          = false  # Disabled by default
}

resource "aws_cloudwatch_event_target" "orchestrator" {
  rule      = aws_cloudwatch_event_rule.daily_analysis.name
  target_id = "OrchestratorTarget"
  arn       = aws_lambda_function.finops_functions["orchestrator_agent"].arn
  
  input = jsonencode({
    query = "Perform daily cost analysis and send report"
    days  = 1
    depth = "detailed"
  })
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.finops_functions["orchestrator_agent"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_analysis.arn
}