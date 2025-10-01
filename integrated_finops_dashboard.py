import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import time
import uuid
import random

# Initialize AWS clients
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
lambda_client = boto3.client('lambda')
bedrock_runtime = boto3.client('bedrock-agent-runtime')
sts = boto3.client('sts')

# Page configuration
st.set_page_config(
    page_title="Integrated AI FinOps Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .recommendation-card {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .apptio-highlight {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .agent-card {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #4682b4;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'cost_data_cache' not in st.session_state:
    st.session_state.cost_data_cache = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'idle_resources' not in st.session_state:
    st.session_state.idle_resources = []
if 'savings_plans' not in st.session_state:
    st.session_state.savings_plans = []

# Get account info
try:
    account_id = sts.get_caller_identity()['Account']
except:
    account_id = "123456789012"  # Dummy account ID for demo

# Load configuration
try:
    with open('finops_config.json', 'r') as f:
        config = json.load(f)
    AGENT_ID = config['agents'][0]['agent_id']
    AGENT_ALIAS = config['agents'][0]['alias_id']
except:
    AGENT_ID = "DEMO_AGENT_ID"
    AGENT_ALIAS = "DEMO_ALIAS"

# Title
st.markdown('<h1 class="main-header">🚀 Integrated AI FinOps Platform</h1>', unsafe_allow_html=True)
st.markdown("### Unified Cost Management, AI-Powered Insights, and Automated Optimization")

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Time period selection
    st.subheader("Analysis Period")
    col1, col2 = st.columns(2)
    with col1:
        days = st.slider("Days", 1, 90, 7)
    with col2:
        granularity = st.selectbox("Granularity", ["DAILY", "MONTHLY", "HOURLY"])
    
    # Feature toggles
    st.subheader("Features")
    use_apptio = st.checkbox("Enable Apptio Integration", True)
    use_ai_agents = st.checkbox("Enable AI Agents", True)
    enable_auto_optimization = st.checkbox("Auto-Optimization Mode", False)
    
    # Quick Actions
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh All Data", type="primary"):
        st.session_state.cost_data_cache = None
        st.session_state.last_refresh = None
        st.rerun()
    
    if st.button("🤖 Run Full Analysis"):
        st.session_state.run_full_analysis = True
    
    # About section
    st.markdown("---")
    st.markdown("### About This Platform")
    st.markdown("""
    **Integrated Features:**
    - 📊 Real-time AWS Cost Analysis
    - 🤖 AI-Powered Recommendations
    - 💡 Apptio Integration for TBM
    - 🔍 Idle Resource Detection
    - 💰 Savings Plan Optimization
    - 🚀 Automated Cost Actions
    """)

# Helper Functions
def generate_dummy_apptio_data():
    """Generate dummy Apptio data for demonstration"""
    return {
        "cost_pools": {
            "Infrastructure": random.uniform(50000, 80000),
            "Applications": random.uniform(30000, 50000),
            "End User": random.uniform(20000, 30000),
            "Security": random.uniform(10000, 20000)
        },
        "business_units": {
            "Engineering": random.uniform(40000, 60000),
            "Sales": random.uniform(20000, 30000),
            "Marketing": random.uniform(15000, 25000),
            "Operations": random.uniform(25000, 35000)
        },
        "cost_trends": [
            {"month": "Jan", "actual": random.uniform(90000, 100000), "budget": 95000},
            {"month": "Feb", "actual": random.uniform(92000, 102000), "budget": 95000},
            {"month": "Mar", "actual": random.uniform(88000, 98000), "budget": 95000},
            {"month": "Apr", "actual": random.uniform(93000, 103000), "budget": 100000},
            {"month": "May", "actual": random.uniform(95000, 105000), "budget": 100000},
            {"month": "Jun", "actual": random.uniform(98000, 108000), "budget": 105000}
        ]
    }

def detect_idle_resources():
    """Simulate idle resource detection"""
    return [
        {"resource_id": "i-1234567890", "type": "EC2 Instance", "name": "dev-server-01", 
         "idle_days": 15, "monthly_cost": 150.00, "recommendation": "Terminate or stop instance"},
        {"resource_id": "vol-abcdef123", "type": "EBS Volume", "name": "Unattached Volume",
         "idle_days": 30, "monthly_cost": 50.00, "recommendation": "Delete unattached volume"},
        {"resource_id": "lb-xyz789", "type": "Load Balancer", "name": "test-lb",
         "idle_days": 7, "monthly_cost": 25.00, "recommendation": "Remove unused load balancer"},
        {"resource_id": "db-instance-1", "type": "RDS Instance", "name": "test-database",
         "idle_days": 20, "monthly_cost": 300.00, "recommendation": "Consider Aurora Serverless"},
        {"resource_id": "nat-gateway-123", "type": "NAT Gateway", "name": "unused-nat",
         "idle_days": 45, "monthly_cost": 45.00, "recommendation": "Remove if not needed"}
    ]

def generate_savings_plan_recommendations():
    """Generate savings plan recommendations"""
    return [
        {
            "type": "Compute Savings Plan",
            "term": "1 Year",
            "payment": "All Upfront",
            "hourly_commitment": 25.50,
            "estimated_savings": "28%",
            "monthly_savings": 2150.00,
            "coverage": "EC2, Fargate, Lambda"
        },
        {
            "type": "EC2 Instance Savings Plan",
            "term": "3 Years",
            "payment": "Partial Upfront",
            "hourly_commitment": 15.75,
            "estimated_savings": "42%",
            "monthly_savings": 1890.00,
            "coverage": "m5.large in us-east-1"
        },
        {
            "type": "SageMaker Savings Plan",
            "term": "1 Year",
            "payment": "No Upfront",
            "hourly_commitment": 8.25,
            "estimated_savings": "20%",
            "monthly_savings": 650.00,
            "coverage": "SageMaker instances"
        }
    ]

def get_ai_recommendations(cost_data):
    """Simulate AI-powered recommendations"""
    recommendations = []
    
    # Cost anomaly detection
    if cost_data.get('daily_trend'):
        recent_costs = cost_data['daily_trend'][-7:]
        avg_cost = sum(recent_costs) / len(recent_costs)
        if recent_costs[-1] > avg_cost * 1.2:
            recommendations.append({
                "type": "anomaly",
                "severity": "high",
                "title": "Cost Spike Detected",
                "description": f"Daily costs increased by {((recent_costs[-1]/avg_cost - 1) * 100):.1f}% above 7-day average",
                "action": "Investigate recent deployments and usage patterns"
            })
    
    # Resource optimization
    recommendations.append({
        "type": "optimization",
        "severity": "medium",
        "title": "Right-sizing Opportunity",
        "description": "15 EC2 instances are over-provisioned based on CPU/Memory utilization",
        "action": "Downsize to save ~$1,200/month",
        "confidence": "85%"
    })
    
    # Reserved instance recommendations
    recommendations.append({
        "type": "savings",
        "severity": "medium",
        "title": "Reserved Instance Coverage",
        "description": "Current RI coverage is 65%. Increasing to 80% could save $3,500/month",
        "action": "Purchase additional RIs for stable workloads",
        "confidence": "92%"
    })
    
    return recommendations

# Main Content - Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Dashboard", 
    "🏢 Apptio TBM View", 
    "🤖 AI Cost Assistant",
    "🔍 Resource Optimization",
    "💰 Savings Plans",
    "📈 Advanced Analytics"
])

