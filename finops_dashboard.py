import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-agent-runtime')
ce = boto3.client('ce')

# Agent configuration
AGENT_ID = "S8AZOE6JRP"
AGENT_ALIAS = "L9ZMELFBMS"

st.set_page_config(page_title="FinOps Dashboard", page_icon="💰", layout="wide")

st.title("🚀 AI-Powered FinOps Dashboard")
st.markdown("Real-time AWS cost analysis and optimization powered by Bedrock AI")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    days = st.slider("Analysis Period (days)", 1, 90, 7)
    
    st.header("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This dashboard uses AWS Bedrock agents to analyze costs and provide AI-powered recommendations.")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Cost Overview", "📈 Trends", "💡 AI Assistant", "🔧 Optimizations"])

with tab1:
    st.header("Cost Overview")
    
    col1, col2, col3 = st.columns(3)
    
    try:
        # Get cost data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # Process data
        costs_by_service = {}
        daily_costs = []
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total_daily = 0
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                costs_by_service[service] = costs_by_service.get(service, 0) + cost
                total_daily += cost
            
            daily_costs.append({'date': date, 'cost': total_daily})
        
        total_cost = sum(costs_by_service.values())
        
        # Display metrics
        col1.metric("Total Cost", f"${total_cost:,.2f}", f"Last {days} days")
        col2.metric("Daily Average", f"${total_cost/days:,.2f}")
        col3.metric("Services Used", len(costs_by_service))
        
        # Top services chart
        st.subheader("Top Services by Cost")
        top_services = sorted(costs_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
        
        df = pd.DataFrame(top_services, columns=['Service', 'Cost'])
        fig = px.bar(df, x='Cost', y='Service', orientation='h', 
                     title=f"Top 10 Services (Last {days} days)")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Daily costs chart
        st.subheader("Daily Cost Trend")
        df_daily = pd.DataFrame(daily_costs)
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        
        fig_daily = px.line(df_daily, x='date', y='cost', 
                           title=f"Daily Costs (Last {days} days)")
        fig_daily.update_layout(height=300)
        st.plotly_chart(fig_daily, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error fetching cost data: {e}")

with tab2:
    st.header("Cost Trends Analysis")
    
    trend_period = st.selectbox("Select Period", ["7 days", "30 days", "90 days"])
    trend_days = int(trend_period.split()[0])
    
    if st.button("Analyze Trends"):
        with st.spinner("Analyzing trends..."):
            try:
                # Call Bedrock agent
                session_id = f"trend-{datetime.now().timestamp()}"
                
                response = bedrock_runtime.invoke_agent(
                    agentId=AGENT_ID,
                    agentAliasId=AGENT_ALIAS,
                    sessionId=session_id,
                    inputText=f"Analyze my cost trends for the last {trend_days} days"
                )
                
                # Process response
                result = ""
                for event in response.get('completion', []):
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            result += chunk['bytes'].decode('utf-8')
                
                st.markdown("### AI Analysis")
                st.write(result)
                
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.header("AI FinOps Assistant")
    st.markdown("Ask me anything about your AWS costs!")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
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
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    session_id = f"chat-{datetime.now().timestamp()}"
                    
                    response = bedrock_runtime.invoke_agent(
                        agentId=AGENT_ID,
                        agentAliasId=AGENT_ALIAS,
                        sessionId=session_id,
                        inputText=prompt
                    )
                    
                    # Process response
                    result = ""
                    for event in response.get('completion', []):
                        if 'chunk' in event:
                            chunk = event['chunk']
                            if 'bytes' in chunk:
                                result += chunk['bytes'].decode('utf-8')
                    
                    st.markdown(result)
                    st.session_state.messages.append({"role": "assistant", "content": result})
                    
                except Exception as e:
                    st.error(f"Error: {e}")

with tab4:
    st.header("Cost Optimization Recommendations")
    
    if st.button("Get AI Recommendations"):
        with st.spinner("Generating recommendations..."):
            try:
                session_id = f"opt-{datetime.now().timestamp()}"
                
                response = bedrock_runtime.invoke_agent(
                    agentId=AGENT_ID,
                    agentAliasId=AGENT_ALIAS,
                    sessionId=session_id,
                    inputText="Provide detailed cost optimization recommendations based on my current spending"
                )
                
                # Process response
                result = ""
                for event in response.get('completion', []):
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            result += chunk['bytes'].decode('utf-8')
                
                st.markdown("### AI-Generated Recommendations")
                st.write(result)
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Quick tips
    st.markdown("### Quick Cost-Saving Tips")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **💡 Reserved Instances**
        - Save up to 72% on EC2
        - Best for steady workloads
        - 1 or 3 year commitments
        """)
        
        st.success("""
        **🎯 Spot Instances**
        - Save up to 90% on EC2
        - Great for batch jobs
        - Fault-tolerant workloads
        """)
    
    with col2:
        st.warning("""
        **📊 Right-sizing**
        - Match instance size to workload
        - Use CloudWatch metrics
        - Start with over-provisioned resources
        """)
        
        st.info("""
        **🗑️ Clean Up**
        - Delete unattached EBS volumes
        - Remove old snapshots
        - Terminate idle resources
        """)

# Footer
st.markdown("---")
st.markdown("🤖 Powered by AWS Bedrock AI | 💰 FinOps Dashboard v1.0")
