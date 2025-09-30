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

# Initialize AWS clients
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
lambda_client = boto3.client('lambda')
bedrock_runtime = boto3.client('bedrock-agent-runtime')
sts = boto3.client('sts')

# Get account info
account_id = sts.get_caller_identity()['Account']

# Check if running in Streamlit
try:
    st.set_page_config(page_title="AI FinOps Dashboard with Chatbot", page_icon="💰", layout="wide")
    
    # Initialize session state for chat
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'cost_data_cache' not in st.session_state:
        st.session_state.cost_data_cache = None
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
except:
    # Not running in Streamlit context (e.g., being imported for testing)
    pass

# Load configuration
try:
    with open('finops_config.json', 'r') as f:
        config = json.load(f)
    AGENT_ID = config['agents'][0]['agent_id']
    AGENT_ALIAS = config['agents'][0]['alias_id']
except:
    AGENT_ID = None
    AGENT_ALIAS = None

st.title("🚀 AI-Powered FinOps Dashboard with Chatbot")
st.markdown("Real-time AWS cost analysis with integrated AI assistant")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    days = st.slider("Analysis Period (days)", 1, 90, 7)
    
    st.header("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.session_state.cost_data_cache = None
        st.rerun()
    
    # Chat mode toggle
    chat_mode = st.checkbox("Enhanced Chat Mode", value=False)
    
    st.markdown("---")
    st.markdown("### System Status")
    
    # Check components
    try:
        lambda_resp = lambda_client.get_function(FunctionName='finops-cost-analysis')
        st.success("✓ Lambda: Active")
    except:
        st.error("✗ Lambda: Not found")
    
    if AGENT_ID:
        st.success("✓ Bedrock Agent: Configured")
    else:
        st.warning("⚠️ Bedrock Agent: Not configured")
    
    # Account info
    st.markdown("### Account Info")
    st.info(f"Account ID: {account_id}")
    
    # Export options
    st.markdown("### Export Options")
    export_format = st.selectbox("Export Format", ["None", "CSV", "JSON", "PDF Summary"])

# Make cache decorator optional for testing
try:
    cache_decorator = st.cache_data(ttl=300)
except:
    # If not in Streamlit context, create a no-op decorator
    def cache_decorator(func):
        return func

# Cache data fetching functions
@cache_decorator
def get_cost_data(days):
    """Fetch cost data from AWS Cost Explorer"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        return response
    except Exception as e:
        st.error(f"Error fetching cost data: {e}")
        return None

@cache_decorator
def get_ec2_utilization():
    """Get EC2 instance utilization"""
    instances = []
    try:
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                # Get tags
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                
                # Get CPU utilization
                end = datetime.now()
                start = end - timedelta(days=7)
                
                cpu_response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=3600,
                    Statistics=['Average', 'Maximum']
                )
                
                cpu_data = cpu_response.get('Datapoints', [])
                avg_cpu = sum(d['Average'] for d in cpu_data) / len(cpu_data) if cpu_data else 0
                max_cpu = max((d['Maximum'] for d in cpu_data), default=0)
                
                instances.append({
                    'InstanceId': instance_id,
                    'InstanceType': instance_type,
                    'Name': tags.get('Name', 'N/A'),
                    'Environment': tags.get('Environment', 'N/A'),
                    'AvgCPU': round(avg_cpu, 2),
                    'MaxCPU': round(max_cpu, 2),
                    'State': instance['State']['Name']
                })
        
        return instances
    except Exception as e:
        st.error(f"Error getting EC2 data: {e}")
        return []

def get_cost_anomalies(days=30):
    """Detect cost anomalies"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        daily_costs = []
        for result in response['ResultsByTime']:
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append({
                'date': result['TimePeriod']['Start'],
                'cost': cost
            })
        
        # Simple anomaly detection
        df = pd.DataFrame(daily_costs)
        df['cost_avg'] = df['cost'].rolling(window=7, min_periods=1).mean()
        df['deviation'] = (df['cost'] - df['cost_avg']) / df['cost_avg'] * 100
        
        anomalies = df[abs(df['deviation']) > 20].to_dict('records')
        
        return anomalies
    except Exception as e:
        return []

def query_bedrock_agent(prompt):
    """Query Bedrock agent for AI insights"""
    if not AGENT_ID or not AGENT_ALIAS:
        return "Bedrock agent not configured. Using fallback analysis."
    
    try:
        session_id = f"chat-{uuid.uuid4()}"
        
        response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS,
            sessionId=session_id,
            inputText=prompt
        )
        
        result = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result += chunk['bytes'].decode('utf-8')
        
        return result
    except Exception as e:
        return f"Error querying Bedrock agent: {str(e)}"

