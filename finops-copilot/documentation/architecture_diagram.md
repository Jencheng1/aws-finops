# FinOps Copilot Architecture Diagram Documentation

## Overview

The FinOps Copilot architecture is designed as a multi-agent system powered by AWS Bedrock that provides comprehensive AWS cost optimization insights and recommendations. The system leverages specialized agents, Model Context Protocol (MCP) servers, and Agent-to-Agent (A2A) communication to analyze AWS costs, resource utilization, and tagging compliance, and generate actionable cost-saving recommendations.

## Architecture Components

![FinOps Copilot Architecture](/home/ubuntu/finops-copilot-presentation/images/finops_copilot_architecture.png)

### 1. User Interface Layer

- **Streamlit Dashboard**: Interactive web application that provides visualizations of cost data, optimization recommendations, and executive summaries.
- **Features**:
  - Interactive cost trend visualizations
  - Service breakdown charts
  - Optimization recommendation cards
  - Tagging compliance reports
  - Exportable executive summaries

### 2. Orchestrator Layer

- **AWS Bedrock Orchestrator Agent**: Central coordinator that manages the workflow between all specialized agents.
- **Responsibilities**:
  - Receives user queries and requests
  - Delegates tasks to appropriate service and strategy agents
  - Aggregates results from multiple agents
  - Prioritizes optimization recommendations based on potential savings
  - Manages the overall optimization workflow

### 3. Agent Layer

#### Service Agents

- **EC2 Agent**: Specializes in compute resource optimization.
  - Analyzes EC2 instance utilization patterns
  - Recommends right-sizing opportunities
  - Identifies Reserved Instance and Savings Plan opportunities
  - Detects idle or underutilized instances

- **S3 Agent**: Specializes in storage optimization.
  - Analyzes S3 bucket usage patterns
  - Recommends appropriate storage classes
  - Identifies lifecycle policy opportunities
  - Detects unused or redundant buckets

- **RDS Agent**: Specializes in database optimization.
  - Analyzes database performance metrics
  - Recommends appropriate instance types
  - Identifies storage optimization opportunities
  - Detects idle or underutilized databases

#### Strategy Agents

- **Tagging Agent**: Specializes in resource tagging and cost allocation.
  - Analyzes tagging compliance across resources
  - Identifies resources with missing or incorrect tags
  - Recommends tagging policies
  - Improves cost allocation accuracy

- **Forecasting Agent**: Specializes in cost prediction and trend analysis.
  - Analyzes historical cost patterns
  - Predicts future costs based on current usage
  - Identifies potential cost spikes
  - Recommends budget adjustments

### 4. MCP Server Layer

- **Cost Explorer MCP Server**: Provides access to AWS Cost Explorer data.
  - Retrieves detailed cost and usage data
  - Processes historical cost trends
  - Formats data for agent consumption

- **CloudWatch MCP Server**: Provides access to AWS CloudWatch metrics.
  - Retrieves resource utilization metrics
  - Processes performance data
  - Formats metrics for agent consumption

- **Tagging MCP Server**: Provides access to AWS resource tagging data.
  - Retrieves resource tag information
  - Processes tagging compliance data
  - Formats tagging data for agent consumption

### 5. External Integration Layer

- **Third-Party FinOps Tools**:
  - CloudHealth: Imports cost data and optimization recommendations
  - Cloudability: Pulls rightsizing recommendations and cost reports
  - Spot.io: Leverages spot instance optimization opportunities

- **AWS Native Services**:
  - AWS Trusted Advisor: Incorporates cost optimization checks
  - AWS Health Dashboard: Monitors service health events

### 6. AWS Services Layer

- **AWS Cost Explorer**: Provides detailed cost and usage data
- **AWS CloudWatch**: Provides resource utilization metrics
- **AWS Resource Groups & Tag Editor**: Provides resource tagging information
- **AWS Trusted Advisor**: Provides cost optimization recommendations

## Data Flow

1. **User Interaction**:
   - User interacts with the Streamlit dashboard to view cost data or request optimization recommendations
   - Dashboard sends requests to the Orchestrator Agent

2. **Task Orchestration**:
   - Orchestrator Agent analyzes the request and determines which specialized agents to engage
   - Orchestrator Agent creates a workflow plan and delegates tasks

3. **Data Acquisition**:
   - Service and Strategy Agents request data from MCP Servers
   - MCP Servers retrieve data from AWS services and external integrations
   - MCP Servers process and format data for agent consumption

4. **Analysis and Recommendation**:
   - Agents analyze the data using AWS Bedrock foundation models
   - Agents generate optimization recommendations
   - Agents communicate findings to the Orchestrator Agent

5. **Result Presentation**:
   - Orchestrator Agent aggregates and prioritizes recommendations
   - Dashboard presents visualizations and actionable insights to the user

## Communication Framework

- **A2A Communication Server**: Facilitates communication between agents
  - Enables message passing between agents
  - Manages agent state and context
  - Ensures secure and reliable communication

- **A2A Client**: Enables agents to communicate with each other
  - Provides a standardized interface for agent communication
  - Handles message formatting and routing
  - Manages communication errors and retries

## Deployment Architecture

The FinOps Copilot system is deployed using the following AWS services:

- **AWS Lambda**: Hosts the Orchestrator Agent, Service Agents, Strategy Agents, and MCP Servers
- **Amazon API Gateway**: Provides RESTful API endpoints for the Streamlit dashboard
- **AWS App Runner**: Hosts the Streamlit dashboard
- **Amazon S3**: Stores static assets and exported reports
- **AWS IAM**: Manages permissions and access control
- **AWS Secrets Manager**: Stores API keys and credentials for external integrations

## Security Considerations

- **IAM Roles**: Each component has a specific IAM role with least privilege permissions
- **API Authentication**: API Gateway endpoints are secured with API keys and IAM authentication
- **Data Encryption**: All data is encrypted in transit and at rest
- **Secrets Management**: API keys and credentials are stored in AWS Secrets Manager
- **Access Logging**: All API calls and data access are logged for audit purposes

## Scalability Considerations

- **Lambda Auto-scaling**: AWS Lambda functions automatically scale based on demand
- **API Gateway Throttling**: API Gateway endpoints are configured with appropriate throttling limits
- **App Runner Scaling**: AWS App Runner service scales based on traffic patterns
- **Cost Control**: Resource limits and budgets are set to prevent unexpected costs

## Monitoring and Logging

- **CloudWatch Logs**: All components log to CloudWatch Logs
- **CloudWatch Metrics**: Custom metrics are published to CloudWatch
- **CloudWatch Alarms**: Alarms are configured for critical metrics
- **X-Ray Tracing**: Distributed tracing is enabled for troubleshooting

## Disaster Recovery

- **Backup Strategy**: Regular backups of configuration and data
- **Recovery Procedures**: Documented procedures for component recovery
- **Multi-Region Considerations**: Options for multi-region deployment for high availability

## Future Enhancements

- **Additional Service Agents**: Expand to cover more AWS services (Lambda, DynamoDB, etc.)
- **Advanced ML Models**: Incorporate more sophisticated machine learning models for prediction
- **Automated Remediation**: Implement automated remediation of identified issues
- **Multi-Cloud Support**: Extend to support other cloud providers (Azure, GCP)