# Tab 1: Executive Dashboard
with tab1:
    st.header("Executive Cost Overview")
    
    # Fetch cost data
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        if not st.session_state.cost_data_cache or st.session_state.last_refresh != days:
            with st.spinner("Loading cost data..."):
                response = ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity=granularity,
                    Metrics=['UnblendedCost', 'UsageQuantity'],
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                    ]
                )
                st.session_state.cost_data_cache = response
                st.session_state.last_refresh = days
        
        cost_data = st.session_state.cost_data_cache
        
        # Process data
        daily_costs = []
        service_costs = {}
        
        for result in cost_data['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total_cost = 0
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                total_cost += cost
                if service not in service_costs:
                    service_costs[service] = 0
                service_costs[service] += cost
            daily_costs.append({'Date': date, 'Cost': total_cost})
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_cost = sum(item['Cost'] for item in daily_costs)
        avg_daily_cost = total_cost / len(daily_costs) if daily_costs else 0
        projected_monthly = avg_daily_cost * 30
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Cost", f"${total_cost:,.2f}", f"Last {days} days")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Daily Average", f"${avg_daily_cost:,.2f}", "↑ 5.2%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Monthly Projection", f"${projected_monthly:,.2f}", "On track")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("YTD Savings", "$45,230", "↑ 12.5%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Daily trend
            df_daily = pd.DataFrame(daily_costs)
            fig = px.line(df_daily, x='Date', y='Cost', title='Daily Cost Trend')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top services pie chart
            top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:5]
            df_services = pd.DataFrame(top_services, columns=['Service', 'Cost'])
            fig = px.pie(df_services, values='Cost', names='Service', title='Top 5 Services by Cost')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # AI Recommendations
        if use_ai_agents:
            st.header("🤖 AI-Powered Recommendations")
            recommendations = get_ai_recommendations({'daily_trend': [item['Cost'] for item in daily_costs]})
            
            cols = st.columns(len(recommendations))
            for idx, rec in enumerate(recommendations):
                with cols[idx]:
                    severity_color = {
                        "high": "#ff4444",
                        "medium": "#ffaa00",
                        "low": "#00aa00"
                    }
                    st.markdown(f"""
                    <div class="recommendation-card">
                        <h4 style="color: {severity_color[rec['severity']]};">{rec['title']}</h4>
                        <p>{rec['description']}</p>
                        <p><strong>Action:</strong> {rec['action']}</p>
                        {f"<p><em>Confidence: {rec.get('confidence', 'N/A')}</em></p>" if 'confidence' in rec else ""}
                    </div>
                    """, unsafe_allow_html=True)
    
    except ClientError as e:
        st.error(f"Error fetching cost data: {e}")
        # Use dummy data for demo
        st.info("Using demo data for illustration")
        daily_costs = [{"Date": f"2024-01-{i:02d}", "Cost": random.uniform(1000, 2000)} for i in range(1, 8)]
        df_daily = pd.DataFrame(daily_costs)
        fig = px.line(df_daily, x='Date', y='Cost', title='Daily Cost Trend (Demo Data)')
        st.plotly_chart(fig, use_container_width=True)

