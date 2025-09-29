# ECR Repository for Streamlit Application
resource "aws_ecr_repository" "streamlit_app" {
  count = var.create_ecr_repository ? 1 : 0
  
  name                 = "${var.project_name}-streamlit"
  image_tag_mutability = var.ecr_image_tag_mutability
  
  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "streamlit_app" {
  count      = var.create_ecr_repository ? 1 : 0
  repository = aws_ecr_repository.streamlit_app[0].name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# App Runner Service for Streamlit Frontend
resource "aws_apprunner_service" "streamlit_frontend" {
  service_name = "${var.project_name}-frontend"
  
  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_build_role.arn
    }
    
    image_repository {
      image_configuration {
        port = var.app_runner_port
        
        runtime_environment_variables = {
          AWS_DEFAULT_REGION    = var.aws_region
          PROJECT_NAME          = var.project_name
          ORCHESTRATOR_FUNCTION = aws_lambda_function.finops_functions["orchestrator_agent"].function_name
        }
      }
      
      image_identifier      = var.create_ecr_repository ? "${aws_ecr_repository.streamlit_app[0].repository_url}:latest" : "${var.project_name}-streamlit:latest"
      image_repository_type = "ECR"
    }
    
    auto_deployments_enabled = true
  }
  
  health_check_configuration {
    healthy_threshold   = 2
    interval            = 10
    path                = "/"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
  
  instance_configuration {
    cpu               = var.app_runner_cpu
    memory            = var.app_runner_memory
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }
  
  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.frontend.arn
  
  tags = {
    Type = "Frontend"
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.apprunner_ecr_access
  ]
}

# Auto Scaling Configuration for App Runner
resource "aws_apprunner_auto_scaling_configuration_version" "frontend" {
  auto_scaling_configuration_name = "${var.project_name}-frontend-autoscaling"
  
  min_size = 1
  max_size = 3
  
  tags = {
    Type = "AutoScaling"
  }
}

# Custom Domain (Optional)
resource "aws_apprunner_custom_domain_association" "frontend" {
  count = var.custom_domain != "" ? 1 : 0
  
  domain_name = var.custom_domain
  service_arn = aws_apprunner_service.streamlit_frontend.arn
  
  enable_www_subdomain = true
}

# VPC Connector for App Runner (Optional - for private resources)
resource "aws_apprunner_vpc_connector" "frontend" {
  count = var.create_vpc_connector ? 1 : 0
  
  vpc_connector_name = "${var.project_name}-frontend-connector"
  subnets            = var.private_subnet_ids
  security_groups    = [aws_security_group.apprunner[0].id]
  
  tags = {
    Type = "VPCConnector"
  }
}

# Security Group for App Runner VPC Connector
resource "aws_security_group" "apprunner" {
  count = var.create_vpc_connector ? 1 : 0
  
  name_prefix = "${var.project_name}-apprunner-"
  vpc_id      = var.vpc_id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Type = "SecurityGroup"
  }
}