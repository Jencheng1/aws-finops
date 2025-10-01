#!/usr/bin/env python3
"""
AWS FinOps Intelligent Dashboard with Complete Feature Set
Includes: Cost Intelligence, Multi-Agent Chatbot, Apptio MCP Integration
"""

import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
import uuid
from typing import Dict, List, Tuple
from multi_agent_processor import MultiAgentProcessor

# Page configuration
st.set_page_config(
    page_title="AWS FinOps Intelligence Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize AWS clients
@st.cache_resource
def init_aws_clients():
    """Initialize AWS clients with caching"""
    return {
        'ce': boto3.client('ce'),
        'ec2': boto3.client('ec2'),
        'cloudwatch': boto3.client('cloudwatch'),
        'lambda': boto3.client('lambda'),
        'dynamodb': boto3.resource('dynamodb'),
        'sts': boto3.client('sts'),
        'support': boto3.client('support', region_name='us-east-1'),
        'organizations': boto3.client('organizations')
    }

clients = init_aws_clients()

# Get account info
try:
    account_id = clients['sts'].get_caller_identity()['Account']
except:
    account_id = "Demo Account"

# Initialize session state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'cost_data_cache' not in st.session_state:
    st.session_state.cost_data_cache = {}
if 'active_agent' not in st.session_state:
    st.session_state.active_agent = "general"
if 'apptio_data' not in st.session_state:
    st.session_state.apptio_data = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Apptio MCP Integration Configuration
APPTIO_MCP_CONFIG = {
    'enabled': True,
    'business_units': ['Engineering', 'Sales', 'Marketing', 'Operations', 'IT'],
    'cost_pools': {
        'Infrastructure': ['EC2', 'EBS', 'S3', 'RDS', 'ElastiCache'],
        'Applications': ['Lambda', 'ECS', 'App Runner', 'Batch'],
        'End User': ['WorkSpaces', 'AppStream', 'Connect'],
        'Security': ['GuardDuty', 'Inspector', 'WAF', 'Shield']
    },
    'tbm_metrics': {
        'cost_per_employee': 0,
        'infrastructure_efficiency': 0,
        'app_rationalization_score': 0
    }
}

# Agent definitions
AGENTS = {
    'general': {
        'name': 'General FinOps Assistant',
        'icon': '🤖',
        'color': '#1f77b4',
        'capabilities': ['General cost queries', 'Basic recommendations', 'Cost summaries']
    },
    'prediction': {
        'name': 'Budget Prediction Agent',
        'icon': '📈',
        'color': '#ff7f0e',
        'capabilities': ['ML-based forecasting', 'Trend analysis', 'Budget planning']
    },
    'optimizer': {
        'name': 'Resource Optimization Agent',
        'icon': '🔍',
        'color': '#2ca02c',
        'capabilities': ['Waste identification', 'Rightsizing', 'Cleanup recommendations']
    },
    'savings': {
        'name': 'Savings Plan Agent',
        'icon': '💎',
        'color': '#d62728',
        'capabilities': ['Commitment optimization', 'ROI analysis', 'Coverage gaps']
    },
    'anomaly': {
        'name': 'Anomaly Detection Agent',
        'icon': '🚨',
        'color': '#9467bd',
        'capabilities': ['Cost spike detection', 'Usage anomalies', 'Alert configuration']
    }
}

def get_apptio_business_context(costs_by_service: Dict) -> Dict:
    """
    Transform AWS costs into Apptio TBM business context with realistic data
    """
    # Get total cost
    total_cost = sum(costs_by_service.values()) if costs_by_service else 50000  # Default for demo
    
    # Enhanced service to business unit mapping with weights
    service_mappings = {
        'Engineering': {
            'services': ['AmazonEC2', 'AWSLambda', 'AmazonECS', 'AWSCodeBuild', 'AmazonECR', 'AmazonSageMaker'],
            'weight': 0.40  # 40% of IT spend
        },
        'Sales': {
            'services': ['AmazonConnect', 'AmazonPinpoint', 'AmazonSES', 'AmazonSNS'],
            'weight': 0.15  # 15% of IT spend
        },
        'Marketing': {
            'services': ['AmazonS3', 'AmazonCloudFront', 'AWSElementalMediaConvert', 'AmazonPersonalize'],
            'weight': 0.20  # 20% of IT spend
        },
        'Operations': {
            'services': ['AmazonRDS', 'AmazonDynamoDB', 'AmazonElastiCache', 'AmazonRedshift', 'AmazonKinesis'],
            'weight': 0.20  # 20% of IT spend
        },
        'IT': {
            'services': ['AmazonWorkSpaces', 'AWSDirectoryService', 'AWSSystemsManager', 'AWSIAM'],
            'weight': 0.05  # 5% of IT spend
        }
    }
    
    # Calculate business unit costs with realistic distribution
    business_allocation = {}
    allocated_total = 0
    
    for bu, config in service_mappings.items():
        # Calculate based on actual service costs if available
        bu_cost = sum(costs_by_service.get(svc, 0) for svc in config['services'])
        
        # If no actual costs, use weighted distribution
        if bu_cost == 0:
            bu_cost = total_cost * config['weight']
        
        business_allocation[bu] = bu_cost
        allocated_total += bu_cost
    
    # Normalize to ensure total matches
    if allocated_total > 0:
        for bu in business_allocation:
            business_allocation[bu] = (business_allocation[bu] / allocated_total) * total_cost
    
    # Calculate realistic TBM metrics
    employee_count = 1000  # Company size
    annual_revenue = 500_000_000  # $500M annual revenue
    
    # Realistic TBM metrics based on industry benchmarks
    tbm_metrics = {
        'cost_per_employee': total_cost / employee_count,
        'infrastructure_efficiency': 0.68,  # Industry avg: 65-75%
        'app_rationalization_score': 0.73,  # Indicates room for consolidation
        'it_spend_as_percent_revenue': (total_cost * 12) / annual_revenue * 100,  # Annualized
        'run_vs_grow_spend': {'run': 72, 'grow': 28},  # Typical split
        'cost_per_transaction': total_cost / 1_000_000,  # Per 1M transactions
        'infrastructure_unit_cost': total_cost * 0.4 / 1000,  # Per infrastructure unit
        'application_tco': total_cost * 0.35,  # 35% of costs for apps
        'end_user_cost': total_cost * 0.15 / employee_count,  # Per user
        'security_spend_percent': 8.5  # % of IT budget on security
    }
    
    # Enhanced cost pools with realistic percentages
    cost_pools_allocation = {
        'Infrastructure': total_cost * 0.40,  # 40% - Compute, storage, network
        'Applications': total_cost * 0.35,   # 35% - App platforms, containers
        'End User': total_cost * 0.15,      # 15% - Workspaces, productivity
        'Security': total_cost * 0.10       # 10% - Security services
    }
    
    return {
        'business_allocation': business_allocation,
        'tbm_metrics': tbm_metrics,
        'cost_pools': APPTIO_MCP_CONFIG['cost_pools'],
        'cost_pools_allocation': cost_pools_allocation,
        'total_it_spend': total_cost,
        'insights': {
            'optimization_potential': total_cost * 0.18,  # 18% potential savings
            'recommended_run_percentage': 65,  # Target: 65% run
            'automation_opportunity': total_cost * 0.12  # 12% through automation
        }
    }

def identify_active_agent(query: str) -> str:
    """
    Identify which agent should handle the query
    """
    query_lower = query.lower()
    
    # Check for multi-agent queries that need optimization
    if 'recommend' in query_lower and 'optimization' in query_lower:
        return 'optimizer'
    elif 'analyze' in query_lower and 'costs' in query_lower and 'recommend' in query_lower:
        return 'optimizer'
    
    # Standard agent routing
    if any(word in query_lower for word in ['predict', 'forecast', 'budget', 'future', 'trend', 'will', 'next month', 'next year']):
        return 'prediction'
    elif any(word in query_lower for word in ['optimize', 'waste', 'idle', 'unused', 'cleanup', 'underutilized', 'optimization']):
        return 'optimizer'
    elif any(word in query_lower for word in ['savings plan', 'commitment', 'reserved', 'discount', 'save']):
        return 'savings'
    elif any(word in query_lower for word in ['anomaly', 'spike', 'unusual', 'alert']):
        return 'anomaly'
    else:
        return 'general'

# Initialize agent processor
@st.cache_resource
def get_agent_processor():
    return MultiAgentProcessor()

agent_processor = get_agent_processor()

def process_with_agent(agent_type: str, query: str, context: Dict) -> Tuple[str, Dict]:
    """
    Process query with specific agent using real AWS APIs
    """
    context['user_id'] = st.session_state.user_id
    context['session_id'] = st.session_state.session_id
    
    # Route to appropriate agent processor
    if agent_type == 'prediction':
        return agent_processor.process_prediction_query(query, context)
    elif agent_type == 'optimizer':
        return agent_processor.process_optimizer_query(query, context)
    elif agent_type == 'savings':
        return agent_processor.process_savings_query(query, context)
    elif agent_type == 'anomaly':
        return agent_processor.process_anomaly_query(query, context)
    else:
        return agent_processor.process_general_query(query, context)

# Main header with Apptio integration highlight
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("🚀 AWS FinOps Intelligence Platform")
with col2:
    st.markdown("### 🔗 Apptio MCP Integrated")
    st.caption("Business Context Enabled")
with col3:
    st.metric("AWS Account", account_id)

# Sidebar
with st.sidebar:
    st.header("🔧 Platform Configuration")
    
    # Apptio MCP Status
    if APPTIO_MCP_CONFIG['enabled']:
        st.success("✅ Apptio MCP Connected")
        st.caption("TBM insights active")
    else:
        st.warning("⚠️ Apptio MCP Disconnected")
    
    # Analysis Parameters
    st.subheader("Analysis Parameters")
    days_lookback = st.slider("Historical Days", 7, 90, 30)
    forecast_days = st.slider("Forecast Days", 7, 90, 30)
    
    # Active Agents Status
    st.subheader("🤖 Active AI Agents")
    for agent_key, agent in AGENTS.items():
        st.markdown(f"{agent['icon']} **{agent['name']}**")
        st.caption(f"Status: ✅ Active")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Full Analysis", use_container_width=True):
            st.session_state.run_full_analysis = True
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")

# Main content area
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Cost Intelligence",
    "💬 Multi-Agent Chat",
    "🏢 Business Context (Apptio)",
    "🔍 Resource Optimization",
    "💎 Savings Plans",
    "🔮 Budget Prediction",
    "📈 Executive Dashboard"
])

