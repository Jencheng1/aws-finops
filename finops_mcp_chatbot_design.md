# FinOps MCP Integration and AWS Cost Intelligence Chatbot Design

## Overview

This document outlines the design for integrating IBM Cloudability and Apptio with AWS Bedrock using Model Context Protocol (MCP), and building a chatbot interface for AWS cost and resource intelligence. The solution will provide actionable insights and strategic cost-saving recommendations, including AWS Savings Plans and identification of idle resources.

## Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  AWS Bedrock    │◄────┤  MCP Servers    │◄────┤  Data Sources   │
│  Agents         │     │                 │     │                 │
│                 │     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │                                       ▲
         │                                       │
         │                                       │
         ▼                                       │
┌─────────────────┐                     ┌────────┴────────┐
│                 │                     │                 │
│  Streamlit      │                     │  AWS Services   │
│  Chatbot UI     │                     │  & APIs         │
│                 │                     │                 │
└─────────────────┘                     └─────────────────┘
```

### Components

1. **MCP Servers**:
   - IBM Cloudability MCP Server
   - Apptio MCP Server
   - AWS Cost Explorer MCP Server
   - AWS Resource Intelligence MCP Server

2. **AWS Bedrock Agents**:
   - Orchestrator Agent
   - Cost Analysis Agent
   - Resource Optimization Agent
   - Savings Plan Recommendation Agent

3. **Chatbot Interface**:
   - Streamlit-based web application
   - Natural language query processing
   - Interactive visualizations
   - Actionable recommendations

4. **Data Sources**:
   - IBM Cloudability API
   - Apptio API
   - AWS Cost Explorer API
   - AWS Resource Groups Tagging API
   - AWS Compute Optimizer API
   - AWS Trusted Advisor API

## MCP Server Implementations

### 1. IBM Cloudability MCP Server

#### Capabilities

- **Resources**:
  - Cost data
  - Usage data
  - Tagging compliance data
  - Anomaly detection data

- **Tools**:
  - `get_cost_data`: Retrieve cost data for a specified time period
  - `get_usage_data`: Retrieve usage data for a specified time period
  - `get_tagging_compliance`: Retrieve tagging compliance information
  - `get_anomalies`: Retrieve detected cost anomalies

#### Implementation

```python
from mcp.server.fastmcp import FastMCP
import httpx

# Initialize FastMCP server
mcp = FastMCP("cloudability")

# Constants
CLOUDABILITY_API_BASE = "https://api.cloudability.com/v3"

@mcp.tool()
async def get_cost_data(start_date: str, end_date: str, granularity: str = "daily") -> str:
    """Get cost data from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Data granularity (daily, monthly)
    """
    # Implementation details for accessing Cloudability API
    # ...
    
@mcp.tool()
async def get_usage_data(start_date: str, end_date: str, service: str = None) -> str:
    """Get usage data from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        service: Optional AWS service filter
    """
    # Implementation details for accessing Cloudability API
    # ...

# Additional tools...

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

### 2. Apptio MCP Server

#### Capabilities

- **Resources**:
  - Cost data
  - Budget data
  - Forecast data
  - Optimization recommendations

- **Tools**:
  - `get_cost_data`: Retrieve cost data from Apptio
  - `get_budget_data`: Retrieve budget information
  - `get_forecast_data`: Retrieve cost forecasts
  - `get_optimization_recommendations`: Retrieve cost optimization recommendations

#### Implementation

```python
from mcp.server.fastmcp import FastMCP
import httpx

# Initialize FastMCP server
mcp = FastMCP("apptio")

# Constants
APPTIO_API_BASE = "https://api.apptio.com"

@mcp.tool()
async def get_cost_data(start_date: str, end_date: str) -> str:
    """Get cost data from Apptio.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    # Implementation details for accessing Apptio API
    # ...
    
@mcp.tool()
async def get_budget_data(fiscal_year: str, fiscal_period: str = None) -> str:
    """Get budget data from Apptio.
    
    Args:
        fiscal_year: Fiscal year
        fiscal_period: Optional fiscal period
    """
    # Implementation details for accessing Apptio API
    # ...

# Additional tools...

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

### 3. AWS Cost Explorer MCP Server

#### Capabilities

- **Resources**:
  - Cost and usage data
  - Savings Plans recommendations
  - Reserved Instance recommendations
  - Cost anomalies

- **Tools**:
  - `get_cost_usage`: Retrieve cost and usage data
  - `get_savings_plans_recommendations`: Retrieve Savings Plans recommendations
  - `get_ri_recommendations`: Retrieve Reserved Instance recommendations
  - `get_cost_anomalies`: Retrieve detected cost anomalies

#### Implementation

```python
from mcp.server.fastmcp import FastMCP
import boto3