# Tab 2: Apptio TBM View
with tab2:
    st.header("🏢 Apptio Technology Business Management (TBM)")
    
    if use_apptio:
        st.markdown("""
        <div class="apptio-highlight">
        <h4>🔍 Why Apptio MCP Server Integration?</h4>
        <p>The Apptio MCP Server enables seamless integration between AWS cost data and Apptio's TBM framework, providing:</p>
        <ul>
            <li><strong>IT Financial Management:</strong> Allocate IT costs to business units and applications</li>
            <li><strong>Cost Transparency:</strong> Show IT spending in business-relevant terms</li>
            <li><strong>Benchmarking:</strong> Compare costs against industry standards</li>
            <li><strong>Chargeback/Showback:</strong> Implement cost allocation to departments</li>
            <li><strong>Strategic Planning:</strong> Align IT investments with business outcomes</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate dummy Apptio data
        apptio_data = generate_dummy_apptio_data()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost Pools
            st.subheader("IT Cost Pools")
            df_pools = pd.DataFrame(list(apptio_data["cost_pools"].items()), 
                                   columns=['Category', 'Cost'])
            fig = px.bar(df_pools, x='Category', y='Cost', 
                        title='IT Spending by Cost Pool',
                        color='Cost', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Business Units
            st.subheader("Business Unit Allocation")
            df_units = pd.DataFrame(list(apptio_data["business_units"].items()), 
                                   columns=['Unit', 'Cost'])
            fig = px.pie(df_units, values='Cost', names='Unit', 
                        title='Cost Distribution by Business Unit')
            st.plotly_chart(fig, use_container_width=True)
        
        # Budget vs Actual
        st.subheader("Budget vs Actual Spending")
        df_trends = pd.DataFrame(apptio_data["cost_trends"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_trends['month'], y=df_trends['actual'],
                                mode='lines+markers', name='Actual',
                                line=dict(color='blue', width=2)))
        fig.add_trace(go.Scatter(x=df_trends['month'], y=df_trends['budget'],
                                mode='lines+markers', name='Budget',
                                line=dict(color='red', width=2, dash='dash')))
        fig.update_layout(title='Monthly Budget vs Actual', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # TBM Metrics
        st.subheader("Key TBM Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("IT Spend per Employee", "$8,450", "↓ 3.2%")
        with col2:
            st.metric("Infrastructure Efficiency", "78%", "↑ 5.1%")
        with col3:
            st.metric("Application TCO", "$2.3M", "↓ 8.7%")
        with col4:
            st.metric("Cost per Transaction", "$0.012", "↓ 15.3%")
    
    else:
        st.info("Enable Apptio Integration in the sidebar to view TBM insights")

# Tab 3: AI Cost Assistant
with tab3:
    st.header("🤖 AI-Powered Cost Assistant")
    
    if use_ai_agents:
        st.markdown("""
        <div class="agent-card">
        <h4>🎯 Value of AI Agents vs AWS Cost Insights</h4>
        <p>While AWS Cost Explorer provides basic cost insights, our AI agents offer:</p>
        <ul>
            <li><strong>Contextual Understanding:</strong> Understands your specific architecture and business needs</li>
            <li><strong>Proactive Recommendations:</strong> Identifies opportunities before they become issues</li>
            <li><strong>Cross-Service Optimization:</strong> Analyzes patterns across all AWS services</li>
            <li><strong>Natural Language Queries:</strong> Ask complex questions in plain English</li>
            <li><strong>Automated Actions:</strong> Can execute cost-saving actions with approval</li>
            <li><strong>Learning Capability:</strong> Improves recommendations based on your decisions</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat interface
        st.subheader("Chat with Your FinOps AI Assistant")
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about costs, savings, or optimization..."):
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    # Simulate AI response
                    if "savings plan" in prompt.lower():
                        response = """Based on your usage patterns, I recommend:

**Compute Savings Plan** (1-year, All Upfront)
- Hourly commitment: $25.50
- Estimated savings: 28% (~$2,150/month)
- Covers: EC2, Fargate, and Lambda

**EC2 Instance Savings Plan** (3-year, Partial Upfront)
- Hourly commitment: $15.75
- Estimated savings: 42% (~$1,890/month)
- Specific to m5.large instances in us-east-1

Would you like me to calculate the exact commitment amount based on your last 30 days of usage?"""
                    elif "idle" in prompt.lower() or "unused" in prompt.lower():
                        response = """I've identified 5 idle resources costing $570/month:

1. **EC2 Instance** (i-1234567890)
   - Idle for 15 days
   - Cost: $150/month
   - Action: Terminate or stop

2. **Unattached EBS Volume** (vol-abcdef123)
   - Idle for 30 days
   - Cost: $50/month
   - Action: Delete

3. **RDS Test Database** (db-instance-1)
   - Low usage for 20 days
   - Cost: $300/month
   - Action: Consider Aurora Serverless

Would you like me to create a cleanup plan?"""
                    else:
                        response = """I'm analyzing your AWS costs. Here are the key insights:

📊 **Current Status:**
- Total monthly spend: $45,678
- Trending 12% above last month
- Primary cost driver: EC2 (45% of total)

💡 **Top 3 Optimization Opportunities:**
1. Right-size 15 over-provisioned instances (save ~$1,200/month)
2. Increase RI coverage from 65% to 80% (save ~$3,500/month)
3. Remove 5 idle resources (save ~$570/month)

What specific area would you like to explore further?"""
                    
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        # Quick action buttons
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Find Idle Resources"):
                st.session_state.idle_resources = detect_idle_resources()
                st.success("Found 5 idle resources!")
                
        with col2:
            if st.button("💰 Recommend Savings Plans"):
                st.session_state.savings_plans = generate_savings_plan_recommendations()
                st.success("Generated 3 savings plan recommendations!")
                
        with col3:
            if st.button("📊 Analyze Cost Anomalies"):
                st.info("Analyzing last 7 days for anomalies...")
                time.sleep(1)
                st.success("Found 2 cost spikes that need attention!")
    
    else:
        st.info("Enable AI Agents in the sidebar to use the cost assistant")

# Tab 4: Resource Optimization
with tab4:
    st.header("🔍 Resource Optimization & Cleanup")
    
    # Idle resources section
    st.subheader("Idle Resources Detection")
    
    if st.button("🔄 Scan for Idle Resources", key="scan_idle"):
        with st.spinner("Scanning AWS resources..."):
            st.session_state.idle_resources = detect_idle_resources()
    
    if st.session_state.idle_resources:
        # Summary metrics
        total_idle_cost = sum(r['monthly_cost'] for r in st.session_state.idle_resources)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Idle Resources Found", len(st.session_state.idle_resources))
        with col2:
            st.metric("Monthly Waste", f"${total_idle_cost:,.2f}")
        with col3:
            st.metric("Potential Annual Savings", f"${total_idle_cost * 12:,.2f}")
        
        # Detailed table
        st.subheader("Idle Resources Details")
        df_idle = pd.DataFrame(st.session_state.idle_resources)
        
        # Add action column
        for idx, row in df_idle.iterrows():
            if st.button(f"Take Action", key=f"action_{row['resource_id']}"):
                st.success(f"Action initiated for {row['resource_id']}")
        
        st.dataframe(df_idle, use_container_width=True)
        
        # Visualization
        fig = px.bar(df_idle, x='name', y='monthly_cost', 
                    color='type', title='Monthly Cost by Idle Resource',
                    hover_data=['idle_days', 'recommendation'])
        st.plotly_chart(fig, use_container_width=True)
    
    # Resource rightsizing
    st.subheader("Resource Rightsizing Opportunities")
    
    rightsizing_data = [
        {"instance_id": "i-0987654321", "current_type": "m5.xlarge", 
         "recommended_type": "m5.large", "cpu_avg": "25%", 
         "memory_avg": "40%", "monthly_savings": 180},
        {"instance_id": "i-1122334455", "current_type": "c5.2xlarge", 
         "recommended_type": "c5.xlarge", "cpu_avg": "35%", 
         "memory_avg": "30%", "monthly_savings": 250},
        {"instance_id": "i-5544332211", "current_type": "r5.large", 
         "recommended_type": "t3.large", "cpu_avg": "15%", 
         "memory_avg": "20%", "monthly_savings": 95}
    ]
    
    df_rightsize = pd.DataFrame(rightsizing_data)
    st.dataframe(df_rightsize, use_container_width=True)
    
    total_rightsize_savings = df_rightsize['monthly_savings'].sum()
    st.info(f"Total potential savings from rightsizing: ${total_rightsize_savings:,.2f}/month")

# Tab 5: Savings Plans
with tab5:
    st.header("💰 Savings Plans & Reserved Instances")
    
    # Current coverage
    st.subheader("Current Coverage Analysis")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("On-Demand Spend", "$28,450/mo", "65% of total")
    with col2:
        st.metric("RI Coverage", "35%", "↑ 5% from last month")
    with col3:
        st.metric("SP Coverage", "15%", "New this month")
    with col4:
        st.metric("Spot Usage", "8%", "For batch workloads")
    
    # Recommendations
    st.subheader("Savings Plan Recommendations")
    
    if st.button("🤖 Generate AI-Powered Recommendations", key="gen_sp"):
        with st.spinner("Analyzing usage patterns..."):
            st.session_state.savings_plans = generate_savings_plan_recommendations()
    
    if st.session_state.savings_plans:
        for idx, plan in enumerate(st.session_state.savings_plans):
            with st.expander(f"{plan['type']} - Save ${plan['monthly_savings']:,.0f}/month"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Details:**
                    - Term: {plan['term']}
                    - Payment: {plan['payment']}
                    - Hourly Commitment: ${plan['hourly_commitment']}
                    - Estimated Savings: {plan['estimated_savings']}
                    - Coverage: {plan['coverage']}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Financial Impact:**
                    - Monthly Savings: ${plan['monthly_savings']:,.2f}
                    - Annual Savings: ${plan['monthly_savings'] * 12:,.2f}
                    - Break-even: ~3-4 months
                    """)
                
                if st.button(f"Calculate Exact Commitment", key=f"calc_{idx}"):
                    st.info("Calculating based on last 30 days usage...")
                    time.sleep(1)
                    st.success(f"Recommended hourly commitment: ${plan['hourly_commitment'] * 0.95:.2f}")
    
    # Comparison chart
    st.subheader("Savings Plan Comparison")
    
    comparison_data = {
        "Plan Type": ["No Savings Plan", "1-Year SP", "3-Year SP", "1-Year RI", "3-Year RI"],
        "Monthly Cost": [10000, 7200, 5800, 7000, 5500],
        "Flexibility": [100, 80, 60, 40, 20],
        "Savings %": [0, 28, 42, 30, 45]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    fig = go.Figure()
    
    fig.add_trace(go.Bar(name='Monthly Cost', x=df_comparison['Plan Type'], 
                        y=df_comparison['Monthly Cost'], yaxis='y'))
    fig.add_trace(go.Scatter(name='Flexibility Score', x=df_comparison['Plan Type'], 
                            y=df_comparison['Flexibility'], yaxis='y2', 
                            mode='lines+markers', line=dict(color='red')))
    
    fig.update_layout(
        title='Cost vs Flexibility Comparison',
        yaxis=dict(title='Monthly Cost ($)', side='left'),
        yaxis2=dict(title='Flexibility Score', overlaying='y', side='right'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Tab 6: Advanced Analytics
with tab6:
    st.header("📈 Advanced Analytics & Forecasting")
    
    # Cost forecasting
    st.subheader("Cost Forecasting")
    
    # Generate forecast data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    historical_costs = [random.uniform(40000, 50000) for _ in range(6)]
    forecast_costs = [random.uniform(48000, 55000) for _ in range(6)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates[:6], y=historical_costs,
                            mode='lines+markers', name='Historical',
                            line=dict(color='blue', width=2)))
    fig.add_trace(go.Scatter(x=dates[5:], y=[historical_costs[-1]] + forecast_costs,
                            mode='lines+markers', name='Forecast',
                            line=dict(color='red', width=2, dash='dash')))
    
    # Add confidence interval
    upper_bound = [c * 1.1 for c in forecast_costs]
    lower_bound = [c * 0.9 for c in forecast_costs]
    
    fig.add_trace(go.Scatter(x=dates[6:], y=upper_bound,
                            fill=None, mode='lines',
                            line_color='rgba(255,0,0,0)',
                            showlegend=False))
    fig.add_trace(go.Scatter(x=dates[6:], y=lower_bound,
                            fill='tonexty', mode='lines',
                            line_color='rgba(255,0,0,0)',
                            name='Confidence Interval'))
    
    fig.update_layout(title='12-Month Cost Forecast', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Cost allocation analysis
    st.subheader("Cost Allocation Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tag coverage
        tag_data = {
            "Tag": ["Environment", "Project", "Owner", "Department", "CostCenter"],
            "Coverage": [95, 88, 76, 82, 91]
        }
        df_tags = pd.DataFrame(tag_data)
        fig = px.bar(df_tags, x='Tag', y='Coverage', title='Resource Tag Coverage (%)',
                    color='Coverage', color_continuous_scale='Greens')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Untagged resources cost
        untagged_data = {
            "Service": ["EC2", "RDS", "S3", "Lambda", "ELB"],
            "Untagged Cost": [2340, 1560, 890, 450, 340]
        }
        df_untagged = pd.DataFrame(untagged_data)
        fig = px.pie(df_untagged, values='Untagged Cost', names='Service',
                    title='Untagged Resources by Service ($)')
        st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly detection
    st.subheader("Cost Anomaly Detection")
    
    # Generate anomaly data
    anomaly_dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    normal_costs = [random.uniform(1000, 1500) for _ in range(30)]
    # Add some anomalies
    normal_costs[10] = 2500
    normal_costs[20] = 2800
    normal_costs[25] = 2200
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=anomaly_dates, y=normal_costs,
                            mode='lines+markers', name='Daily Cost'))
    
    # Highlight anomalies
    anomaly_indices = [10, 20, 25]
    anomaly_x = [anomaly_dates[i] for i in anomaly_indices]
    anomaly_y = [normal_costs[i] for i in anomaly_indices]
    
    fig.add_trace(go.Scatter(x=anomaly_x, y=anomaly_y,
                            mode='markers', name='Anomalies',
                            marker=dict(color='red', size=12)))
    
    fig.update_layout(title='Cost Anomaly Detection (Last 30 Days)', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("🔍 Investigate Anomalies"):
        st.warning("""
        **Anomaly Analysis Results:**
        - Day 11: EC2 Auto Scaling event triggered (+$1,500)
        - Day 21: Data transfer spike to Internet (+$1,800)
        - Day 26: RDS backup retention increased (+$1,200)
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Integrated AI FinOps Platform v2.0 | Powered by AWS Bedrock, Apptio MCP, and Advanced AI Agents</p>
    <p>Last updated: {} UTC</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)