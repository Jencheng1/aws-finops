#!/usr/bin/env python3
"""
AWS FinOps Intelligent Dashboard with Fixed Tab Display
Alternative approach using sidebar navigation for better visibility
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
from finops_report_generator import FinOpsReportGenerator
from tag_compliance_agent import TagComplianceAgent
import base64
import io

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
    account_id = 'Unknown'

# Header
st.title("💰 AWS FinOps Intelligence Platform")
st.markdown(f"**Account:** {account_id} | **Region:** {boto3.Session().region_name or 'us-east-1'}")

# Sidebar navigation
st.sidebar.title("🧭 Navigation")
st.sidebar.markdown("### 📊 Main Features")

# Define tabs
tabs = {
    "📊 Cost Intelligence": "tab1",
    "💬 Multi-Agent Chat": "tab2",
    "🏢 Business Context (Apptio)": "tab3",
    "🔍 Resource Optimization": "tab4",
    "💎 Savings Plans": "tab5",
    "🔮 Budget Prediction": "tab6",
    "📈 Executive Dashboard": "tab7"
}

# Add separator for new features
st.sidebar.markdown("---")
st.sidebar.markdown("### 🆕 New Features")

new_tabs = {
    "📋 Report Generator": "tab8",
    "🏷️ Tag Compliance": "tab9"
}

# Combine all tabs
all_tabs = {**tabs, **new_tabs}

# Create radio button for navigation
selected_tab_name = st.sidebar.radio(
    "Select a feature:",
    list(all_tabs.keys()),
    index=0
)

selected_tab = all_tabs[selected_tab_name]

# Display content based on selection
st.markdown(f"## {selected_tab_name}")

if selected_tab == "tab8":
    # Report Generator Tab
    st.header("📋 FinOps Report Generator")
    
    # Initialize report generator
    @st.cache_resource
    def get_report_generator():
        return FinOpsReportGenerator(clients)
    
    report_generator = get_report_generator()
    
    # Report configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["full", "executive", "technical", "cost-only", "compliance-only"],
            help="Select the type of report to generate"
        )
    
    with col2:
        report_format = st.selectbox(
            "Report Format",
            ["pdf", "excel", "json"],
            help="Select the output format"
        )
    
    with col3:
        days_back = st.slider(
            "Days of Data",
            min_value=7,
            max_value=90,
            value=30,
            help="Number of days to include in the report"
        )
    
    # Date selection
    col1, col2 = st.columns(2)
    with col1:
        end_date = st.date_input("End Date", value=datetime.now().date())
    with col2:
        start_date = st.date_input("Start Date", value=end_date - timedelta(days=days_back))
    
    # Additional options
    col1, col2 = st.columns(2)
    with col1:
        include_recommendations = st.checkbox("Include Optimization Recommendations", value=True)
        include_trends = st.checkbox("Include Trend Analysis", value=True)
    
    with col2:
        include_tag_compliance = st.checkbox("Include Tag Compliance Analysis", value=True)
        include_savings_plans = st.checkbox("Include Savings Plan Recommendations", value=True)
    
    # Generate report button
    if st.button("🚀 Generate Report", type="primary"):
        with st.spinner(f"Generating {report_format.upper()} report..."):
            try:
                # Generate the report
                report_content = report_generator.generate_comprehensive_report(
                    report_type=report_type,
                    start_date=start_date,
                    end_date=end_date,
                    format=report_format,
                    include_recommendations=include_recommendations,
                    include_trends=include_trends
                )
                
                # Display success message
                st.success(f"✅ Report generated successfully!")
                
                # Show report preview for JSON
                if report_format == 'json':
                    report_data = json.loads(report_content)
                    
                    # Display key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Cost", f"${report_data['cost_analysis']['total_cost']:,.2f}")
                    with col2:
                        st.metric("Daily Average", f"${report_data['cost_analysis']['average_daily_cost']:,.2f}")
                    with col3:
                        st.metric("Services", len(report_data['cost_analysis']['service_costs']))
                    with col4:
                        if 'resource_tagging' in report_data:
                            st.metric("Tag Compliance", f"{report_data['resource_tagging']['compliance_rate']:.1f}%")
                
                # Download button
                if report_format == 'pdf':
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=report_content,
                        file_name=f"finops_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                elif report_format == 'excel':
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=report_content,
                        file_name=f"finops_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:  # json
                    st.download_button(
                        label="📥 Download JSON Report",
                        data=report_content,
                        file_name=f"finops_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    
                    # Show JSON preview
                    with st.expander("📄 Report Preview", expanded=True):
                        st.json(report_data)
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    # Report Templates
    st.subheader("📚 Report Templates")
    
    template_col1, template_col2 = st.columns(2)
    
    with template_col1:
        if st.button("Monthly Executive Report"):
            st.info("Template: Monthly executive summary with cost trends and recommendations")
            
    with template_col2:
        if st.button("Weekly Cost Analysis"):
            st.info("Template: Detailed weekly cost breakdown by service and resource")
    
    # Recent Reports (mock data for now)
    st.subheader("📂 Recent Reports")
    
    recent_reports = pd.DataFrame({
        'Report Name': ['Monthly Executive Report', 'Cost Analysis Q4', 'Tag Compliance Audit'],
        'Date': ['2024-01-15', '2024-01-10', '2024-01-05'],
        'Format': ['PDF', 'Excel', 'JSON'],
        'Size': ['2.3 MB', '1.8 MB', '0.5 MB']
    })
    
    st.dataframe(recent_reports, use_container_width=True)

elif selected_tab == "tab9":
    # Tag Compliance Tab
    st.header("🏷️ Resource Tag Compliance")
    
    # Initialize tag compliance agent
    tag_agent = TagComplianceAgent()
    
    # Compliance Overview
    col1, col2, col3, col4 = st.columns(4)
    
    # Quick Actions
    with col1:
        if st.button("🔍 Scan Compliance", type="primary"):
            with st.spinner("Scanning resources for tag compliance..."):
                response, data = tag_agent.perform_compliance_scan()
                st.session_state['compliance_data'] = data
                st.session_state['compliance_response'] = response
    
    with col2:
        if st.button("📊 Generate Report"):
            with st.spinner("Generating compliance report..."):
                response, data = tag_agent.generate_compliance_report()
                st.session_state['compliance_report'] = response
                st.session_state['report_data'] = data
    
    with col3:
        if st.button("🔧 Suggest Remediation"):
            with st.spinner("Analyzing and suggesting remediation..."):
                response, data = tag_agent.suggest_remediation()
                st.session_state['remediation'] = response
                st.session_state['remediation_data'] = data
    
    with col4:
        if st.button("📈 Show Trends"):
            with st.spinner("Analyzing compliance trends..."):
                response, data = tag_agent.analyze_compliance_trends()
                st.session_state['compliance_trends'] = response
                st.session_state['trends_data'] = data
    
    # Display compliance results
    if 'compliance_data' in st.session_state:
        st.markdown("### 📊 Compliance Summary")
        
        data = st.session_state['compliance_data']
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Compliance Rate", f"{data.get('compliance_rate', 0):.1f}%", 
                     delta=f"{data.get('compliance_rate', 0) - 80:.1f}%")
        with col2:
            st.metric("Total Resources", data.get('total_resources', 0))
        with col3:
            st.metric("Non-Compliant", data.get('non_compliant_count', 0))
        with col4:
            st.metric("Missing Tags", sum(data.get('missing_tags_summary', {}).values()))
        
        # Compliance visualization
        if data.get('compliance_rate', 0) > 0:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = data.get('compliance_rate', 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Tag Compliance Score"},
                delta = {'reference': 90},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display full response
        with st.expander("📝 Detailed Compliance Report", expanded=True):
            st.markdown(st.session_state['compliance_response'])
    
    # Non-compliant resources
    if 'compliance_data' in st.session_state and 'resources_by_compliance' in st.session_state['compliance_data']:
        st.markdown("### 🚨 Non-Compliant Resources")
        
        non_compliant = st.session_state['compliance_data']['resources_by_compliance'].get('non_compliant', [])
        if non_compliant:
            # Create DataFrame for display
            df_data = []
            for resource in non_compliant[:10]:  # Show first 10
                df_data.append({
                    'Resource ID': resource['resource_id'],
                    'Type': resource['resource_type'],
                    'Missing Tags': ', '.join(resource['missing_tags']),
                    'Region': resource.get('region', 'N/A')
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Export Non-Compliant Resources (CSV)",
                data=csv,
                file_name=f"non_compliant_resources_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.success("✅ All resources are compliant!")
    
    st.markdown("---")
    st.info("💡 **Tip**: The new Report Generator and Tag Compliance features are now easily accessible from the sidebar!")

else:
    # Display message for other tabs
    st.info(f"The {selected_tab_name} feature is available in the main dashboard. This demo shows the new Report Generator and Tag Compliance features.")
    st.markdown("### Available Features:")
    st.markdown("- **📋 Report Generator**: Generate comprehensive FinOps reports in PDF, Excel, or JSON format")
    st.markdown("- **🏷️ Tag Compliance**: Monitor and enforce resource tagging policies")

# Footer
st.markdown("---")
st.caption(f"🟢 System Status: Operational | Account: {account_id} | Last Update: {datetime.now().strftime('%H:%M:%S')}")