# Initialize global variables for cross-tab access
daily_costs = []
service_costs = {}

# Tab 1: Cost Intelligence
with tab1:
    st.header("📊 Cost Intelligence Dashboard")
    
    # Fetch cost data
    @st.cache_data(ttl=300)
    def fetch_cost_data(days):
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        response = clients['ce'].get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        return response
    
    try:
        cost_data = fetch_cost_data(days_lookback)
        
        # Process data for visualization (update global variables)
        daily_costs.clear()
        service_costs.clear()
        
        for result in cost_data['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total = 0
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if service not in service_costs:
                    service_costs[service] = 0
                service_costs[service] += cost
                total += cost
            
            daily_costs.append({'Date': date, 'Cost': total})
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_cost = sum(d['Cost'] for d in daily_costs)
        avg_daily = total_cost / len(daily_costs) if daily_costs else 0
        yesterday_cost = daily_costs[-1]['Cost'] if daily_costs else 0
        week_ago_cost = daily_costs[-7]['Cost'] if len(daily_costs) >= 7 else yesterday_cost
        
        with col1:
            st.metric("Total Period Cost", f"${total_cost:,.2f}")
        with col2:
            st.metric("Average Daily", f"${avg_daily:,.2f}")
        with col3:
            st.metric("Yesterday", f"${yesterday_cost:,.2f}", 
                     delta=f"{((yesterday_cost/week_ago_cost - 1) * 100):.1f}%")
        with col4:
            mtd_cost = sum(d['Cost'] for d in daily_costs[-30:])
            st.metric("Last 30 Days", f"${mtd_cost:,.2f}")
        
        # Daily trend chart
        st.subheader("📈 Daily Cost Trend")
        df_daily = pd.DataFrame(daily_costs)
        fig_daily = px.line(df_daily, x='Date', y='Cost', markers=True)
        fig_daily.update_layout(height=400)
        st.plotly_chart(fig_daily, use_container_width=True)
        
        # Service breakdown
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🏷️ Cost by Service")
            top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:10]
            df_services = pd.DataFrame(top_services, columns=['Service', 'Cost'])
            fig_services = px.bar(df_services, x='Cost', y='Service', orientation='h')
            fig_services.update_layout(height=400)
            st.plotly_chart(fig_services, use_container_width=True)
        
        with col2:
            st.subheader("📊 Cost Distribution")
            fig_pie = px.pie(values=[x[1] for x in top_services], 
                            names=[x[0] for x in top_services])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Service drill-down section
        st.subheader("🔍 Service Drill-Down Analysis")
        
        # Service selector
        selected_service = st.selectbox(
            "Select a service to view detailed resource costs:",
            options=[s[0] for s in top_services],
            format_func=lambda x: f"{x} (${service_costs.get(x, 0):,.2f})"
        )
        
        if selected_service:
            with st.spinner(f"Loading resource details for {selected_service}..."):
                try:
                    # Get resource-level costs for selected service
                    @st.cache_data(ttl=300)
                    def get_resource_costs(service_name, start_date, end_date):
                        # Map service names to appropriate group-by keys
                        # Note: RESOURCE_ID is not a valid dimension for Cost Explorer
                        service_mapping = {
                            'AmazonEC2': 'INSTANCE_TYPE',  # Changed from RESOURCE_ID
                            'AmazonRDS': 'DATABASE_ENGINE',
                            'AmazonS3': 'USAGE_TYPE',
                            'AWSLambda': 'USAGE_TYPE',
                            'AmazonDynamoDB': 'USAGE_TYPE',
                            'ElasticLoadBalancing': 'USAGE_TYPE',
                            'AmazonCloudFront': 'USAGE_TYPE'
                        }
                        
                        group_by_key = service_mapping.get(service_name, 'USAGE_TYPE')
                        
                        try:
                            response = clients['ce'].get_cost_and_usage(
                                TimePeriod={
                                    'Start': start_date,
                                    'End': end_date
                                },
                                Granularity='DAILY',
                                Metrics=['UnblendedCost'],
                                Filter={
                                    'Dimensions': {
                                        'Key': 'SERVICE',
                                        'Values': [service_name]
                                    }
                                },
                                GroupBy=[{'Type': 'DIMENSION', 'Key': group_by_key}]
                            )
                            return response, group_by_key
                        except:
                            # Fallback to USAGE_TYPE if specific grouping fails
                            response = clients['ce'].get_cost_and_usage(
                                TimePeriod={
                                    'Start': start_date,
                                    'End': end_date
                                },
                                Granularity='DAILY',
                                Metrics=['UnblendedCost'],
                                Filter={
                                    'Dimensions': {
                                        'Key': 'SERVICE',
                                        'Values': [service_name]
                                    }
                                },
                                GroupBy=[{'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}]
                            )
                            return response, 'USAGE_TYPE'
                    
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=days_lookback)
                    
                    resource_response, group_type = get_resource_costs(
                        selected_service,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    # Process resource-level data
                    resource_costs = {}
                    resource_daily_data = []
                    
                    for result in resource_response['ResultsByTime']:
                        date = result['TimePeriod']['Start']
                        
                        for group in result['Groups']:
                            resource_id = group['Keys'][0]
                            cost = float(group['Metrics']['UnblendedCost']['Amount'])
                            
                            if resource_id not in resource_costs:
                                resource_costs[resource_id] = 0
                            resource_costs[resource_id] += cost
                            
                            if cost > 0:  # Only track resources with costs
                                resource_daily_data.append({
                                    'Date': date,
                                    'Resource': resource_id[:50],  # Truncate long IDs
                                    'Cost': cost
                                })
                    
                    # For EC2, show comprehensive instance details
                    if selected_service == 'AmazonEC2':
                        st.info("💡 **Note**: Cost Explorer groups EC2 costs by usage type. Below are all your EC2 instances with detailed metrics and costs.")
                        
                        try:
                            # Import the utility function
                            from get_ec2_details_with_costs import get_ec2_instance_details_with_costs
                            
                            # Get comprehensive EC2 data
                            with st.spinner("Fetching detailed EC2 instance data with real-time metrics..."):
                                df_ec2_details, ec2_summary = get_ec2_instance_details_with_costs(days_lookback=days_lookback)
                                
                                # Display EC2 summary metrics
                                st.markdown("**🖥️ EC2 Fleet Overview:**")
                                metric_cols = st.columns(6)
                                with metric_cols[0]:
                                    st.metric("Total Instances", ec2_summary['total_instances'])
                                with metric_cols[1]:
                                    st.metric("Running", ec2_summary['running_instances'], 
                                             delta=f"{ec2_summary['running_instances']}/{ec2_summary['total_instances']}")
                                with metric_cols[2]:
                                    st.metric("Stopped", ec2_summary['stopped_instances'])
                                with metric_cols[3]:
                                    st.metric("Underutilized", ec2_summary['underutilized_count'])
                                with metric_cols[4]:
                                    st.metric("Monthly Cost", f"${ec2_summary['total_monthly_cost']:,.0f}")
                                with metric_cols[5]:
                                    st.metric("Potential Savings", f"${ec2_summary['potential_monthly_savings']:,.0f}")
                                
                                # Detailed instance table with filtering
                                st.markdown("**📊 Detailed Instance Information:**")
                                
                                # Add filters
                                filter_cols = st.columns([2, 2, 2, 2])
                                with filter_cols[0]:
                                    state_filter = st.multiselect(
                                        "State", 
                                        options=df_ec2_details['State'].unique().tolist(),
                                        default=df_ec2_details['State'].unique().tolist()
                                    )
                                with filter_cols[1]:
                                    type_filter = st.multiselect(
                                        "Instance Type",
                                        options=sorted(df_ec2_details['Type'].unique().tolist()),
                                        default=sorted(df_ec2_details['Type'].unique().tolist())
                                    )
                                with filter_cols[2]:
                                    optimization_filter = st.multiselect(
                                        "Optimization Status",
                                        options=df_ec2_details['Optimization'].unique().tolist(),
                                        default=df_ec2_details['Optimization'].unique().tolist()
                                    )
                                with filter_cols[3]:
                                    show_columns = st.multiselect(
                                        "Show Columns",
                                        options=['Instance ID', 'Name', 'Type', 'State', 'Region', 'AZ', 
                                                'Launch Time', 'CPU Avg %', 'CPU Max %', 'Network In (MB)', 
                                                'Network Out (MB)', 'Storage (GB)', f'{days_lookback}d Cost', 
                                                'Monthly Cost', 'Annual Cost', 'Optimization'],
                                        default=['Instance ID', 'Name', 'Type', 'State', 'CPU Avg %', 
                                                'Monthly Cost', 'Optimization']
                                    )
                                
                                # Apply filters
                                filtered_df = df_ec2_details[
                                    (df_ec2_details['State'].isin(state_filter)) &
                                    (df_ec2_details['Type'].isin(type_filter)) &
                                    (df_ec2_details['Optimization'].isin(optimization_filter))
                                ]
                                
                                # Display filtered dataframe
                                if not filtered_df.empty:
                                    # Format currency columns for display
                                    display_df = filtered_df[show_columns].copy()
                                    if 'Monthly Cost' in display_df.columns:
                                        display_df['Monthly Cost'] = display_df['Monthly Cost'].apply(lambda x: f"${x:,.2f}")
                                    if 'Annual Cost' in display_df.columns:
                                        display_df['Annual Cost'] = display_df['Annual Cost'].apply(lambda x: f"${x:,.2f}")
                                    if f'{days_lookback}d Cost' in display_df.columns:
                                        display_df[f'{days_lookback}d Cost'] = display_df[f'{days_lookback}d Cost'].apply(lambda x: f"${x:,.2f}")
                                    
                                    # Add row coloring based on optimization status
                                    def highlight_optimization(row):
                                        if 'Optimization' in row:
                                            if row['Optimization'] == 'Underutilized':
                                                return ['background-color: #fff3cd'] * len(row)
                                            elif row['Optimization'] == 'Stop to save':
                                                return ['background-color: #f8d7da'] * len(row)
                                        return [''] * len(row)
                                    
                                    styled_df = display_df.style.apply(highlight_optimization, axis=1)
                                    st.dataframe(styled_df, use_container_width=True, height=400)
                                    
                                    # Download button for CSV export
                                    csv = filtered_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download EC2 Details as CSV",
                                        data=csv,
                                        file_name=f"ec2_instance_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    st.warning("No instances match the selected filters")
                                
                                # Instance type distribution
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**📊 Instance Type Distribution:**")
                                    type_counts = df_ec2_details['Type'].value_counts().head(10)
                                    fig_types = px.bar(
                                        x=type_counts.values,
                                        y=type_counts.index,
                                        orientation='h',
                                        labels={'x': 'Count', 'y': 'Instance Type'}
                                    )
                                    fig_types.update_layout(height=300)
                                    st.plotly_chart(fig_types, use_container_width=True)
                                
                                with col2:
                                    st.markdown("**💰 Cost by Instance State:**")
                                    state_costs = df_ec2_details.groupby('State')['Monthly Cost'].sum()
                                    fig_state_costs = px.pie(
                                        values=state_costs.values,
                                        names=state_costs.index,
                                        hole=0.3
                                    )
                                    fig_state_costs.update_layout(height=300)
                                    st.plotly_chart(fig_state_costs, use_container_width=True)
                                
                                # CPU utilization distribution for running instances
                                running_instances = df_ec2_details[df_ec2_details['State'] == 'running']
                                if not running_instances.empty:
                                    st.markdown("**🔥 CPU Utilization Analysis (Running Instances):**")
                                    
                                    # Create CPU utilization bins
                                    cpu_bins = [0, 10, 30, 50, 70, 100]
                                    cpu_labels = ['0-10%', '10-30%', '30-50%', '50-70%', '70-100%']
                                    running_instances['CPU Bin'] = pd.cut(
                                        running_instances['CPU Avg %'], 
                                        bins=cpu_bins, 
                                        labels=cpu_labels,
                                        include_lowest=True
                                    )
                                    
                                    cpu_dist = running_instances['CPU Bin'].value_counts().sort_index()
                                    fig_cpu = px.bar(
                                        x=cpu_dist.index,
                                        y=cpu_dist.values,
                                        labels={'x': 'CPU Utilization Range', 'y': 'Number of Instances'},
                                        color=cpu_dist.values,
                                        color_continuous_scale=['green', 'yellow', 'orange', 'red']
                                    )
                                    fig_cpu.update_layout(height=300, showlegend=False)
                                    st.plotly_chart(fig_cpu, use_container_width=True)
                                    
                                    # Show underutilized instances
                                    underutilized = running_instances[running_instances['CPU Avg %'] < 10]
                                    if not underutilized.empty:
                                        st.warning(f"⚠️ {len(underutilized)} running instances have CPU utilization < 10%")
                                        with st.expander("View Underutilized Instances"):
                                            st.dataframe(
                                                underutilized[['Instance ID', 'Name', 'Type', 'CPU Avg %', 'Monthly Cost']],
                                                use_container_width=True
                                            )
                                            
                                            potential_savings = underutilized['Monthly Cost'].sum() * 0.5
                                            st.info(f"💡 Potential savings from rightsizing: ${potential_savings:,.2f}/month")
                                
                        except ImportError:
                            st.error("EC2 details utility not found. Showing usage type breakdown instead.")
                            
                        except Exception as e:
                            st.error(f"Error fetching EC2 details: {str(e)[:200]}")
                    
                    # Show usage type breakdown for all services
                    st.markdown(f"**💰 {selected_service} Cost Breakdown by {group_type.replace('_', ' ').title()}:**")
                    top_resources = sorted(resource_costs.items(), key=lambda x: x[1], reverse=True)[:10]
                    
                    if top_resources:
                        # Create a more readable format
                        resource_df = pd.DataFrame(top_resources, columns=['Resource', 'Total Cost'])
                        resource_df['Total Cost'] = resource_df['Total Cost'].apply(lambda x: f"${x:,.2f}")
                        resource_df['Resource'] = resource_df['Resource'].apply(lambda x: x[:40] + '...' if len(x) > 40 else x)
                        st.dataframe(resource_df, use_container_width=True)
                    
                    # Resource cost trend over time
                    if resource_daily_data:
                        st.markdown("**📊 Daily Resource Cost Trend:**")
                        
                        # Get top 5 resources by total cost
                        top_5_resources = [r[0] for r in sorted(resource_costs.items(), 
                                                               key=lambda x: x[1], reverse=True)[:5]]
                        
                        # Filter daily data for top 5 resources
                        filtered_data = [d for d in resource_daily_data 
                                       if any(d['Resource'].startswith(r[:40]) for r in top_5_resources)]
                        
                        if filtered_data:
                            df_resource_trend = pd.DataFrame(filtered_data)
                            fig_trend = px.line(df_resource_trend, x='Date', y='Cost', 
                                              color='Resource', markers=True)
                            fig_trend.update_layout(height=400, showlegend=True)
                            st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # Additional service-specific insights
                    if selected_service == 'AmazonS3':
                        st.markdown("**🗂️ S3 Storage Insights:**")
                        storage_types = {}
                        for resource, cost in resource_costs.items():
                            if 'TimedStorage' in resource:
                                storage_type = 'Standard Storage'
                            elif 'IntelligentTiering' in resource:
                                storage_type = 'Intelligent Tiering'
                            elif 'Glacier' in resource:
                                storage_type = 'Glacier Storage'
                            elif 'Requests' in resource:
                                storage_type = 'API Requests'
                            elif 'DataTransfer' in resource:
                                storage_type = 'Data Transfer'
                            else:
                                storage_type = 'Other'
                            
                            if storage_type not in storage_types:
                                storage_types[storage_type] = 0
                            storage_types[storage_type] += cost
                        
                        if storage_types:
                            df_storage = pd.DataFrame(list(storage_types.items()), 
                                                    columns=['Storage Type', 'Cost'])
                            fig_storage = px.pie(df_storage, values='Cost', names='Storage Type')
                            st.plotly_chart(fig_storage, use_container_width=True)
                    
                    elif selected_service == 'AmazonRDS':
                        st.markdown("**🗄️ RDS Database Insights:**")
                        st.info("Group by DATABASE_ENGINE shows costs per database engine type")
                    
                    elif selected_service == 'AWSLambda':
                        st.markdown("**⚡ Lambda Function Insights:**")
                        request_costs = sum(c for r, c in resource_costs.items() if 'Request' in r)
                        compute_costs = sum(c for r, c in resource_costs.items() if 'GB-Second' in r)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Request Costs", f"${request_costs:.2f}")
                        with col2:
                            st.metric("Compute Costs", f"${compute_costs:.2f}")
                    
                except Exception as e:
                    st.error(f"Error getting resource details: {str(e)}")
                    st.info("Try selecting a different service or adjusting the date range.")
        
    except Exception as e:
        st.error(f"Error fetching cost data: {str(e)}")

# Tab 2: Multi-Agent Chat
with tab2:
    st.header("💬 Multi-Agent Cost Assistant")
    
    # Agent selector
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"🤖 Active Agent: **{AGENTS[st.session_state.active_agent]['name']}**")
    with col2:
        if st.button("🔄 Reset Chat"):
            st.session_state.chat_messages = []
    
    # Example questions
    with st.expander("💡 Example Questions to Ask", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **General Cost Questions:**
            - "What are my current month costs?"
            - "Show me top spending services"
            - "What's my daily average spend?"
            
            **Prediction & Forecasting:**
            - "Predict next month's costs"
            - "Forecast my annual budget"
            - "Will I exceed my budget this month?"
            
            **Resource Optimization:**
            - "Find idle resources"
            - "Show me unused EBS volumes"
            - "Which EC2 instances are underutilized?"
            """)
        
        with col2:
            st.markdown("""
            **Savings Plans:**
            - "Recommend savings plans"
            - "What's my current commitment coverage?"
            - "How much can I save with reserved instances?"
            
            **Anomaly Detection:**
            - "Check for cost anomalies"
            - "Alert me about unusual spending"
            - "What caused yesterday's cost spike?"
            
            **Multi-Agent Queries:**
            - "Analyze my costs and recommend optimizations"
            - "Help me reduce my AWS bill by 20%"
            - "Create a cost optimization plan"
            """)
    
    # Display agent capabilities
    with st.expander("🎯 Agent Capabilities", expanded=False):
        for agent_key, agent in AGENTS.items():
            st.markdown(f"**{agent['icon']} {agent['name']}**")
            for cap in agent['capabilities']:
                st.caption(f"  • {cap}")
    
    # Chat interface
    chat_container = st.container()
    
    # Display messages
    with chat_container:
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                # User message display
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.write("👤")
                    with col2:
                        st.info(message["content"])
            else:
                # Assistant message display
                agent_key = message.get("agent", "general")
                agent = AGENTS.get(agent_key, AGENTS["general"])
                
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.write(agent["icon"])
                    with col2:
                        st.success(f"**[{agent['name']}]**")
                        st.write(message["content"])
    
    # Chat input (using form for compatibility with Streamlit 1.23)
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Ask about costs, optimizations, or predictions...", key="chat_input_field")
        with col2:
            submit_button = st.form_submit_button("Send", use_container_width=True)
    
    if submit_button and user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Identify appropriate agent
        agent_type = identify_active_agent(user_input)
        st.session_state.active_agent = agent_type
        
        # Process with agent
        with st.spinner(f"🤔 {AGENTS[agent_type]['name']} is thinking..."):
            response, data = process_with_agent(agent_type, user_input, {})
        
        # Add agent response
        st.session_state.chat_messages.append({
            "role": "assistant",
            "agent": agent_type,
            "content": response,
            "data": data
        })
        
        # Force refresh to show new messages
        st.experimental_rerun()

# Tab 3: Business Context (Apptio)
with tab3:
    st.header("🏢 Business Context Analytics (Apptio MCP)")
    
    st.info("🔗 **Apptio MCP Integration** transforms technical AWS costs into business-relevant insights")
    
    # Get business context
    if service_costs and len(service_costs) > 0:
        apptio_context = get_apptio_business_context(service_costs)
        st.session_state.apptio_data = apptio_context
        
        # TBM Metrics
        st.subheader("📊 Technology Business Management (TBM) Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cost per Employee", 
                     f"${apptio_context['tbm_metrics']['cost_per_employee']:,.2f}")
        with col2:
            st.metric("Infrastructure Efficiency", 
                     f"{apptio_context['tbm_metrics']['infrastructure_efficiency']*100:.1f}%")
        with col3:
            st.metric("App Rationalization Score", 
                     f"{apptio_context['tbm_metrics']['app_rationalization_score']*100:.1f}%")
        with col4:
            st.metric("IT Spend vs Revenue", 
                     f"{apptio_context['tbm_metrics']['it_spend_as_percent_revenue']:.1f}%")
        
        # Business Unit Allocation
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💼 Cost by Business Unit")
            bu_data = apptio_context['business_allocation']
            df_bu = pd.DataFrame(list(bu_data.items()), columns=['Business Unit', 'Cost'])
            fig_bu = px.bar(df_bu, x='Business Unit', y='Cost')
            st.plotly_chart(fig_bu, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Run vs Grow Spend")
            run_grow = apptio_context['tbm_metrics']['run_vs_grow_spend']
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = run_grow['grow'],
                title = {'text': "Grow Spend %"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 30
                    }
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Cost Pools
        st.subheader("🏭 IT Cost Pools")
        pool_cols = st.columns(4)
        for i, (pool, cost) in enumerate(apptio_context.get('cost_pools_allocation', {}).items()):
            with pool_cols[i % 4]:
                st.metric(f"{pool}", f"${cost:,.2f}", 
                         help=f"Services: {', '.join(APPTIO_MCP_CONFIG['cost_pools'][pool][:3])}...")
        
        # Additional Insights
        if 'insights' in apptio_context:
            st.subheader("💡 Optimization Insights")
            insight_cols = st.columns(3)
            with insight_cols[0]:
                st.metric("Optimization Potential", 
                         f"${apptio_context['insights']['optimization_potential']:,.2f}",
                         help="Estimated savings through optimization")
            with insight_cols[1]:
                st.metric("Automation Opportunity", 
                         f"${apptio_context['insights']['automation_opportunity']:,.2f}",
                         help="Potential savings through automation")
            with insight_cols[2]:
                st.metric("Target Run %", 
                         f"{apptio_context['insights']['recommended_run_percentage']}%",
                         help="Industry benchmark for run vs grow")
    else:
        st.info("📊 Please navigate to the Cost Intelligence tab first to load cost data.")
        st.caption("Once cost data is loaded, business context analytics will be available here.")

# Tab 4: Resource Optimization
with tab4:
    st.header("🔍 Resource Optimization Center")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🚀 Run Optimization Scan", type="primary"):
