import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import boto3
import json
from datetime import datetime, timedelta
import requests

# Configure page
st.set_page_config(
    page_title="FinOps Copilot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .recommendation-card {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    .agent-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    .status-idle {
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

class FinOpsCopilot:
    def __init__(self):
        self.lambda_client = None
        self.cost_explorer_client = None
        self.cloudwatch_client = None
        self.orchestrator_function = 'finops-copilot-orchestrator-agent'
        
    def initialize_aws_clients(self):
        """Initialize AWS clients"""
        try:
            # Initialize real AWS clients for production
            self.lambda_client = boto3.client('lambda')
            self.cost_explorer_client = boto3.client('ce')
            self.cloudwatch_client = boto3.client('cloudwatch')
            st.success("AWS clients initialized successfully")
        except Exception as e:
            st.error(f"Error initializing AWS clients: {str(e)}")
            # Fall back to mock mode
            self.lambda_client = None
    
    def get_mock_cost_data(self):
        """Generate mock cost data for demonstration"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        services = ['EC2', 'S3', 'RDS', 'Lambda', 'CloudWatch']
        
        data = []
        for date in dates:
            for service in services:
                base_cost = {'EC2': 1000, 'S3': 200, 'RDS': 500, 'Lambda': 50, 'CloudWatch': 30}[service]
            # Add some randomness
            cost = base_cost + (base_cost * 0.2 * (hash(str(date) + service) % 100 - 50) / 100)
            data.append({
                'Date': date,
                'Service': service,
                'Cost': max(0, cost),
                'Environment': ['Production', 'Development', 'Staging'][hash(str(date) + service) % 3]
            })
        
        return pd.DataFrame(data)
    
    def get_mock_recommendations(self):
        """Generate mock cost optimization recommendations"""
        return [
            {
                'title': 'Right-size EC2 Instances',
                'description': 'Identified 15 over-provisioned EC2 instances in production environment',
                'potential_savings': '$2,400/month',
                'priority': 'High',
                'agent': 'EC2 Agent',
                'tags': ['Environment:Production', 'Team:Backend']
            },
            {
                'title': 'Optimize S3 Storage Classes',
                'description': 'Move 500GB of infrequently accessed data to S3 Intelligent-Tiering',
                'potential_savings': '$180/month',
                'priority': 'Medium',
                'agent': 'S3 Agent',
                'tags': ['Environment:All', 'Team:Data']
            },
            {
                'title': 'Purchase Reserved Instances',
                'description': 'Commit to 1-year Reserved Instances for consistent workloads',
                'potential_savings': '$3,600/year',
                'priority': 'High',
                'agent': 'RI/SP Agent',
                'tags': ['Environment:Production']
            },
            {
                'title': 'Remove Unused RDS Instances',
                'description': 'Found 3 RDS instances with no connections in the last 30 days',
                'potential_savings': '$800/month',
                'priority': 'High',
                'agent': 'RDS Agent',
                'tags': ['Environment:Development']
            }
        ]
    
    def invoke_orchestrator_agent(self, query, days=30, depth='standard'):
        """Invoke the orchestrator Lambda function"""
        try:
            if self.lambda_client:
                # Real AWS Lambda invocation
                payload = {
                    'query': query,
                    'days': days,
                    'depth': depth
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=self.orchestrator_function,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    return {
                        'response': body.get('natural_response', 'Analysis completed'),
                        'agents_involved': body.get('detailed_analysis', {}).get('agents_consulted', []),
                        'data_sources': ['Cost Explorer', 'CloudWatch Metrics', 'Apptio'],
                        'confidence': 0.9,
                        'detailed_analysis': body.get('detailed_analysis', {}),
                        'apptio_insights': body.get('detailed_analysis', {}).get('apptio_insights', {}),
                        'recommendations': body.get('detailed_analysis', {}).get('recommendations', [])
                    }
                else:
                    return {'error': 'Failed to get response from orchestrator'}
            else:
                # Mock response for demo mode
                return self.simulate_agent_interaction(query)
                
        except Exception as e:
            st.error(f"Error invoking orchestrator: {str(e)}")
            return self.simulate_agent_interaction(query)
    
    def simulate_agent_interaction(self, query):
        """Simulate interaction with AWS Bedrock agents (fallback/demo mode)"""
        # Enhanced mock response based on query keywords
        if 'cost' in query.lower():
            return {
                'response': f"Based on your AWS cost analysis, I've identified several optimization opportunities. Your current monthly spend is approximately $15,000 across all services. The EC2 Agent found 15 over-provisioned instances, while the S3 Agent identified storage optimization opportunities worth $180/month. Apptio analysis shows your cloud spend is 12% over budget this quarter.",
                'agents_involved': ['Orchestrator Agent', 'EC2 Agent', 'S3 Agent', 'Apptio Integration'],
                'data_sources': ['Cost Explorer', 'CloudWatch Metrics', 'Apptio'],
                'confidence': 0.92,
                'apptio_insights': {
                    'budget_variance': '+12%',
                    'forecast_accuracy': 'High',
                    'cost_allocation_gaps': '23% untagged resources'
                },
                'recommendations': self.get_mock_recommendations()[:3]
            }
        elif 'ec2' in query.lower():
            return {
                'response': f"The EC2 Agent has analyzed your instances and found significant right-sizing opportunities. 15 instances are running at less than 20% CPU utilization and can be downsized, potentially saving $2,400/month.",
                'agents_involved': ['EC2 Agent'],
                'data_sources': ['CloudWatch Metrics', 'Cost Explorer'],
                'confidence': 0.88,
                'recommendations': [r for r in self.get_mock_recommendations() if 'EC2' in r['title']]
            }
        else:
            return {
                'response': f"I've analyzed your query and coordinated with the relevant agents. Based on current data, I recommend reviewing your resource utilization patterns and considering the optimization suggestions in the dashboard.",
                'agents_involved': ['Orchestrator Agent'],
                'data_sources': ['Multiple AWS Services'],
                'confidence': 0.75,
                'recommendations': []
            }

def main():
    st.markdown('<h1 class="main-header">🤖 FinOps Copilot</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered AWS Cost Optimization with Multi-Agent Intelligence</p>', unsafe_allow_html=True)
    
    # Initialize the copilot
    copilot = FinOpsCopilot()
    copilot.initialize_aws_clients()
    
    # Sidebar for navigation and agent status
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Agent Status
        st.subheader("Agent Status")
        agents = [
            ("Orchestrator Agent", "active"),
            ("EC2 Agent", "active"),
            ("S3 Agent", "active"),
            ("RDS Agent", "idle"),
            ("RI/SP Agent", "active"),
            ("Tagging Agent", "idle"),
            ("Apptio Integration", "active")
        ]
        
        for agent, status in agents:
            status_class = "status-active" if status == "active" else "status-idle"
            st.markdown(f'<div class="agent-status"><span class="{status_class}">●</span> {agent}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Filters
        st.subheader("Filters")
        environment_filter = st.selectbox("Environment", ["All", "Production", "Development", "Staging"])
        date_range = st.date_input("Date Range", value=[datetime.now() - timedelta(days=30), datetime.now()])
        
        st.divider()
        
        # Quick Actions
        st.subheader("Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        if st.button("📊 Generate Report", use_container_width=True):
            st.success("Report generation initiated!")
        if st.button("⚡ Run Optimization", use_container_width=True):
            st.info("Optimization analysis started...")
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Chat with Agents", "📋 Recommendations", "🏷️ Tag Analysis"])
    
    with tab1:
        st.header("Cost Analysis Dashboard")
        
        # Get mock data
        cost_data = copilot.get_mock_cost_data()
        
        # Filter data based on sidebar selections
        if environment_filter != "All":
            cost_data = cost_data[cost_data['Environment'] == environment_filter]
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_cost = cost_data['Cost'].sum()
        avg_daily_cost = cost_data.groupby('Date')['Cost'].sum().mean()
        top_service = cost_data.groupby('Service')['Cost'].sum().idxmax()
        cost_trend = "📈 +5.2%" if total_cost > 100000 else "📉 -2.1%"
        
        with col1:
            st.markdown(f'<div class="metric-card"><h3>${total_cost:,.0f}</h3><p>Total Cost (YTD)</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><h3>${avg_daily_cost:,.0f}</h3><p>Avg Daily Cost</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><h3>{top_service}</h3><p>Top Service</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><h3>{cost_trend}</h3><p>Monthly Trend</p></div>', unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cost Trend by Service")
            daily_costs = cost_data.groupby(['Date', 'Service'])['Cost'].sum().reset_index()
            fig = px.line(daily_costs, x='Date', y='Cost', color='Service', 
                         title="Daily Cost Trends")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Cost Distribution by Service")
            service_costs = cost_data.groupby('Service')['Cost'].sum().reset_index()
            fig = px.pie(service_costs, values='Cost', names='Service', 
                        title="Service Cost Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        # Environment breakdown
        st.subheader("Cost by Environment")
        env_costs = cost_data.groupby(['Environment', 'Service'])['Cost'].sum().reset_index()
        fig = px.bar(env_costs, x='Environment', y='Cost', color='Service',
                    title="Cost Breakdown by Environment")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("💬 Chat with FinOps Agents")
        st.markdown("Ask questions about your AWS costs and get insights from our AI agents.")
        
        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I'm your FinOps Copilot. I can help you analyze AWS costs, identify optimization opportunities, and provide actionable recommendations. What would you like to know?"}
            ]
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        prompt = st.chat_input("Ask about your AWS costs...")
        if prompt:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Consulting with agents..."):
                    response_data = copilot.invoke_orchestrator_agent(prompt)
                    
                    # Display response
                    st.markdown(response_data.get("response", "I'm processing your request..."))
                    
                    # Show agent details
                    with st.expander("Agent Details"):
                        st.write("**Agents Involved:**", ", ".join(response_data.get("agents_involved", [])))
                        st.write("**Data Sources:**", ", ".join(response_data.get("data_sources", [])))
                        st.write("**Confidence:**", f"{response_data.get('confidence', 0):.1%}")
                    
                    # Show Apptio insights if available
                    if response_data.get("apptio_insights"):
                        with st.expander("Apptio Insights"):
                            insights = response_data["apptio_insights"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Budget Variance", insights.get('budget_variance', 'N/A'))
                            with col2:
                                st.metric("Forecast Accuracy", insights.get('forecast_accuracy', 'N/A'))
                            with col3:
                                st.metric("Untagged Resources", insights.get('cost_allocation_gaps', 'N/A'))
                    
                    # Show inline recommendations if available
                    if response_data.get("recommendations"):
                        with st.expander("Quick Recommendations"):
                            for rec in response_data["recommendations"][:3]:
                                st.write(f"• **{rec.get('recommendation', rec.get('title', 'N/A'))}**")
                                if rec.get('estimated_monthly_savings'):
                                    st.write(f"  Potential savings: ${rec['estimated_monthly_savings']:.2f}/month")
                    
                    # Add to session state
                    st.session_state.messages.append({"role": "assistant", "content": response_data.get("response", "")})
    
    with tab3:
        st.header("📋 Cost Optimization Recommendations")
        
        recommendations = copilot.get_mock_recommendations()
        
        # Priority filter
        priority_filter = st.selectbox("Filter by Priority", ["All", "High", "Medium", "Low"])
        
        filtered_recs = recommendations
        if priority_filter != "All":
            filtered_recs = [r for r in recommendations if r['priority'] == priority_filter]
        
        # Display recommendations
        for i, rec in enumerate(filtered_recs):
            priority_color = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}[rec['priority']]
            
            st.markdown(f"""
            <div class="recommendation-card">
                <h4 style="color: {priority_color};">🎯 {rec['title']}</h4>
                <p><strong>Description:</strong> {rec['description']}</p>
                <p><strong>Potential Savings:</strong> {rec['potential_savings']}</p>
                <p><strong>Priority:</strong> <span style="color: {priority_color};">{rec['priority']}</span></p>
                <p><strong>Analyzed by:</strong> {rec['agent']}</p>
                <p><strong>Tags:</strong> {', '.join(rec['tags'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"✅ Implement", key=f"implement_{i}"):
                    st.success(f"Implementation initiated for: {rec['title']}")
            with col2:
                if st.button(f"📋 More Details", key=f"details_{i}"):
                    st.info(f"Detailed analysis for: {rec['title']}")
            with col3:
                if st.button(f"⏰ Schedule", key=f"schedule_{i}"):
                    st.info(f"Scheduled for review: {rec['title']}")
    
    with tab4:
        st.header("🏷️ Tag Analysis & Compliance")
        
        # Mock tag compliance data
        tag_data = {
            'Resource Type': ['EC2', 'S3', 'RDS', 'Lambda'],
            'Total Resources': [150, 45, 12, 89],
            'Tagged Resources': [120, 45, 10, 75],
            'Compliance %': [80, 100, 83, 84]
        }
        
        df_tags = pd.DataFrame(tag_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Tag Compliance by Service")
            fig = px.bar(df_tags, x='Resource Type', y='Compliance %',
                        title="Tagging Compliance Percentage")
            fig.add_hline(y=90, line_dash="dash", line_color="red", 
                         annotation_text="Target: 90%")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Compliance Summary")
            for _, row in df_tags.iterrows():
                compliance = row['Compliance %']
                color = "#28a745" if compliance >= 90 else "#ffc107" if compliance >= 80 else "#dc3545"
                st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.5rem 0; border-left: 4px solid {color}; background-color: #f8f9fa;">
                    <strong>{row['Resource Type']}</strong><br>
                    {row['Tagged Resources']}/{row['Total Resources']} resources tagged ({compliance}%)
                </div>
                """, unsafe_allow_html=True)
        
        # Tag recommendations
        st.subheader("Tagging Recommendations")
        st.markdown("""
        - **EC2 Instances**: 30 instances missing required tags (Environment, Owner, Project)
        - **RDS Databases**: 2 databases need cost center tags
        - **Lambda Functions**: 14 functions missing team ownership tags
        """)

if __name__ == "__main__":
    main()
