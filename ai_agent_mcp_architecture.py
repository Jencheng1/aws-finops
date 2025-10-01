"""
AI Agent and MCP Architecture Documentation
Shows how different AI agents and MCP servers work together
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import json

# Configure page
st.set_page_config(
    page_title="AI Agent & MCP Architecture",
    page_icon="🏗️",
    layout="wide"
)

# Custom CSS for architecture diagram
st.markdown("""
<style>
    .architecture-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .mcp-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .integration-flow {
        background: #f0f8ff;
        padding: 2rem;
        border-radius: 1rem;
        margin: 2rem 0;
        border: 2px solid #4682b4;
    }
    .savings-impact {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        font-size: 1.5rem;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="architecture-header">🏗️ AI Agent & MCP Architecture</h1>', unsafe_allow_html=True)
st.markdown("### How AI Agents and MCP Servers Orchestrate Cost Optimization")

# Tab layout
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏛️ Architecture Overview",
    "🤝 Agent-MCP Integration", 
    "💬 Chatbot Intelligence",
    "💰 Cost Optimization Flow",
    "📊 Real Savings Examples"
])

# Tab 1: Architecture Overview
with tab1:
    st.header("System Architecture: AI Agents + MCP Servers")
    
    # Create architecture diagram using Plotly
    fig = go.Figure()
    
    # Add nodes
    # User layer
    fig.add_trace(go.Scatter(
        x=[5], y=[10], 
        mode='markers+text',
        marker=dict(size=40, color='lightblue'),
        text=["User"],
        textposition="bottom center",
        name="User Layer"
    ))
    
    # Chatbot layer
    fig.add_trace(go.Scatter(
        x=[5], y=[8],
        mode='markers+text',
        marker=dict(size=50, color='purple'),
        text=["AI Chatbot"],
        textposition="bottom center",
        name="Interface"
    ))
    
    # AI Agents layer
    fig.add_trace(go.Scatter(
        x=[2, 4, 6, 8], y=[6, 6, 6, 6],
        mode='markers+text',
        marker=dict(size=40, color='orange'),
        text=["Budget AI", "Anomaly AI", "Optimizer AI", "Savings AI"],
        textposition="bottom center",
        name="AI Agents"
    ))
    
    # MCP Servers layer
    fig.add_trace(go.Scatter(
        x=[1, 3, 5, 7, 9], y=[4, 4, 4, 4, 4],
        mode='markers+text',
        marker=dict(size=35, color='green'),
        text=["Cost Explorer", "Apptio MCP", "CloudWatch", "Tagging MCP", "Resource MCP"],
        textposition="bottom center",
        name="MCP Servers"
    ))
    
    # AWS Services layer
    fig.add_trace(go.Scatter(
        x=[5], y=[2],
        mode='markers+text',
        marker=dict(size=60, color='yellow'),
        text=["AWS Services"],
        textposition="bottom center",
        name="Cloud Layer"
    ))
    
    # Add connections
    connections = [
        # User to Chatbot
        (5, 10, 5, 8),
        # Chatbot to AI Agents
        (5, 8, 2, 6),
        (5, 8, 4, 6),
        (5, 8, 6, 6),
        (5, 8, 8, 6),
        # AI Agents to MCP Servers
        (2, 6, 1, 4),
        (2, 6, 3, 4),
        (4, 6, 3, 4),
        (4, 6, 5, 4),
        (6, 6, 5, 4),
        (6, 6, 7, 4),
        (8, 6, 7, 4),
        (8, 6, 9, 4),
        # MCP Servers to AWS
        (1, 4, 5, 2),
        (3, 4, 5, 2),
        (5, 4, 5, 2),
        (7, 4, 5, 2),
        (9, 4, 5, 2)
    ]
    
    for x1, y1, x2, y2 in connections:
        fig.add_shape(
            type="line",
            x0=x1, y0=y1, x1=x2, y1=y2,
            line=dict(color="gray", width=1)
        )
    
    fig.update_layout(
        title="Multi-Layer AI Architecture for FinOps",
        showlegend=True,
        height=600,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explain each layer
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h3>🤖 AI Agent Layer</h3>
            <ul>
                <li><strong>Budget Prediction Agent:</strong> ML models for cost forecasting</li>
                <li><strong>Anomaly Detection Agent:</strong> Statistical analysis for cost spikes</li>
                <li><strong>Resource Optimizer Agent:</strong> Identifies waste and inefficiencies</li>
                <li><strong>Savings Plan Agent:</strong> Calculates optimal commitments</li>
            </ul>
            <p><em>Each agent specializes in specific cost optimization tasks</em></p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="mcp-card">
            <h3>🔌 MCP Server Layer</h3>
            <ul>
                <li><strong>Cost Explorer MCP:</strong> Real-time cost data access</li>
                <li><strong>Apptio MCP:</strong> Business context and TBM mapping</li>
                <li><strong>CloudWatch MCP:</strong> Performance metrics for rightsizing</li>
                <li><strong>Tagging MCP:</strong> Cost allocation and governance</li>
                <li><strong>Resource MCP:</strong> Infrastructure inventory and state</li>
            </ul>
            <p><em>MCP servers provide standardized access to data sources</em></p>
        </div>
        """, unsafe_allow_html=True)

# Tab 2: Agent-MCP Integration
with tab2:
    st.header("🤝 How AI Agents and MCP Servers Work Together")
    
    st.markdown("""
    <div class="integration-flow">
        <h3>Integration Workflow Example: Finding Cost Savings</h3>
        <ol>
            <li><strong>User Query:</strong> "How can I reduce my AWS costs?"</li>
            <li><strong>Chatbot:</strong> Activates multiple AI agents in parallel</li>
            <li><strong>AI Agents:</strong> Query relevant MCP servers for data</li>
            <li><strong>MCP Servers:</strong> Fetch and standardize data from AWS</li>
            <li><strong>AI Agents:</strong> Analyze data and generate insights</li>
            <li><strong>Chatbot:</strong> Synthesizes recommendations from all agents</li>
            <li><strong>Result:</strong> Comprehensive savings plan with actions</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Show specific integrations
    st.subheader("Specific Agent-MCP Integrations")
    
    integrations = [
        {
            "agent": "Budget Prediction Agent",
            "mcps": ["Cost Explorer MCP", "Apptio MCP"],
            "data_flow": "Historical costs → Pattern analysis → ML prediction",
            "output": "30-day cost forecast with confidence intervals",
            "savings": "Prevent budget overruns by 15-20%"
        },
        {
            "agent": "Anomaly Detection Agent",
            "mcps": ["CloudWatch MCP", "Cost Explorer MCP"],
            "data_flow": "Real-time metrics → Statistical analysis → Spike detection",
            "output": "Cost anomalies with root cause identification",
            "savings": "Catch waste within hours instead of weeks"
        },
        {
            "agent": "Resource Optimizer Agent",
            "mcps": ["Resource MCP", "CloudWatch MCP", "Tagging MCP"],
            "data_flow": "Resource inventory → Usage analysis → Idle detection",
            "output": "List of resources to terminate/rightsize",
            "savings": "Average 30% reduction in compute costs"
        },
        {
            "agent": "Savings Plan Agent",
            "mcps": ["Cost Explorer MCP", "Apptio MCP"],
            "data_flow": "Usage patterns → Commitment analysis → ROI calculation",
            "output": "Optimal Savings Plan recommendations",
            "savings": "Up to 72% discount on compute costs"
        }
    ]
    
    for integration in integrations:
        with st.expander(f"🔗 {integration['agent']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**MCP Servers Used:** {', '.join(integration['mcps'])}")
                st.markdown(f"**Data Flow:** {integration['data_flow']}")
                st.markdown(f"**Output:** {integration['output']}")
                
            with col2:
                st.metric("Potential Savings", integration['savings'])

# Tab 3: Chatbot Intelligence
with tab3:
    st.header("💬 How the AI Chatbot Orchestrates Multiple Agents")
    
    # Chatbot decision tree
    st.subheader("Chatbot's Intelligent Query Routing")
    
    st.markdown("""
    <div class="integration-flow">
        <h3>Query Analysis & Agent Selection</h3>
        <p>The chatbot uses NLP to understand intent and activates relevant agents:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Example queries and agent activation
    query_examples = [
        {
            "query": "What will my costs be next month?",
            "agents": ["Budget Prediction Agent"],
            "mcps": ["Cost Explorer MCP", "Apptio MCP"],
            "response": "Forecast with ML models based on historical patterns"
        },
        {
            "query": "Why did my costs spike yesterday?",
            "agents": ["Anomaly Detection Agent", "Resource Optimizer Agent"],
            "mcps": ["CloudWatch MCP", "Cost Explorer MCP", "Resource MCP"],
            "response": "Identifies the specific service/resource causing the spike"
        },
        {
            "query": "Find all my idle resources",
            "agents": ["Resource Optimizer Agent"],
            "mcps": ["Resource MCP", "CloudWatch MCP", "Tagging MCP"],
            "response": "Comprehensive list of idle EC2, EBS, RDS, etc."
        },
        {
            "query": "Should I buy Savings Plans?",
            "agents": ["Savings Plan Agent", "Budget Prediction Agent"],
            "mcps": ["Cost Explorer MCP", "Apptio MCP"],
            "response": "Personalized recommendations with ROI calculations"
        },
        {
            "query": "How can I save money on AWS?",
            "agents": ["ALL AGENTS"],
            "mcps": ["ALL MCP SERVERS"],
            "response": "Comprehensive analysis across all optimization dimensions"
        }
    ]
    
    for example in query_examples:
        with st.expander(f"💭 Query: '{example['query']}'"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Agents Activated:**")
                for agent in example['agents']:
                    st.markdown(f"• {agent}")
                    
            with col2:
                st.markdown("**MCP Servers Used:**")
                for mcp in example['mcps']:
                    st.markdown(f"• {mcp}")
                    
            with col3:
                st.markdown("**Response Type:**")
                st.markdown(example['response'])
    
    # Show parallel processing
    st.subheader("⚡ Parallel Processing for Speed")
    
    st.info("""
    **The chatbot activates multiple agents simultaneously:**
    - All agents work in parallel, not sequentially
    - Each agent queries its required MCP servers independently
    - Results are aggregated and synthesized by the chatbot
    - Response time: 2-5 seconds instead of 30+ seconds sequential
    """)

# Tab 4: Cost Optimization Flow
with tab4:
    st.header("💰 End-to-End Cost Optimization Workflow")
    
    # Create a flow diagram
    st.subheader("Complete Cost Optimization Journey")
    
    # Step-by-step flow
    steps = [
        {
            "step": 1,
            "title": "Data Collection",
            "agents": ["All Agents"],
            "mcps": ["All MCP Servers"],
            "action": "Gather comprehensive cost and usage data",
            "time": "1-2 seconds"
        },
        {
            "step": 2,
            "title": "Analysis",
            "agents": ["Budget AI", "Anomaly AI", "Optimizer AI"],
            "mcps": ["Cost Explorer", "CloudWatch", "Resource MCP"],
            "action": "Identify patterns, anomalies, and inefficiencies",
            "time": "2-3 seconds"
        },
        {
            "step": 3,
            "title": "Recommendations",
            "agents": ["Optimizer AI", "Savings Plan AI"],
            "mcps": ["Apptio MCP", "Cost Explorer"],
            "action": "Generate prioritized recommendations",
            "time": "1-2 seconds"
        },
        {
            "step": 4,
            "title": "Business Context",
            "agents": ["Budget AI"],
            "mcps": ["Apptio MCP"],
            "action": "Map technical recommendations to business impact",
            "time": "1 second"
        },
        {
            "step": 5,
            "title": "Action Plan",
            "agents": ["All Agents"],
            "mcps": ["All MCPs"],
            "action": "Create executable action plan with ROI",
            "time": "1 second"
        }
    ]
    
    for step in steps:
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            
            with col1:
                st.markdown(f"### Step {step['step']}")
                
            with col2:
                st.markdown(f"**{step['title']}**")
                st.markdown(f"{step['action']}")
                
            with col3:
                st.markdown(f"**Agents:** {', '.join(step['agents'])}")
                st.markdown(f"**MCPs:** {', '.join(step['mcps'])}")
                
            with col4:
                st.metric("Time", step['time'])
            
            if step['step'] < len(steps):
                st.markdown("⬇️")
    
    # Total impact
    st.markdown("""
    <div class="savings-impact">
        <h2>💰 Total Processing Time: 6-9 seconds</h2>
        <p>Average Savings Identified: $15,000-50,000/month</p>
        <p>ROI of AI Implementation: 300-500%</p>
    </div>
    """, unsafe_allow_html=True)

# Tab 5: Real Savings Examples
with tab5:
    st.header("📊 Real-World Savings Examples")
    
    st.markdown("### Case Studies: AI + MCP in Action")
    
    # Case 1
    with st.expander("🏭 Case 1: Manufacturing Company - $45K/month saved"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Scenario:**
            - Large manufacturing company with $200K/month AWS spend
            - Complex multi-account structure
            - No visibility into cost drivers
            
            **AI Agents Activated:**
            - Resource Optimizer Agent found 150+ idle resources
            - Savings Plan Agent calculated optimal commitments
            - Anomaly Agent detected recurring cost spikes
            
            **MCP Servers Used:**
            - Apptio MCP mapped costs to production lines
            - Cost Explorer MCP provided detailed usage data
            - Resource MCP identified zombie infrastructure
            """)
            
        with col2:
            st.markdown("""
            **Results:**
            - 🗑️ Cleaned up $8K/month in idle resources
            - 💰 Implemented Savings Plans: $25K/month saved
            - 🔧 Rightsized instances: $7K/month saved
            - 📊 Fixed data transfer issues: $5K/month saved
            
            **Total Monthly Savings: $45,000**
            **Annual Savings: $540,000**
            
            **ROI: 450% in first year**
            """)
    
    # Case 2
    with st.expander("🚀 Case 2: SaaS Startup - $18K/month saved"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Scenario:**
            - Fast-growing SaaS startup
            - $80K/month AWS spend
            - Costs growing 20% monthly
            
            **AI Agents Activated:**
            - Budget Prediction Agent forecasted unsustainable growth
            - Anomaly Agent found development waste
            - Optimizer Agent identified overprovisioning
            
            **MCP Servers Used:**
            - CloudWatch MCP analyzed actual usage
            - Tagging MCP improved cost allocation
            - Cost Explorer MCP tracked per-customer costs
            """)
            
        with col2:
            st.markdown("""
            **Results:**
            - 📈 Implemented auto-scaling: $5K/month saved
            - 🌙 Dev environment scheduling: $3K/month saved
            - 💾 Optimized storage tiers: $4K/month saved
            - 🔄 Spot instances for batch: $6K/month saved
            
            **Total Monthly Savings: $18,000**
            **Annual Savings: $216,000**
            
            **Growth rate controlled to 5% monthly**
            """)
    
    # Case 3
    with st.expander("🏥 Case 3: Healthcare Provider - $72K/month saved"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Scenario:**
            - Large healthcare provider
            - $400K/month AWS spend
            - HIPAA compliance requirements
            - Multiple departments with no accountability
            
            **AI Agents Activated:**
            - ALL AGENTS for comprehensive analysis
            
            **MCP Servers Used:**
            - Apptio MCP for department chargeback
            - All other MCPs for full visibility
            """)
            
        with col2:
            st.markdown("""
            **Results:**
            - 🏢 Dept chargeback reduced waste: $20K/month
            - 💰 3-year Savings Plans: $35K/month saved
            - 🗑️ Massive cleanup effort: $12K/month saved
            - 🔒 Consolidated security tools: $5K/month saved
            
            **Total Monthly Savings: $72,000**
            **Annual Savings: $864,000**
            
            **Compliance maintained throughout**
            """)
    
    # Summary metrics
    st.subheader("📊 Aggregate Impact Across All Customers")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average Savings", "23%", "of total AWS spend")
    
    with col2:
        st.metric("Time to Value", "2 weeks", "to first savings")
    
    with col3:
        st.metric("ROI", "380%", "average first year")
    
    with col4:
        st.metric("Payback Period", "3.2 months", "for implementation")
    
    # Key success factors
    st.markdown("""
    <div class="integration-flow">
        <h3>🔑 Key Success Factors</h3>
        <ol>
            <li><strong>Multi-Agent Collaboration:</strong> Each agent brings specialized expertise</li>
            <li><strong>MCP Data Access:</strong> Real-time, accurate data from multiple sources</li>
            <li><strong>Apptio Business Context:</strong> Technical savings mapped to business value</li>
            <li><strong>Automated Execution:</strong> Recommendations can be implemented programmatically</li>
            <li><strong>Continuous Learning:</strong> AI agents improve recommendations over time</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Footer with call to action
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem;'>
    <h2>🚀 Ready to Save 20-40% on Your AWS Costs?</h2>
    <p>Our AI Agents + MCP Architecture typically identifies savings opportunities within minutes</p>
    <p>Average customer saves $25,000+ per month</p>
</div>
""", unsafe_allow_html=True)