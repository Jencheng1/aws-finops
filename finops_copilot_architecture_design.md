# FinOps Copilot: Detailed Architecture Design

## 1. Introduction

This document provides a detailed architecture design for the FinOps Copilot, an AI-powered multi-agent system for AWS cost optimization. It expands upon the high-level architecture, detailing each component, their interactions, and the underlying technologies.

## 2. System Components

The FinOps Copilot is composed of the following key components:

- **Streamlit Frontend**: The user interface for interacting with the system.
- **Orchestrator Agent**: The central agent that coordinates all other agents and tasks.
- **Service Agents**: Specialized agents for analyzing specific AWS services (EC2, S3, RDS).
- **Strategy Agents**: Agents focused on cross-service optimization strategies.
- **MCP Servers**: Provide a standardized interface to AWS services (Cost Explorer, CloudWatch, Tagging).
- **AWS Lambda Functions**: Serverless functions for agent actions and data processing.
- **External FinOps Tools**: Integration with third-party tools like Apito.

## 3. Detailed Component Architecture

### 3.1. Streamlit Frontend

The frontend will be a web application built using Streamlit. It will provide the following functionalities:

-   **User Authentication**: Secure login for accessing the dashboard.
-   **Cost Analysis Dashboard**: Interactive visualizations of AWS costs, trends, and forecasts.
-   **Recommendations Panel**: A list of actionable cost-saving recommendations.
-   **Query Interface**: A chat-like interface for making specific cost-related queries to the Orchestrator Agent.

### 3.2. Orchestrator Agent

The Orchestrator Agent will be implemented as an AWS Bedrock agent. Its primary responsibilities are:

-   **Task Decomposition**: Breaking down user queries into smaller, manageable tasks.
-   **Agent Delegation**: Assigning tasks to the appropriate Service or Strategy Agents.
-   **Result Synthesis**: Aggregating the results from different agents and formulating a comprehensive response.
-   **State Management**: Maintaining the context of the conversation with the user.

### 3.3. Service Agents

Service Agents are specialized AWS Bedrock agents, each focusing on a specific AWS service. They will be implemented with the following capabilities:

-   **EC2 Agent**: Analyzes EC2 instance usage, identifies idle or underutilized instances, and recommends right-sizing opportunities.
-   **S3 Agent**: Analyzes S3 storage classes, identifies opportunities for cost savings through lifecycle policies, and flags infrequently accessed data.
-   **RDS Agent**: Analyzes RDS instance usage, recommends right-sizing, and identifies idle database instances.

### 3.4. Strategy Agents

Strategy Agents are also AWS Bedrock agents, but they focus on cross-service optimization strategies:

-   **Reserved Instance/Savings Plans Agent**: Analyzes usage patterns and recommends the optimal Reserved Instance or Savings Plans portfolio.
-   **Tagging Compliance Agent**: Analyzes resource tags and identifies resources that are not compliant with the organization's tagging policy.

### 3.5. MCP Servers

Model Context Protocol (MCP) servers will be implemented to provide a standardized interface to various AWS services. This decouples the agents from the underlying data sources.

-   **Cost Explorer MCP Server**: Exposes AWS Cost Explorer data through a simple API.
-   **CloudWatch MCP Server**: Provides access to CloudWatch metrics for resource utilization.
-   **Tagging MCP Server**: Allows agents to query resource tags.

### 3.6. AWS Lambda Functions

AWS Lambda functions will be used to implement the action groups for the Bedrock agents. These functions will contain the business logic for interacting with the MCP servers and processing the data.

### 3.7. External FinOps Tools

The system will integrate with external FinOps tools like Apito to enhance its capabilities. This will be done through API calls from the Lambda functions.

## 4. Data Flow

1.  The user interacts with the Streamlit frontend, submitting a query.
2.  The Streamlit app sends the query to the Orchestrator Agent.
3.  The Orchestrator Agent decomposes the query and delegates tasks to the appropriate Service and Strategy Agents.
4.  The agents invoke their action groups, which are implemented as AWS Lambda functions.
5.  The Lambda functions query the MCP servers to retrieve the necessary data from AWS services.
6.  The MCP servers return the data to the Lambda functions.
7.  The Lambda functions process the data and return the results to the agents.
8.  The agents analyze the results and send their findings back to the Orchestrator Agent.
9.  The Orchestrator Agent synthesizes the findings and generates a comprehensive response.
10. The response is sent back to the Streamlit frontend and displayed to the user.

## 5. Technology Stack

-   **Frontend**: Streamlit
-   **Backend**: AWS Bedrock, AWS Lambda
-   **Programming Language**: Python
-   **Infrastructure**: AWS (S3, IAM, etc.)
-   **API**: Apito (for external integration)

This detailed architecture provides a solid foundation for building a robust and scalable FinOps Copilot system.
