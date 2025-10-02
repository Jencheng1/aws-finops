#!/usr/bin/env python3
"""
Minimal FinOps Dashboard to test tab display
"""

import streamlit as st
import boto3
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AWS FinOps Platform",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("💰 AWS FinOps Intelligence Platform")

# Show current config
try:
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    st.caption(f"Account: {account_id}")
except:
    st.caption("Account: Demo Mode")

# Create all 9 tabs
st.markdown("### All Features")
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Cost Intelligence",
    "💬 Multi-Agent Chat",
    "🏢 Business Context (Apptio)",
    "🔍 Resource Optimization",
    "💎 Savings Plans",
    "🔮 Budget Prediction",
    "📈 Executive Dashboard",
    "📋 Report Generator",
    "🏷️ Tag Compliance"
])

# Tab 1
with tab1:
    st.header("📊 Cost Intelligence")
    st.info("Cost analysis and visualization features")

# Tab 2
with tab2:
    st.header("💬 Multi-Agent Chat")
    st.info("AI-powered FinOps assistant with 6 specialized agents")

# Tab 3
with tab3:
    st.header("🏢 Business Context (Apptio)")
    st.info("TBM taxonomy mapping and business alignment")

# Tab 4
with tab4:
    st.header("🔍 Resource Optimization")
    st.info("Find and eliminate idle resources")

# Tab 5
with tab5:
    st.header("💎 Savings Plans")
    st.info("Savings plan recommendations and ROI analysis")

# Tab 6
with tab6:
    st.header("🔮 Budget Prediction")
    st.info("AI-powered budget forecasting")

# Tab 7
with tab7:
    st.header("📈 Executive Dashboard")
    st.info("High-level KPIs and trends")

# Tab 8 - NEW
with tab8:
    st.header("📋 Report Generator")
    st.success("🆕 NEW FEATURE!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Report Type", ["Full", "Executive", "Technical"])
    with col2:
        st.selectbox("Format", ["PDF", "Excel", "JSON"])
    with col3:
        st.button("Generate Report", type="primary")
    
    st.info("Generate comprehensive FinOps reports in multiple formats")

# Tab 9 - NEW
with tab9:
    st.header("🏷️ Tag Compliance")
    st.success("🆕 NEW FEATURE!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Scan Compliance", type="primary")
    with col2:
        st.button("Generate Report")
    
    st.info("Monitor and enforce resource tagging policies")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")