# Initialize FastMCP server
mcp = FastMCP("aws-cost-explorer")

# Initialize AWS clients
ce_client = boto3.client('ce')
savingsplans_client = boto3.client('savingsplans')

@mcp.tool()
async def get_cost_usage(start_date: str, end_date: str, granularity: str = "DAILY") -> str:
    """Get cost and usage data from AWS Cost Explorer.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Data granularity (DAILY, MONTHLY)
    """
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity=granularity,
        Metrics=['UnblendedCost', 'UsageQuantity']
    )
    
    # Format and return the response
    # ...
    
@mcp.tool()
async def get_savings_plans_recommendations() -> str:
    """Get Savings Plans recommendations from AWS."""
    response = savingsplans_client.describe_savings_plans_offering_rates(
        filters={
            'savingsPlanTypes': ['Compute', 'EC2Instance']
        }
    )
    
    # Format and return the response
    # ...

# Additional tools...

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

### 4. AWS Resource Intelligence MCP Server

#### Capabilities

- **Resources**:
  - EC2 instance data
  - EBS volume data
  - RDS instance data
  - Idle resource data

- **Tools**:
  - `get_idle_ec2_instances`: Identify idle EC2 instances
  - `get_idle_ebs_volumes`: Identify idle EBS volumes
  - `get_idle_rds_instances`: Identify idle RDS instances
  - `get_rightsizing_recommendations`: Get rightsizing recommendations

#### Implementation

```python
from mcp.server.fastmcp import FastMCP
import boto3

# Initialize FastMCP server
mcp = FastMCP("aws-resource-intelligence")

# Initialize AWS clients
ec2_client = boto3.client('ec2')
rds_client = boto3.client('rds')
compute_optimizer_client = boto3.client('compute-optimizer')

@mcp.tool()
async def get_idle_ec2_instances(days: int = 14) -> str:
    """Get idle EC2 instances based on CloudWatch metrics.
    
    Args:
        days: Number of days to look back
    """
    # Implementation to identify idle EC2 instances
    # ...
    
@mcp.tool()
async def get_idle_ebs_volumes() -> str:
    """Get idle EBS volumes that are not attached to any instance."""
    response = ec2_client.describe_volumes(
        Filters=[
            {
                'Name': 'status',
                'Values': ['available']
            }
        ]
    )
    
    # Format and return the response
    # ...

# Additional tools...

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

## AWS Bedrock Agents

### 1. Orchestrator Agent

The Orchestrator Agent coordinates the activities of all other agents and provides a unified interface for the chatbot.

#### Capabilities

- Understand user queries and route to appropriate specialized agents
- Aggregate responses from multiple agents
- Provide a coherent response to the user
- Handle follow-up questions

### 2. Cost Analysis Agent

The Cost Analysis Agent analyzes cost data from multiple sources and provides insights.

#### Capabilities

- Analyze cost trends
- Identify cost drivers
- Compare costs across time periods
- Generate cost reports

### 3. Resource Optimization Agent

The Resource Optimization Agent identifies opportunities to optimize AWS resources.

#### Capabilities

- Identify idle resources
- Provide rightsizing recommendations
- Suggest instance type changes
- Recommend storage optimizations

### 4. Savings Plan Recommendation Agent

The Savings Plan Recommendation Agent provides recommendations for AWS Savings Plans.

#### Capabilities

- Analyze usage patterns
- Recommend optimal Savings Plans
- Calculate potential savings
- Provide implementation guidance

## Chatbot Interface

### Streamlit Application

The chatbot interface will be built using Streamlit, providing a web-based interface for users to interact with the system.

#### Features

- Natural language query input
- Interactive visualizations of cost data
- Actionable recommendations
- Drill-down capabilities for detailed analysis

### Sample Implementation

```python
import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="AWS FinOps Copilot",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display header
st.title("AWS FinOps Copilot")
st.subheader("Your AI-powered cost optimization assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
if prompt := st.chat_input("Ask me about your AWS costs..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call AWS Bedrock agent
            response = call_bedrock_agent(prompt)
            
            # Display response
            st.markdown(response["text"])
            
            # Display visualizations if available
            if "visualizations" in response:
                for viz in response["visualizations"]:
                    if viz["type"] == "bar":
                        df = pd.DataFrame(viz["data"])
                        st.plotly_chart(px.bar(df, x=viz["x"], y=viz["y"], title=viz["title"]))
                    elif viz["type"] == "line":
                        df = pd.DataFrame(viz["data"])
                        st.plotly_chart(px.line(df, x=viz["x"], y=viz["y"], title=viz["title"]))
            
            # Display recommendations if available
            if "recommendations" in response:
                st.subheader("Recommendations")
                for i, rec in enumerate(response["recommendations"]):
                    with st.expander(f"{i+1}. {rec['title']}"):
                        st.markdown(rec["description"])
                        st.markdown(f"**Potential Savings**: ${rec['savings']:,.2f}")
                        st.markdown(f"**Implementation Difficulty**: {rec['difficulty']}")
                        st.markdown(f"**Implementation Steps**:")
                        for step in rec["steps"]:
                            st.markdown(f"- {step}")
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response["text"]})

