#!/usr/bin/env python3
"""
AWS Cost Intelligence Chatbot

A Streamlit-based chatbot interface for AWS cost optimization and resource intelligence,
integrating with AWS Bedrock agents and MCP servers for IBM Cloudability and Apptio.
"""

import os
import json
import boto3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Set page configuration
st.set_page_config(
    page_title="AWS FinOps Copilot",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "filters" not in st.session_state:
    st.session_state.filters = {
        "time_period": "Last 30 days",
        "services": [],
        "accounts": [],
        "regions": [],
        "tags": {}
    }

# Helper functions
def get_date_range(time_period: str) -> tuple:
    """Get start and end dates based on time period.
    
    Args:
        time_period: Time period string
        
    Returns:
        Tuple of (start_date, end_date) as strings in YYYY-MM-DD format
    """
    end_date = datetime.now()
    
    if time_period == "Last 7 days":
        start_date = end_date - timedelta(days=7)
    elif time_period == "Last 30 days":
        start_date = end_date - timedelta(days=30)
    elif time_period == "Last 3 months":
        start_date = end_date - timedelta(days=90)
    elif time_period == "Last 6 months":
        start_date = end_date - timedelta(days=180)
    elif time_period == "Last 12 months":
        start_date = end_date - timedelta(days=365)
    else:
        # Default to last 30 days
        start_date = end_date - timedelta(days=30)
    
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def call_bedrock_agent(prompt: str) -> Dict:
    """Call AWS Bedrock agent with the given prompt.
    
    Args:
        prompt: User prompt
        
    Returns:
        Agent response as a dictionary
    """
    # In a real implementation, this would call the AWS Bedrock agent
    # For this demo, we'll return mock data
    
    # Mock cost data
    mock_cost_data = {
        "services": [
            {"name": "EC2", "cost": 1250.45},
            {"name": "S3", "cost": 450.20},
            {"name": "RDS", "cost": 850.75},
            {"name": "Lambda", "cost": 120.30},
            {"name": "Other", "cost": 350.10}
        ],
        "trend": [
            {"date": "2025-08-25", "cost": 95.45},
            {"date": "2025-08-26", "cost": 102.30},
            {"date": "2025-08-27", "cost": 98.75},
            {"date": "2025-08-28", "cost": 105.20},
            {"date": "2025-08-29", "cost": 110.45},
            {"date": "2025-08-30", "cost": 108.30},
            {"date": "2025-08-31", "cost": 115.75},
            {"date": "2025-09-01", "cost": 120.20},
            {"date": "2025-09-02", "cost": 118.45},
            {"date": "2025-09-03", "cost": 125.30},
            {"date": "2025-09-04", "cost": 130.75},
            {"date": "2025-09-05", "cost": 128.20},
            {"date": "2025-09-06", "cost": 135.45},
            {"date": "2025-09-07", "cost": 140.30},
            {"date": "2025-09-08", "cost": 138.75},
            {"date": "2025-09-09", "cost": 145.20},
            {"date": "2025-09-10", "cost": 150.45},
            {"date": "2025-09-11", "cost": 148.30},
            {"date": "2025-09-12", "cost": 155.75},
            {"date": "2025-09-13", "cost": 160.20},
            {"date": "2025-09-14", "cost": 158.45},
            {"date": "2025-09-15", "cost": 165.30},
            {"date": "2025-09-16", "cost": 170.75},
            {"date": "2025-09-17", "cost": 168.20},
            {"date": "2025-09-18", "cost": 175.45},
            {"date": "2025-09-19", "cost": 180.30},
            {"date": "2025-09-20", "cost": 178.75},
            {"date": "2025-09-21", "cost": 185.20},
            {"date": "2025-09-22", "cost": 190.45},
            {"date": "2025-09-23", "cost": 188.30},
            {"date": "2025-09-24", "cost": 195.75}
        ]
    }
    
    # Mock recommendations
    mock_recommendations = [
        {
            "title": "Right-size underutilized EC2 instances",
            "description": "We've identified 12 EC2 instances with average CPU utilization below 10% over the past 30 days. Downsizing these instances could result in significant cost savings.",
            "savings": 450.75,
            "difficulty": "Medium",
            "steps": [
                "Review the list of underutilized instances",
                "Create AMIs of the instances to be downsized",
                "Launch new instances with smaller instance types",
                "Verify application performance on the new instances",
                "Terminate the original instances"
            ]
        },
        {
            "title": "Purchase Savings Plans for consistent EC2 usage",
            "description": "Based on your consistent EC2 usage pattern, purchasing Compute Savings Plans could provide significant savings compared to On-Demand pricing.",
            "savings": 850.20,
            "difficulty": "Low",
            "steps": [
                "Review the Savings Plans recommendation in the AWS Cost Explorer",
                "Choose a 1-year or 3-year commitment term",
                "Select the hourly commitment amount",
                "Purchase the Savings Plans through the AWS Console"
            ]
        },
        {
            "title": "Delete unattached EBS volumes",
            "description": "We've identified 8 EBS volumes that are not attached to any instances. These volumes are incurring charges without providing any value.",
            "savings": 120.50,
            "difficulty": "Low",
            "steps": [
                "Review the list of unattached EBS volumes",
                "Create snapshots of the volumes if needed",
                "Delete the unattached volumes"
            ]
        },
        {
            "title": "Implement S3 Lifecycle policies",
            "description": "Your S3 storage costs could be reduced by implementing lifecycle policies to transition infrequently accessed data to cheaper storage classes.",
            "savings": 250.30,
            "difficulty": "Medium",
            "steps": [
                "Analyze S3 access patterns using S3 Analytics",
                "Create lifecycle policies for buckets with infrequently accessed data",
                "Configure transitions to S3 Standard-IA or S3 Glacier",
                "Monitor storage costs after implementation"
            ]
        }
    ]
    
    # Generate response based on prompt
    if "cost" in prompt.lower() and "breakdown" in prompt.lower():
        return {
            "text": "Here's the breakdown of your AWS costs for the past 30 days. EC2 instances account for the largest portion of your spending at $1,250.45, followed by RDS at $850.75 and S3 at $450.20. Your total cost for this period is $3,021.80, which is 15% higher than the previous 30-day period.",
            "visualizations": [
                {
                    "type": "bar",
                    "data": [{"service": s["name"], "cost": s["cost"]} for s in mock_cost_data["services"]],
                    "x": "service",
                    "y": "cost",
                    "title": "AWS Cost by Service (Last 30 Days)"
                },
                {
                    "type": "line",
                    "data": [{"date": d["date"], "cost": d["cost"]} for d in mock_cost_data["trend"]],
                    "x": "date",
                    "y": "cost",
                    "title": "Daily AWS Cost Trend (Last 30 Days)"
                }
            ]
        }
    elif "savings" in prompt.lower() and "plan" in prompt.lower():
        return {
            "text": "Based on your consistent EC2 usage pattern, I recommend purchasing Compute Savings Plans. With a 1-year commitment, you could save approximately $850.20 per month compared to On-Demand pricing. This represents a 25% reduction in your EC2 costs.",
            "recommendations": [mock_recommendations[1]]
        }
    elif "idle" in prompt.lower() and "resource" in prompt.lower():
        return {
            "text": "I've identified several idle resources that could be optimized or removed to reduce costs. These include 12 underutilized EC2 instances and 8 unattached EBS volumes. By addressing these issues, you could save approximately $571.25 per month.",
            "recommendations": [mock_recommendations[0], mock_recommendations[2]]
        }
    elif "optimization" in prompt.lower() or "recommend" in prompt.lower():
        return {
            "text": "I've analyzed your AWS environment and identified several cost optimization opportunities. These recommendations could save you approximately $1,671.75 per month if fully implemented.",
            "recommendations": mock_recommendations
        }
    else:
        return {
            "text": "I'm your AWS FinOps Copilot, here to help you optimize your AWS costs and resource usage. You can ask me about cost breakdowns, savings opportunities, idle resources, and optimization recommendations. How can I assist you today?"
        }

# Display header
st.title("AWS FinOps Copilot")
st.subheader("Your AI-powered cost optimization assistant")

# Sidebar with filters
with st.sidebar:
    st.header("Filters")
    
    st.subheader("Time Period")
    time_period = st.selectbox(
        "Select time period",
        ["Last 7 days", "Last 30 days", "Last 3 months", "Last 6 months", "Last 12 months", "Custom"],
        index=1
    )
    
    if time_period == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End date", datetime.now())
    else:
        start_date, end_date = get_date_range(time_period)
        st.info(f"Date range: {start_date} to {end_date}")
    
    st.session_state.filters["time_period"] = time_period
    
    st.subheader("Services")
    services = st.multiselect(
        "Select AWS services",
        ["EC2", "S3", "RDS", "Lambda", "CloudFront", "EBS", "ELB", "DynamoDB", "All"],
        default=[]
    )
    st.session_state.filters["services"] = services
    
    st.subheader("Accounts")
    accounts = st.multiselect(
        "Select AWS accounts",
        ["Production", "Development", "Staging", "Testing", "All"],
        default=[]
    )
    st.session_state.filters["accounts"] = accounts
    
    st.subheader("Regions")
    regions = st.multiselect(
        "Select AWS regions",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "All"],
        default=[]
    )
    st.session_state.filters["regions"] = regions
    
    st.subheader("Tags")
    tag_key = st.selectbox(
        "Select tag key",
        ["Environment", "Project", "Team", "CostCenter", "Application"]
    )
    
    tag_values = st.multiselect(
        f"Select {tag_key} values",
        ["Production", "Development", "Staging", "Testing", "Finance", "Marketing", "Engineering", "All"],
        default=[]
    )
    
    if tag_values:
        st.session_state.filters["tags"][tag_key] = tag_values
    
    if st.button("Apply Filters"):
        st.success("Filters applied successfully!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display visualizations if available
        if "visualizations" in message:
            for viz in message["visualizations"]:
                if viz["type"] == "bar":
                    df = pd.DataFrame(viz["data"])
                    fig = px.bar(df, x=viz["x"], y=viz["y"], title=viz["title"])
                    fig.update_layout(
                        xaxis_title=viz["x"].capitalize(),
                        yaxis_title="Cost ($)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif viz["type"] == "line":
                    df = pd.DataFrame(viz["data"])
                    fig = px.line(df, x=viz["x"], y=viz["y"], title=viz["title"])
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Cost ($)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Display recommendations if available
        if "recommendations" in message:
            st.subheader("Recommendations")
            for i, rec in enumerate(message["recommendations"]):
                with st.expander(f"{i+1}. {rec['title']}"):
                    st.markdown(rec["description"])
                    st.markdown(f"**Potential Savings**: ${rec['savings']:,.2f}")
                    st.markdown(f"**Implementation Difficulty**: {rec['difficulty']}")
                    st.markdown(f"**Implementation Steps**:")
                    for step in rec["steps"]:
                        st.markdown(f"- {step}")

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
            
            # Add visualizations to response if available
            if "visualizations" in response:
                for viz in response["visualizations"]:
                    if viz["type"] == "bar":
                        df = pd.DataFrame(viz["data"])
                        fig = px.bar(df, x=viz["x"], y=viz["y"], title=viz["title"])
                        fig.update_layout(
                            xaxis_title=viz["x"].capitalize(),
                            yaxis_title="Cost ($)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif viz["type"] == "line":
                        df = pd.DataFrame(viz["data"])
                        fig = px.line(df, x=viz["x"], y=viz["y"], title=viz["title"])
                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Cost ($)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Add recommendations to response if available
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
    assistant_message = {"role": "assistant", "content": response["text"]}
    if "visualizations" in response:
        assistant_message["visualizations"] = response["visualizations"]
    if "recommendations" in response:
        assistant_message["recommendations"] = response["recommendations"]
    
    st.session_state.messages.append(assistant_message)

# Display welcome message if no messages yet
if not st.session_state.messages:
    st.info("""
    👋 Welcome to AWS FinOps Copilot!
    
    I'm your AI-powered assistant for AWS cost optimization. Here are some questions you can ask me:
    
    - What's my AWS cost breakdown for the last month?
    - How can I optimize my EC2 costs?
    - Do I have any idle resources that I can remove?
    - What Savings Plans would you recommend for my usage?
    - How has my S3 cost trend changed over the past 3 months?
    
    Feel free to ask any questions about your AWS costs and resource usage!
    """)

if __name__ == "__main__":
    # This is included for running the script directly
    pass
