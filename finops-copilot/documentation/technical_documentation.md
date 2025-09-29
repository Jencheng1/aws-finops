# FinOps Copilot Technical Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
   - [Streamlit Frontend](#streamlit-frontend)
   - [AWS Bedrock Agents](#aws-bedrock-agents)
   - [Model Context Protocol (MCP) Servers](#model-context-protocol-mcp-servers)
   - [Agent-to-Agent (A2A) Communication](#agent-to-agent-a2a-communication)
   - [External Integrations](#external-integrations)
4. [Data Flow](#data-flow)
5. [Deployment Architecture](#deployment-architecture)
6. [Security Considerations](#security-considerations)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Scaling Considerations](#scaling-considerations)
9. [Development and Testing](#development-and-testing)
10. [Troubleshooting](#troubleshooting)

## Introduction

FinOps Copilot is an AI-powered multi-agent system built on AWS Bedrock that provides comprehensive AWS cost optimization insights and recommendations. The system leverages specialized agents, Model Context Protocol (MCP) servers, and Agent-to-Agent (A2A) communication to analyze AWS costs, resource utilization, and tagging compliance, and generate actionable cost-saving recommendations.

This document provides technical details about the system architecture, components, data flow, deployment, security, and operational aspects of the FinOps Copilot system.

## System Architecture

The FinOps Copilot system is designed with a multi-layered architecture:

![FinOps Copilot Architecture](/home/ubuntu/finops-copilot/documentation/diagrams/detailed_architecture.png)

The system consists of the following main components:

1. **User Interface Layer**: Streamlit dashboard for user interaction
2. **Orchestrator Layer**: Central AWS Bedrock agent that coordinates the system
3. **Agent Layer**: Specialized AWS Bedrock agents for different services and strategies
4. **MCP Server Layer**: Model Context Protocol servers for data access
5. **External Integration Layer**: Connections to third-party FinOps tools
6. **AWS Services Layer**: Integration with native AWS services

## Component Details

### Streamlit Frontend

The Streamlit frontend provides an interactive web interface for users to interact with the FinOps Copilot system.

**Key Features:**

- Interactive cost trend visualizations
- Service breakdown charts
- Optimization recommendation cards
- Tagging compliance reports
- Exportable executive summaries

**Implementation Details:**

```python
# Key frontend components in app.py
import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import json

# API endpoint configuration
API_ENDPOINT = "https://api.finops-copilot.example.com/v1"

# Authentication setup
def get_auth_header():
    return {"Authorization": f"Bearer {st.session_state.api_token}"}

# Dashboard layout
st.set_page_config(page_title="FinOps Copilot", layout="wide")
st.title("FinOps Copilot Dashboard")

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Overview", "Cost Analysis", "Recommendations", "Tagging Compliance", "Settings"]
)

# Cost trend visualization example
if page == "Overview" or page == "Cost Analysis":
    st.subheader("AWS Cost Trends")
    
    # Get cost data from API
    response = requests.get(f"{API_ENDPOINT}/costs/trends", headers=get_auth_header())
    cost_data = response.json()
    
    # Create DataFrame
    df = pd.DataFrame(cost_data)
    
    # Create visualization
    fig = px.line(
        df, 
        x="date", 
        y="cost", 
        color="service",
        title="Monthly AWS Costs by Service"
    )
    st.plotly_chart(fig, use_container_width=True)

# Recommendations section
if page == "Overview" or page == "Recommendations":
    st.subheader("Cost Optimization Recommendations")
    
    # Get recommendations from API
    response = requests.get(f"{API_ENDPOINT}/recommendations", headers=get_auth_header())
    recommendations = response.json()
    
    # Display recommendations
    for rec in recommendations:
        with st.expander(f"{rec['title']} - Estimated Savings: ${rec['estimated_savings']:,.2f}"):
            st.write(f"**Service:** {rec['service']}")
            st.write(f"**Impact:** {rec['impact']}")
            st.write(f"**Effort:** {rec['effort']}")
            st.write(f"**Description:** {rec['description']}")
            st.write(f"**Implementation Steps:**")
            for i, step in enumerate(rec['implementation_steps']):
                st.write(f"{i+1}. {step}")
```

### AWS Bedrock Agents

The system uses AWS Bedrock agents to provide AI-powered analysis and recommendations.

**Agent Types:**

1. **Orchestrator Agent**: Central coordinator that manages the workflow between all specialized agents.
2. **Service Agents**: Specialized agents for specific AWS services.
   - EC2 Agent: Analyzes compute resource utilization and costs
   - S3 Agent: Analyzes storage usage patterns and costs
   - RDS Agent: Analyzes database performance and costs
3. **Strategy Agents**: Specialized agents for cross-service optimization strategies.
   - Tagging Agent: Analyzes resource tagging compliance
   - Forecasting Agent: Predicts future costs based on historical data

**Agent Configuration Example:**

```json
{
  "agentId": "ec2-agent",
  "agentName": "EC2 Optimization Agent",
  "description": "Analyzes EC2 instance utilization and recommends optimization opportunities",
  "foundationModel": "anthropic.claude-v2",
  "instruction": "You are an EC2 optimization specialist. Analyze EC2 instance utilization data and recommend right-sizing, reserved instances, and other cost-saving opportunities.",
  "actionGroups": [
    {
      "actionGroupName": "EC2Analysis",
      "description": "Actions for analyzing EC2 instances",
      "actions": [
        {
          "actionName": "analyzeUtilization",
          "description": "Analyze EC2 instance utilization metrics",
          "parameters": {
            "instanceId": {
              "type": "string",
              "description": "EC2 instance ID"
            },
            "timeRange": {
              "type": "string",
              "description": "Time range for analysis (e.g., 7d, 30d)"
            }
          },
          "handler": "lambda:ec2-agent-analyze-utilization"
        },
        {
          "actionName": "recommendRightSizing",
          "description": "Generate right-sizing recommendations",
          "parameters": {
            "instanceId": {
              "type": "string",
              "description": "EC2 instance ID"
            }
          },
          "handler": "lambda:ec2-agent-recommend-right-sizing"
        }
      ]
    }
  ],
  "customerEncryptionKeyArn": "arn:aws:kms:us-east-1:123456789012:key/abcd1234-a123-456a-a12b-a123b4cd56ef"
}
```

### Model Context Protocol (MCP) Servers

MCP servers provide a standardized way for agents to access and process AWS cost and resource data.

**MCP Server Types:**

1. **Cost Explorer MCP Server**: Provides access to AWS Cost Explorer data
2. **CloudWatch MCP Server**: Provides access to AWS CloudWatch metrics
3. **Tagging MCP Server**: Provides access to AWS resource tagging data

**MCP Server Implementation Example:**

```python
# Cost Explorer MCP Server Lambda Function
import boto3
import json
import os
from datetime import datetime, timedelta

# Initialize AWS clients
cost_explorer = boto3.client('ce')
dynamodb = boto3.resource('dynamodb')
cache_table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])

def lambda_handler(event, context):
    """
    Handle MCP requests for Cost Explorer data
    """
    try:
        # Extract request parameters
        request_type = event.get('requestType')
        parameters = event.get('parameters', {})
        
        # Check cache for recent results
        cache_key = f"{request_type}:{json.dumps(parameters)}"
        cache_item = get_from_cache(cache_key)
        
        if cache_item:
            return {
                'statusCode': 200,
                'body': cache_item['data']
            }
        
        # Process different request types
        if request_type == 'getCostAndUsage':
            result = get_cost_and_usage(parameters)
        elif request_type == 'getCostForecast':
            result = get_cost_forecast(parameters)
        elif request_type == 'getReservationUtilization':
            result = get_reservation_utilization(parameters)
        elif request_type == 'getSavingsPlansUtilization':
            result = get_savings_plans_utilization(parameters)
        else:
            return {
                'statusCode': 400,
                'body': f"Unsupported request type: {request_type}"
            }
        
        # Cache results
        store_in_cache(cache_key, result)
        
        return {
            'statusCode': 200,
            'body': result
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error processing request: {str(e)}"
        }

def get_cost_and_usage(parameters):
    """
    Get cost and usage data from AWS Cost Explorer
    """
    time_period = parameters.get('timePeriod', {})
    granularity = parameters.get('granularity', 'MONTHLY')
    metrics = parameters.get('metrics', ['UnblendedCost'])
    group_by = parameters.get('groupBy', [])
    
    # Set default time period if not provided
    if not time_period:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        time_period = {
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        }
    
    # Build request parameters
    request_params = {
        'TimePeriod': time_period,
        'Granularity': granularity,
        'Metrics': metrics
    }
    
    # Add GroupBy if specified
    if group_by:
        request_params['GroupBy'] = group_by
    
    # Call Cost Explorer API
    response = cost_explorer.get_cost_and_usage(**request_params)
    
    return response

# Additional helper functions for other request types...

def get_from_cache(key):
    """
    Get item from cache if it exists and is not expired
    """
    response = cache_table.get_item(Key={'cacheKey': key})
    
    if 'Item' in response:
        item = response['Item']
        expiration = item.get('expiration', 0)
        
        # Check if cache item is still valid
        if expiration > int(datetime.now().timestamp()):
            return item
    
    return None

def store_in_cache(key, data, ttl_seconds=3600):
    """
    Store item in cache with expiration
    """
    expiration = int(datetime.now().timestamp()) + ttl_seconds
    
    cache_table.put_item(
        Item={
            'cacheKey': key,
            'data': data,
            'expiration': expiration
        }
    )
```

### Agent-to-Agent (A2A) Communication

The A2A communication framework enables agents to share insights and collaborate on optimization recommendations.

**A2A Server Implementation Example:**

```python
# A2A Communication Server Lambda Function
import boto3
import json
import os
import uuid
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
message_table = dynamodb.Table(os.environ['MESSAGE_TABLE_NAME'])
subscription_table = dynamodb.Table(os.environ['SUBSCRIPTION_TABLE_NAME'])

def lambda_handler(event, context):
    """
    Handle A2A communication requests
    """
    try:
        # Extract request parameters
        action = event.get('action')
        
        if action == 'publish':
            return publish_message(event)
        elif action == 'subscribe':
            return subscribe_to_topic(event)
        elif action == 'unsubscribe':
            return unsubscribe_from_topic(event)
        elif action == 'getMessages':
            return get_messages(event)
        else:
            return {
                'statusCode': 400,
                'body': f"Unsupported action: {action}"
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error processing request: {str(e)}"
        }

def publish_message(event):
    """
    Publish a message to a topic
    """
    topic = event.get('topic')
    message = event.get('message')
    sender = event.get('sender')
    
    if not topic or not message or not sender:
        return {
            'statusCode': 400,
            'body': "Missing required parameters: topic, message, sender"
        }
    
    # Create message record
    message_id = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    
    message_item = {
        'messageId': message_id,
        'topic': topic,
        'message': message,
        'sender': sender,
        'timestamp': timestamp
    }
    
    # Store message in DynamoDB
    message_table.put_item(Item=message_item)
    
    return {
        'statusCode': 200,
        'body': {
            'messageId': message_id,
            'timestamp': timestamp
        }
    }

def subscribe_to_topic(event):
    """
    Subscribe an agent to a topic
    """
    topic = event.get('topic')
    subscriber = event.get('subscriber')
    
    if not topic or not subscriber:
        return {
            'statusCode': 400,
            'body': "Missing required parameters: topic, subscriber"
        }
    
    # Create subscription record
    subscription_id = f"{subscriber}:{topic}"
    timestamp = int(datetime.now().timestamp())
    
    subscription_item = {
        'subscriptionId': subscription_id,
        'topic': topic,
        'subscriber': subscriber,
        'timestamp': timestamp
    }
    
    # Store subscription in DynamoDB
    subscription_table.put_item(Item=subscription_item)
    
    return {
        'statusCode': 200,
        'body': {
            'subscriptionId': subscription_id,
            'timestamp': timestamp
        }
    }

def unsubscribe_from_topic(event):
    """
    Unsubscribe an agent from a topic
    """
    topic = event.get('topic')
    subscriber = event.get('subscriber')
    
    if not topic or not subscriber:
        return {
            'statusCode': 400,
            'body': "Missing required parameters: topic, subscriber"
        }
    
    # Delete subscription record
    subscription_id = f"{subscriber}:{topic}"
    
    subscription_table.delete_item(
        Key={
            'subscriptionId': subscription_id
        }
    )
    
    return {
        'statusCode': 200,
        'body': {
            'status': 'unsubscribed',
            'timestamp': int(datetime.now().timestamp())
        }
    }

def get_messages(event):
    """
    Get messages for a subscriber
    """
    subscriber = event.get('subscriber')
    since_timestamp = event.get('sinceTimestamp', 0)
    
    if not subscriber:
        return {
            'statusCode': 400,
            'body': "Missing required parameter: subscriber"
        }
    
    # Get subscriptions for the subscriber
    subscriptions = get_subscriptions_for_subscriber(subscriber)
    
    if not subscriptions:
        return {
            'statusCode': 200,
            'body': {
                'messages': []
            }
        }
    
    # Get messages for each subscription
    all_messages = []
    
    for subscription in subscriptions:
        topic = subscription['topic']
        messages = get_messages_for_topic(topic, since_timestamp)
        all_messages.extend(messages)
    
    # Sort messages by timestamp
    all_messages.sort(key=lambda x: x['timestamp'])
    
    return {
        'statusCode': 200,
        'body': {
            'messages': all_messages
        }
    }

def get_subscriptions_for_subscriber(subscriber):
    """
    Get all subscriptions for a subscriber
    """
    response = subscription_table.scan(
        FilterExpression='subscriber = :subscriber',
        ExpressionAttributeValues={
            ':subscriber': subscriber
        }
    )
    
    return response.get('Items', [])

def get_messages_for_topic(topic, since_timestamp):
    """
    Get messages for a topic since a timestamp
    """
    response = message_table.scan(
        FilterExpression='topic = :topic AND #ts > :since_timestamp',
        ExpressionAttributeNames={
            '#ts': 'timestamp'
        },
        ExpressionAttributeValues={
            ':topic': topic,
            ':since_timestamp': since_timestamp
        }
    )
    
    return response.get('Items', [])
```

### External Integrations

The system integrates with third-party FinOps tools to enhance its optimization capabilities.

**Integration Types:**

1. **CloudHealth**: Imports cost data and optimization recommendations
2. **Cloudability**: Pulls rightsizing recommendations and cost reports
3. **Spot.io**: Leverages spot instance optimization opportunities
4. **AWS Trusted Advisor**: Incorporates cost optimization checks

**External Integration Example:**

```python
# CloudHealth Integration Module
import requests
import json
import os
import boto3
from datetime import datetime, timedelta

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')

# Get API key from Secrets Manager
def get_api_key():
    secret_name = os.environ['CLOUDHEALTH_SECRET_NAME']
    response = secretsmanager.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret['api_key']

# CloudHealth API base URL
BASE_URL = "https://chapi.cloudhealthtech.com/v1"

def get_assets(asset_type, params=None):
    """
    Get assets from CloudHealth
    """
    api_key = get_api_key()
    
    url = f"{BASE_URL}/assets/{asset_type}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

def get_ec2_recommendations():
    """
    Get EC2 rightsizing recommendations from CloudHealth
    """
    api_key = get_api_key()
    
    url = f"{BASE_URL}/recommendations/ec2"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()

def get_cost_history(start_date, end_date, interval="daily"):
    """
    Get cost history from CloudHealth
    """
    api_key = get_api_key()
    
    url = f"{BASE_URL}/olap_reports/cost/history"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "interval": interval
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

def map_recommendations_to_internal_format(cloudhealth_recommendations):
    """
    Map CloudHealth recommendations to internal format
    """
    mapped_recommendations = []
    
    for rec in cloudhealth_recommendations.get('recommendations', []):
        mapped_rec = {
            'source': 'CloudHealth',
            'service': 'EC2',
            'resourceId': rec.get('instance_id'),
            'title': f"Resize {rec.get('instance_id')} from {rec.get('current_type')} to {rec.get('recommended_type')}",
            'description': rec.get('description', 'Resize EC2 instance based on utilization patterns'),
            'estimated_savings': rec.get('estimated_monthly_savings', 0),
            'impact': 'Medium',
            'effort': 'Low',
            'implementation_steps': [
                f"Review utilization metrics for {rec.get('instance_id')}",
                f"Stop the instance",
                f"Change instance type from {rec.get('current_type')} to {rec.get('recommended_type')}",
                f"Start the instance",
                "Verify application performance after resize"
            ]
        }
        
        mapped_recommendations.append(mapped_rec)
    
    return mapped_recommendations
```

## Data Flow

The data flow through the FinOps Copilot system follows a specific pattern:

![Data Flow Diagram](/home/ubuntu/finops-copilot/documentation/diagrams/data_flow.png)

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

## Deployment Architecture

The FinOps Copilot system is deployed using a serverless architecture on AWS:

![Deployment Architecture](/home/ubuntu/finops-copilot/documentation/diagrams/deployment_architecture.png)

**Key AWS Services Used:**

- **AWS Lambda**: Hosts the Orchestrator Agent, Service Agents, Strategy Agents, and MCP Servers
- **Amazon API Gateway**: Provides RESTful API endpoints for the Streamlit dashboard
- **AWS App Runner**: Hosts the Streamlit dashboard
- **Amazon S3**: Stores static assets and exported reports
- **AWS IAM**: Manages permissions and access control
- **AWS Secrets Manager**: Stores API keys and credentials for external integrations
- **Amazon DynamoDB**: Stores agent state and communication messages
- **AWS CloudWatch**: Monitors system performance and logs
- **AWS CloudFormation**: Manages infrastructure as code

**Deployment Process:**

1. Create AWS resources using CloudFormation templates
2. Deploy Lambda functions for agents and MCP servers
3. Configure API Gateway endpoints
4. Deploy Streamlit dashboard to AWS App Runner
5. Configure IAM roles and permissions
6. Set up monitoring and logging

## Security Considerations

The FinOps Copilot system implements several security measures:

1. **Authentication and Authorization**:
   - API Gateway endpoints secured with API keys and IAM authentication
   - JWT-based authentication for dashboard users
   - IAM roles with least privilege permissions for all components

2. **Data Protection**:
   - All data encrypted in transit using TLS
   - All data encrypted at rest using AWS KMS
   - Sensitive data (API keys, credentials) stored in AWS Secrets Manager

3. **Network Security**:
   - API Gateway endpoints configured with appropriate resource policies
   - Lambda functions deployed within VPC when necessary
   - Security groups and network ACLs configured to restrict access

4. **Logging and Auditing**:
   - All API calls logged to CloudTrail
   - All component logs sent to CloudWatch Logs
   - Log retention policies configured according to compliance requirements

5. **Compliance**:
   - System designed to comply with relevant security standards
   - Regular security assessments and penetration testing
   - Automated security scanning of code and dependencies

## Monitoring and Logging

The FinOps Copilot system includes comprehensive monitoring and logging:

1. **CloudWatch Metrics**:
   - Custom metrics for each component
   - Dashboards for system performance monitoring
   - Alarms for critical metrics

2. **CloudWatch Logs**:
   - Centralized logging for all components
   - Log groups organized by component
   - Log retention policies configured

3. **X-Ray Tracing**:
   - Distributed tracing for request flows
   - Service map for visualizing component interactions
   - Trace analysis for performance optimization

4. **Alerting**:
   - SNS topics for alerting on critical issues
   - Integration with incident management systems
   - Escalation policies for different alert types

## Scaling Considerations

The FinOps Copilot system is designed to scale with increasing workload:

1. **Lambda Auto-scaling**:
   - AWS Lambda functions automatically scale based on demand
   - Concurrency limits configured to prevent resource exhaustion

2. **API Gateway Throttling**:
   - API Gateway endpoints configured with appropriate throttling limits
   - Usage plans to manage API access

3. **App Runner Scaling**:
   - AWS App Runner service scales based on traffic patterns
   - Auto-scaling configuration for the Streamlit dashboard

4. **DynamoDB Scaling**:
   - On-demand capacity mode for unpredictable workloads
   - Auto-scaling for provisioned capacity mode

5. **Cost Control**:
   - Resource limits and budgets to prevent unexpected costs
   - Cost allocation tags for tracking component costs

## Development and Testing

The development and testing process for the FinOps Copilot system includes:

1. **Development Environment**:
   - Local development environment with Docker containers
   - AWS SAM CLI for local Lambda testing
   - Streamlit development server for frontend testing

2. **Testing Strategy**:
   - Unit tests for individual components
   - Integration tests for component interactions
   - End-to-end tests for complete workflows
   - Performance tests for system scalability

3. **CI/CD Pipeline**:
   - GitHub Actions for continuous integration
   - AWS CodePipeline for continuous deployment
   - Automated testing in the pipeline
   - Deployment approval gates for production

4. **Code Quality**:
   - Linting and static analysis
   - Code reviews for all changes
   - Security scanning for vulnerabilities
   - Documentation requirements

## Troubleshooting

Common issues and troubleshooting steps:

1. **API Gateway Errors**:
   - Check API Gateway logs in CloudWatch
   - Verify API key and authentication
   - Check API Gateway throttling limits

2. **Lambda Errors**:
   - Check Lambda function logs in CloudWatch
   - Verify IAM permissions
   - Check Lambda function timeouts and memory limits

3. **Agent Communication Issues**:
   - Check A2A Server logs
   - Verify DynamoDB table access
   - Check message format and structure

4. **MCP Server Issues**:
   - Check MCP Server logs
   - Verify AWS service access permissions
   - Check external API connectivity

5. **Dashboard Issues**:
   - Check App Runner service logs
   - Verify API endpoint configuration
   - Check browser console for JavaScript errors