# Sidebar with filters
with st.sidebar:
    st.header("Filters")
    
    st.subheader("Time Period")
    time_period = st.selectbox(
        "Select time period",
        ["Last 7 days", "Last 30 days", "Last 3 months", "Last 6 months", "Last 12 months", "Custom"]
    )
    
    if time_period == "Custom":
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
    
    st.subheader("Services")
    services = st.multiselect(
        "Select AWS services",
        ["EC2", "S3", "RDS", "Lambda", "EBS", "All"]
    )
    
    st.subheader("Accounts")
    accounts = st.multiselect(
        "Select AWS accounts",
        ["Account 1", "Account 2", "Account 3", "All"]
    )
    
    st.button("Apply Filters")
```

## Integration with AWS Services

### AWS Cost Explorer

The system will integrate with AWS Cost Explorer to retrieve cost and usage data, as well as Savings Plans recommendations.

### AWS Compute Optimizer

The system will integrate with AWS Compute Optimizer to retrieve rightsizing recommendations for EC2 instances, EBS volumes, and Lambda functions.

### AWS Trusted Advisor

The system will integrate with AWS Trusted Advisor to retrieve cost optimization recommendations.

### AWS Resource Groups Tagging API

The system will integrate with AWS Resource Groups Tagging API to retrieve tagging information for resources.

## Implementation Plan

### Phase 1: MCP Server Implementation

1. Implement IBM Cloudability MCP Server
2. Implement Apptio MCP Server
3. Implement AWS Cost Explorer MCP Server
4. Implement AWS Resource Intelligence MCP Server

### Phase 2: AWS Bedrock Agent Implementation

1. Implement Orchestrator Agent
2. Implement Cost Analysis Agent
3. Implement Resource Optimization Agent
4. Implement Savings Plan Recommendation Agent

### Phase 3: Chatbot Interface Implementation

1. Implement Streamlit application
2. Implement natural language query processing
3. Implement interactive visualizations
4. Implement recommendation display

### Phase 4: Testing and Deployment

1. Test MCP servers
2. Test AWS Bedrock agents
3. Test chatbot interface
4. Deploy the solution

## Conclusion

This design document outlines the architecture and implementation details for integrating IBM Cloudability and Apptio with AWS Bedrock using Model Context Protocol (MCP), and building a chatbot interface for AWS cost and resource intelligence. The solution will provide actionable insights and strategic cost-saving recommendations, including AWS Savings Plans and identification of idle resources.