def invoke_lambda_for_analysis(function_name, days):
    """Invoke Lambda function for cost analysis"""
    try:
        payload = {
            'apiPath': '/getCostBreakdown',
            'parameters': [{'name': 'days', 'value': str(days)}],
            'actionGroup': 'dashboard',
            'httpMethod': 'POST'
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if 'response' in result and 'responseBody' in result['response']:
            body = result['response']['responseBody']['application/json']['body']
            return json.loads(body)
        
        return None
    except Exception as e:
        st.error(f"Lambda invocation error: {e}")
        return None

def generate_insights(cost_data, ec2_data):
    """Generate AI-powered insights from data"""
    insights = []
    
    if cost_data:
        # Process cost data for insights
        total_cost = sum(
            float(group['Metrics']['UnblendedCost']['Amount'])
            for result in cost_data['ResultsByTime']
            for group in result['Groups']
        )
        
        # Top services
        service_costs = {}
        for result in cost_data['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                service_costs[service] = service_costs.get(service, 0) + cost
        
        top_service = max(service_costs.items(), key=lambda x: x[1])[0] if service_costs else "Unknown"
        
        insights.append(f"💰 Your total AWS spend for the selected period is ${total_cost:.2f}")
        insights.append(f"📊 {top_service} is your highest cost service")
    
    if ec2_data:
        low_util = sum(1 for i in ec2_data if i['AvgCPU'] < 10)
        if low_util > 0:
            insights.append(f"⚠️ {low_util} EC2 instances have <10% CPU utilization - consider rightsizing")
    
    # Check for anomalies
    anomalies = get_cost_anomalies()
    if anomalies:
        insights.append(f"🚨 {len(anomalies)} cost anomalies detected in the last 30 days")
    
    return insights

# Main app layout with tabs
if chat_mode:
    # Enhanced chat mode with tabs
    tab1, tab2 = st.tabs(["💬 AI Chat", "📊 Live Dashboard"])
    
    with tab1:
        st.header("AI FinOps Assistant")
        st.markdown("Ask me anything about your AWS costs, optimization opportunities, or trends.")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    st.markdown(f"**🧑 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 Assistant:** {message['content']}")
                st.markdown("")
        
        # Chat input
        prompt = st.text_input("Ask about your AWS costs...", key="chat_input_enhanced", 
                             placeholder="e.g., What are my top costs? How can I save money?")
            
        if prompt:
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            # Generate response
            with st.spinner("🤖 Analyzing..."):
                # Get current data context
                cost_data = get_cost_data(days)
                ec2_data = get_ec2_utilization()
                
                # Build context for the query
                context = f"""
                Current AWS cost data for {days} days:
                - Total cost data available
                - EC2 instances: {len(ec2_data)}
                - Time period: Last {days} days
                
                User query: {prompt}
                """
                
                # Try Bedrock first, then Lambda, then fallback
                response = query_bedrock_agent(context)
                
                if "Error" in response or "not configured" in response:
                    # Try Lambda analysis
                    lambda_result = invoke_lambda_for_analysis('finops-cost-analysis', days)
                    if lambda_result:
                        response = f"Based on AWS Cost Explorer data:\n"
                        response += f"- Total cost: ${lambda_result.get('total_cost', 0):.2f}\n"
                        response += f"- Period: {lambda_result.get('period', 'N/A')}\n"
                        
                        if 'cost_by_service' in lambda_result:
                            response += "\nTop services by cost:\n"
                            for service, cost in list(lambda_result['cost_by_service'].items())[:5]:
                                response += f"- {service}: ${cost:.2f}\n"
                    else:
                        # Fallback to basic insights
                        insights = generate_insights(cost_data, ec2_data)
                        response = "Here are your FinOps insights:\n\n" + "\n".join(insights)
                
                # Add response to chat history
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                
                # Display the response
                with chat_container:
                    st.markdown(f"**🤖 Assistant:** {response}")
    
    with tab2:
        st.header("Live Cost Dashboard")
        
        # Refresh button
        if st.button("🔄 Refresh Data", key="refresh_live_dashboard"):
            st.experimental_rerun()
        
        # Get fresh data
        cost_data = get_cost_data(days)
        
        if cost_data:
            # Process data
            costs_by_service = {}
            daily_costs = []
            
            for result in cost_data['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_total = 0
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    costs_by_service[service] = costs_by_service.get(service, 0) + cost
                    daily_total += cost
                
                daily_costs.append({'date': date, 'cost': daily_total})
            
            total_cost = sum(costs_by_service.values())
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cost", f"${total_cost:,.2f}")
            with col2:
                st.metric("Daily Average", f"${total_cost/days if days > 0 else 0:,.2f}")
            with col3:
                st.metric("Services", len(costs_by_service))
            with col4:
                st.metric("Period", f"{days} days")
            
            # Charts section
            st.markdown("### Cost Breakdown")
            
            # Service breakdown
            top_services = sorted(costs_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
            df_services = pd.DataFrame(top_services, columns=['Service', 'Cost'])
            
            fig = px.bar(df_services, x='Cost', y='Service', orientation='h',
                        title="Top 10 Services by Cost", color='Cost',
                        color_continuous_scale='Blues')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily trend
            st.markdown("### Daily Cost Trend")
            df_daily = pd.DataFrame(daily_costs)
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
            fig_trend = px.line(df_daily, x='date', y='cost', 
                              title=f"Daily Costs - Last {days} Days",
                              markers=True)
            fig_trend.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Cost ($)"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Cost table
            st.markdown("### Detailed Service Costs")
            all_services = sorted(costs_by_service.items(), key=lambda x: x[1], reverse=True)
            df_all = pd.DataFrame(all_services, columns=['Service', 'Cost'])
            df_all['Cost'] = df_all['Cost'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_all, use_container_width=True, height=400)
        
        else:
            st.error("Unable to fetch cost data. Please check your AWS credentials and permissions.")

else:
    # Regular dashboard mode
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Cost Overview", 
        "📈 Trends", 
        "🖥️ EC2 Analysis", 
        "💡 Optimizations",
        "🤖 AI Chat",
        "🧪 Test System"
    ])
    
    with tab1:
        st.header("Cost Overview")
        
        cost_data = get_cost_data(days)
        
        if cost_data:
            # Process data
            costs_by_service = {}
            daily_costs = []
            
            for result in cost_data['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_total = 0
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    costs_by_service[service] = costs_by_service.get(service, 0) + cost
                    daily_total += cost
                
                daily_costs.append({'date': date, 'cost': daily_total})
            
            total_cost = sum(costs_by_service.values())
            
            # Store in session state for chatbot
            st.session_state.cost_data_cache = {
                'total_cost': total_cost,
                'costs_by_service': costs_by_service,
                'daily_costs': daily_costs,
                'days': days
            }
            st.session_state.last_refresh = datetime.now()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Total Cost", f"${total_cost:,.2f}", f"Last {days} days")
            col2.metric("Daily Average", f"${total_cost/days if days > 0 else 0:,.2f}")
            col3.metric("Services Used", len(costs_by_service))
            
            # Calculate trend
            if len(daily_costs) > 1:
                last_day = daily_costs[-1]['cost']
                first_day = daily_costs[0]['cost']
                trend = ((last_day - first_day) / first_day * 100) if first_day > 0 else 0
                col4.metric("Trend", f"{trend:+.1f}%", "vs first day")
            
            # Service breakdown
            st.subheader("Cost by Service")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart
                top_services = sorted(costs_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
                df_services = pd.DataFrame(top_services, columns=['Service', 'Cost'])
                
                fig = px.bar(df_services, x='Cost', y='Service', orientation='h',
                             title=f"Top 10 Services by Cost (${total_cost:,.2f} total)",
                             text='Cost')
                fig.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pie chart
                fig_pie = px.pie(df_services, values='Cost', names='Service',
                                title="Cost Distribution")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Daily trend
            st.subheader("Daily Cost Trend")
            df_daily = pd.DataFrame(daily_costs)
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
            fig_trend = px.line(df_daily, x='date', y='cost',
                               title=f"Daily Costs - {days} Day Period",
                               markers=True)
            fig_trend.update_traces(mode='lines+markers')
            fig_trend.update_layout(hovermode='x unified')
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # AI Insights
            st.subheader("🤖 AI-Generated Insights")
            with st.spinner("Generating insights..."):
                ec2_data = get_ec2_utilization()
                insights = generate_insights(cost_data, ec2_data)
                
                for insight in insights:
                    st.info(insight)
    
    with tab2:
        st.header("Cost Trends & Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            trend_days = st.selectbox("Trend Period", [7, 14, 30, 60, 90], index=2)
        
        with col2:
            granularity = st.selectbox("Granularity", ["DAILY", "WEEKLY", "MONTHLY"])
        
        if st.button("Analyze Trends"):
            with st.spinner("Analyzing trends..."):
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=trend_days)
                
                try:
                    response = ce.get_cost_and_usage(
                        TimePeriod={
                            'Start': start_date.strftime('%Y-%m-%d'),
                            'End': end_date.strftime('%Y-%m-%d')
                        },
                        Granularity=granularity,
                        Metrics=['UnblendedCost'],
                        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                    )
                    
                    # Process data for trend analysis
                    service_trends = {}
                    dates = []
                    
                    for result in response['ResultsByTime']:
                        date = result['TimePeriod']['Start']
                        dates.append(date)
                        
                        for group in result['Groups']:
                            service = group['Keys'][0]
                            cost = float(group['Metrics']['UnblendedCost']['Amount'])
                            
                            if service not in service_trends:
                                service_trends[service] = []
                            service_trends[service].append(cost)
                    
                    # Create trend visualization
                    fig = go.Figure()
                    
                    # Add top 5 services
                    top_services = sorted(
                        [(s, sum(costs)) for s, costs in service_trends.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    
                    for service, _ in top_services:
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=service_trends[service],
                            name=service,
                            mode='lines+markers'
                        ))
                    
                    fig.update_layout(
                        title=f"Cost Trends by Service ({granularity})",
                        xaxis_title="Date",
                        yaxis_title="Cost ($)",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Anomaly Detection
                    st.subheader("🚨 Cost Anomalies")
                    anomalies = get_cost_anomalies(trend_days)
                    
                    if anomalies:
                        df_anomalies = pd.DataFrame(anomalies)
                        st.dataframe(df_anomalies)
                    else:
                        st.success("No significant cost anomalies detected!")
                    
                except Exception as e:
                    st.error(f"Error analyzing trends: {e}")
    
    with tab3:
        st.header("EC2 Instance Analysis")
        
        instances = get_ec2_utilization()
        
        if instances:
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            total_instances = len(instances)
            low_util = sum(1 for i in instances if i['AvgCPU'] < 10)
            medium_util = sum(1 for i in instances if 10 <= i['AvgCPU'] < 50)
            
            col1.metric("Total Running Instances", total_instances)
            col2.metric("Low Utilization (<10%)", low_util, "Consider downsizing" if low_util > 0 else "")
            col3.metric("Medium Utilization (10-50%)", medium_util)
            
            # Instance details
            st.subheader("Instance Utilization Details")
            
            df_instances = pd.DataFrame(instances)
            
            # Add utilization category
            def categorize_utilization(cpu):
                if cpu < 10:
                    return "🔴 Low"
                elif cpu < 50:
                    return "🟡 Medium"
                else:
                    return "🟢 High"
            
            df_instances['Utilization'] = df_instances['AvgCPU'].apply(categorize_utilization)
            
            # Display with conditional formatting
            st.dataframe(
                df_instances[['InstanceId', 'Name', 'InstanceType', 'Environment', 
                             'AvgCPU', 'MaxCPU', 'Utilization']],
                use_container_width=True,
                hide_index=True
            )
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = px.histogram(df_instances, x='AvgCPU', nbins=20,
                                       title="CPU Utilization Distribution",
                                       labels={'AvgCPU': 'Average CPU %', 'count': 'Instance Count'})
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Instance type distribution
                type_counts = df_instances['InstanceType'].value_counts()
                fig_types = px.pie(values=type_counts.values, names=type_counts.index,
                                  title="Instance Type Distribution")
                st.plotly_chart(fig_types, use_container_width=True)
            
            # Recommendations
            st.subheader("💡 EC2 Optimization Recommendations")
            
            if low_util > 0:
                st.warning(f"""
                **{low_util} instances with <10% CPU utilization detected:**
                - Consider terminating or stopping idle instances
                - Downsize to smaller instance types
                - Use Auto Scaling to match capacity with demand
                """)
            
            # Calculate potential savings
            instance_costs = {
                't2.micro': 8.5, 't2.small': 17, 't2.medium': 34,
                't3.micro': 7.6, 't3.small': 15.2, 't3.medium': 30.4,
                't3.large': 60.8, 't3.xlarge': 121.6,
                'm5.large': 70, 'm5.xlarge': 140, 'm5.2xlarge': 280
            }
            
            potential_savings = 0
            for instance in instances:
                if instance['AvgCPU'] < 10:
                    instance_type = instance['InstanceType']
                    monthly_cost = instance_costs.get(instance_type, 50)
                    potential_savings += monthly_cost
            
            if potential_savings > 0:
                st.info(f"💰 Potential monthly savings from rightsizing: ${potential_savings:,.2f}")
        
        else:
            st.info("No running EC2 instances found or unable to fetch data.")
    
    with tab4:
        st.header("Cost Optimization Recommendations")
        
        st.markdown("""
        ### AI-Powered Recommendations
        Based on your AWS usage patterns, here are optimization strategies:
        """)
        
        # Get current cost data for recommendations
        cost_data = get_cost_data(30)
        
        if cost_data:
            total_30d = sum(
                float(group['Metrics']['UnblendedCost']['Amount'])
                for result in cost_data['ResultsByTime']
                for group in result['Groups']
            )
            
            monthly_estimate = total_30d
            
            # Generate recommendations using Lambda or AI
            with st.spinner("Generating AI recommendations..."):
                # Try Lambda function
                lambda_result = invoke_lambda_for_analysis('finops-cost-analysis', 30)
                
                if lambda_result:
                    st.success("Generated recommendations based on your actual AWS data:")
                    
                    # Display Lambda results
                    if 'total_cost' in lambda_result:
                        st.metric("30-Day Cost", f"${lambda_result['total_cost']:.2f}")
                
                # Generate recommendations
                recommendations = []
                
                # EC2 recommendations
                instances = get_ec2_utilization()
                if instances:
                    low_util_count = sum(1 for i in instances if i['AvgCPU'] < 10)
                    if low_util_count > 0:
                        recommendations.append({
                            'Category': 'EC2 Right-sizing',
                            'Action': f'Optimize {low_util_count} underutilized instances',
                            'Potential Savings': '15-30%',
                            'Priority': 'High',
                            'Effort': 'Low'
                        })
                
                # Reserved Instances
                recommendations.append({
                    'Category': 'Reserved Instances',
                    'Action': 'Purchase RIs for stable workloads',
                    'Potential Savings': 'Up to 72%',
                    'Priority': 'High',
                    'Effort': 'Medium'
                })
                
                # Spot Instances
                recommendations.append({
                    'Category': 'Spot Instances',
                    'Action': 'Use Spot for fault-tolerant workloads',
                    'Potential Savings': 'Up to 90%',
                    'Priority': 'Medium',
                    'Effort': 'High'
                })
                
                # Storage optimization
                recommendations.append({
                    'Category': 'Storage Optimization',
                    'Action': 'Move infrequent data to Glacier',
                    'Potential Savings': '10-20%',
                    'Priority': 'Medium',
                    'Effort': 'Low'
                })
                
                # Untagged resources
                recommendations.append({
                    'Category': 'Resource Tagging',
                    'Action': 'Tag all resources for better cost allocation',
                    'Potential Savings': 'Better visibility',
                    'Priority': 'High',
                    'Effort': 'Low'
                })
                
                # Display recommendations
                df_recs = pd.DataFrame(recommendations)
                
                st.dataframe(df_recs, use_container_width=True, hide_index=True)
                
                # Savings calculator
                st.subheader("💰 Savings Calculator")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    ri_percentage = st.slider("RI Coverage %", 0, 100, 30)
                
                with col2:
                    rightsizing_savings = st.slider("Rightsizing Savings %", 0, 50, 15)
                
                with col3:
                    spot_percentage = st.slider("Spot Usage %", 0, 50, 10)
                
                # Calculate potential savings
                ri_savings = monthly_estimate * (ri_percentage / 100) * 0.5
                rs_savings = monthly_estimate * (rightsizing_savings / 100)
                spot_savings = monthly_estimate * (spot_percentage / 100) * 0.7
                
                total_savings = ri_savings + rs_savings + spot_savings
                new_monthly = monthly_estimate - total_savings
                
                # Display savings
                st.markdown("### Projected Savings")
                
                col1, col2, col3 = st.columns(3)
                
                col1.metric("Current Monthly Cost", f"${monthly_estimate:,.2f}")
                col2.metric("Potential Savings", f"${total_savings:,.2f}", f"-{(total_savings/monthly_estimate*100):.1f}%")
                col3.metric("New Monthly Cost", f"${new_monthly:,.2f}")
                
                # Savings breakdown
                fig_savings = go.Figure(go.Waterfall(
                    name="Savings",
                    orientation="v",
                    x=["Current Cost", "RI Savings", "Rightsizing", "Spot Instances", "Optimized Cost"],
                    y=[monthly_estimate, -ri_savings, -rs_savings, -spot_savings, new_monthly],
                    text=[f"${monthly_estimate:,.0f}", f"-${ri_savings:,.0f}", f"-${rs_savings:,.0f}", 
                          f"-${spot_savings:,.0f}", f"${new_monthly:,.0f}"],
                    textposition="outside",
                    connector={"line": {"color": "rgb(63, 63, 63)"}}
                ))
                
                fig_savings.update_layout(
                    title="Monthly Cost Optimization Waterfall",
                    showlegend=False
                )
                
                st.plotly_chart(fig_savings, use_container_width=True)
    
    with tab5:
        st.header("🤖 AI FinOps Assistant")
        st.markdown("Chat with your AI assistant about AWS costs and optimizations")
        
        # Quick suggestions
        st.markdown("### 💡 Quick Questions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("What are my top costs?"):
                st.session_state.chat_messages.append({"role": "user", "content": "What are my top AWS costs?"})
        
        with col2:
            if st.button("How can I save money?"):
                st.session_state.chat_messages.append({"role": "user", "content": "How can I reduce my AWS costs?"})
        
        with col3:
            if st.button("Show cost trends"):
                st.session_state.chat_messages.append({"role": "user", "content": "Show me my cost trends"})
        
        st.markdown("---")
        
        # Chat interface
        chat_container = st.container()
        
        # Display chat history
        with chat_container:
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    st.markdown(f"**🧑 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 Assistant:** {message['content']}")
        
        # Chat input
        prompt = st.text_input("Ask me about your AWS costs...", key="ai_insights_chat_input")
        if prompt:
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            # Generate response
            with st.spinner("Thinking..."):
                    # Use cached data if available
                    if st.session_state.cost_data_cache:
                        cache_data = st.session_state.cost_data_cache
                        
                        # Build context
                        context = f"""
                        Based on the dashboard data:
                        - Total cost (last {cache_data['days']} days): ${cache_data['total_cost']:.2f}
                        - Number of services: {len(cache_data['costs_by_service'])}
                        - Top service: {max(cache_data['costs_by_service'].items(), key=lambda x: x[1])[0] if cache_data['costs_by_service'] else 'Unknown'}
                        
                        User question: {prompt}
                        """
                        
                        # Try AI response
                        response = query_bedrock_agent(context)
                        
                        if "Error" in response or "not configured" in response:
                            # Fallback to rule-based responses
                            if "top" in prompt.lower() and "cost" in prompt.lower():
                                top_5 = sorted(cache_data['costs_by_service'].items(), 
                                             key=lambda x: x[1], reverse=True)[:5]
                                response = "Here are your top 5 AWS services by cost:\n\n"
                                for i, (service, cost) in enumerate(top_5, 1):
                                    response += f"{i}. {service}: ${cost:.2f}\n"
                            
                            elif "save" in prompt.lower() or "reduce" in prompt.lower():
                                response = """Based on your usage patterns, here are ways to save:

1. **Right-size EC2 instances** - Review instances with low CPU utilization
2. **Use Reserved Instances** - For predictable workloads, save up to 72%
3. **Enable S3 lifecycle policies** - Move old data to cheaper storage classes
4. **Review unused resources** - Check for unattached EBS volumes and idle load balancers
5. **Set up budget alerts** - Prevent unexpected cost spikes

Would you like me to analyze any specific service?"""
                            
                            elif "trend" in prompt.lower():
                                if len(cache_data['daily_costs']) > 1:
                                    first = cache_data['daily_costs'][0]['cost']
                                    last = cache_data['daily_costs'][-1]['cost']
                                    trend = ((last - first) / first * 100) if first > 0 else 0
                                    
                                    response = f"""Cost trend analysis for the last {cache_data['days']} days:

- Starting daily cost: ${first:.2f}
- Current daily cost: ${last:.2f}
- Trend: {trend:+.1f}% {'increase' if trend > 0 else 'decrease'}
- Average daily cost: ${cache_data['total_cost'] / cache_data['days']:.2f}

The trend shows your costs are {'increasing' if trend > 0 else 'decreasing'}."""
                                else:
                                    response = "Not enough data to show trends. Try selecting a longer time period."
                            
                            else:
                                # Generic helpful response
                                response = f"""I can help you understand your AWS costs. Based on your data:

- Total cost for last {cache_data['days']} days: ${cache_data['total_cost']:.2f}
- Daily average: ${cache_data['total_cost'] / cache_data['days']:.2f}
- Number of services used: {len(cache_data['costs_by_service'])}

What specific aspect would you like to explore?"""
                    else:
                        response = "Please refresh the dashboard data first by clicking the Refresh button in the sidebar."
                    
                    # Display assistant response
                    with chat_container:
                        st.markdown(f"**🤖 Assistant:** {response}")
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    with tab6:
        st.header("🧪 System Testing")
        
        st.markdown("Test all FinOps system components")
        
        # Test sections
        test_component = st.selectbox(
            "Select Component to Test",
            ["Lambda Function", "Bedrock Agent", "Cost Explorer API", "EC2 API", "Complete System"]
        )
        
        if st.button("Run Test"):
            test_results = []
            
            if test_component in ["Lambda Function", "Complete System"]:
                with st.spinner("Testing Lambda function..."):
                    try:
                        result = invoke_lambda_for_analysis('finops-cost-analysis', 7)
                        if result and 'total_cost' in result:
                            test_results.append({
                                "Component": "Lambda Function",
                                "Status": "✅ Pass",
                                "Details": f"Retrieved cost data: ${result['total_cost']:.2f}"
                            })
                        else:
                            test_results.append({
                                "Component": "Lambda Function",
                                "Status": "❌ Fail",
                                "Details": "No cost data returned"
                            })
                    except Exception as e:
                        test_results.append({
                            "Component": "Lambda Function",
                            "Status": "❌ Fail",
                            "Details": str(e)
                        })
            
            if test_component in ["Bedrock Agent", "Complete System"]:
                with st.spinner("Testing Bedrock agent..."):
                    if AGENT_ID:
                        try:
                            response = query_bedrock_agent("Test query")
                            if response and "Error" not in response:
                                test_results.append({
                                    "Component": "Bedrock Agent",
                                    "Status": "✅ Pass",
                                    "Details": "Agent responded successfully"
                                })
                            else:
                                test_results.append({
                                    "Component": "Bedrock Agent",
                                    "Status": "⚠️ Warning",
                                    "Details": response
                                })
                        except Exception as e:
                            test_results.append({
                                "Component": "Bedrock Agent",
                                "Status": "❌ Fail",
                                "Details": str(e)
                            })
                    else:
                        test_results.append({
                            "Component": "Bedrock Agent",
                            "Status": "⚠️ Not Configured",
                            "Details": "Agent ID not found in config"
                        })
            
            if test_component in ["Cost Explorer API", "Complete System"]:
                with st.spinner("Testing Cost Explorer API..."):
                    try:
                        test_data = get_cost_data(1)
                        if test_data:
                            test_results.append({
                                "Component": "Cost Explorer API",
                                "Status": "✅ Pass",
                                "Details": "Successfully retrieved cost data"
                            })
                        else:
                            test_results.append({
                                "Component": "Cost Explorer API",
                                "Status": "❌ Fail",
                                "Details": "No data returned"
                            })
                    except Exception as e:
                        test_results.append({
                            "Component": "Cost Explorer API",
                            "Status": "❌ Fail",
                            "Details": str(e)
                        })
            
            if test_component in ["EC2 API", "Complete System"]:
                with st.spinner("Testing EC2 API..."):
                    try:
                        instances = get_ec2_utilization()
                        test_results.append({
                            "Component": "EC2 API",
                            "Status": "✅ Pass",
                            "Details": f"Found {len(instances)} EC2 instances"
                        })
                    except Exception as e:
                        test_results.append({
                            "Component": "EC2 API",
                            "Status": "❌ Fail",
                            "Details": str(e)
                        })
            
            # Display results
            if test_results:
                st.markdown("### Test Results")
                df_results = pd.DataFrame(test_results)
                
                # Style the dataframe
                def highlight_status(val):
                    if "Pass" in str(val):
                        return 'background-color: #90EE90'
                    elif "Fail" in str(val):
                        return 'background-color: #FFB6C1'
                    elif "Warning" in str(val):
                        return 'background-color: #FFFACD'
                    return ''
                
                styled_df = df_results.style.applymap(
                    highlight_status, 
                    subset=['Status']
                )
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Summary
                passed = sum(1 for r in test_results if "Pass" in r['Status'])
                failed = sum(1 for r in test_results if "Fail" in r['Status'])
                warnings = sum(1 for r in test_results if "Warning" in r['Status'])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Passed", passed)
                col2.metric("Failed", failed)
                col3.metric("Warnings", warnings)
        
        # System info
        with st.expander("System Information"):
            st.json({
                "Account ID": account_id,
                "Region": boto3.Session().region_name,
                "Bedrock Agent ID": AGENT_ID if AGENT_ID else "Not configured",
                "Lambda Function": "finops-cost-analysis",
                "Dashboard Version": "2.0 with Chatbot",
                "Last Data Refresh": st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S") if st.session_state.last_refresh else "Never"
            })

# Export functionality
if export_format != "None" and st.session_state.cost_data_cache:
    if st.button(f"Export as {export_format}"):
        cache_data = st.session_state.cost_data_cache
        
        if export_format == "CSV":
            # Create CSV
            df = pd.DataFrame([
                {"Service": k, "Cost": v} 
                for k, v in cache_data['costs_by_service'].items()
            ])
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aws_costs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        elif export_format == "JSON":
            # Create JSON
            export_data = {
                "export_date": datetime.now().isoformat(),
                "period_days": cache_data['days'],
                "total_cost": cache_data['total_cost'],
                "services": cache_data['costs_by_service'],
                "daily_costs": cache_data['daily_costs']
            }
            json_str = json.dumps(export_data, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"aws_costs_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        elif export_format == "PDF Summary":
            # For PDF, we'll create a summary text
            summary = f"""AWS Cost Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {cache_data['days']} days
Total Cost: ${cache_data['total_cost']:,.2f}
Daily Average: ${cache_data['total_cost'] / cache_data['days']:,.2f}

Top Services:
"""
            for service, cost in sorted(cache_data['costs_by_service'].items(), 
                                       key=lambda x: x[1], reverse=True)[:10]:
                summary += f"- {service}: ${cost:.2f}\n"
            
            st.download_button(
                label="Download Summary",
                data=summary,
                file_name=f"aws_cost_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🤖 **AI-Powered FinOps**")
    st.caption("Bedrock + Lambda Integration")

with col2:
    st.markdown("💬 **Interactive Chatbot**")
    st.caption("Natural Language Queries")

with col3:
    st.markdown("📊 **Real-time Analytics**")
    st.caption("Live AWS Data")