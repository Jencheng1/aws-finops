import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize AWS clients
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
lambda_client = boto3.client('lambda')

st.set_page_config(page_title="AI FinOps Dashboard", page_icon="💰", layout="wide")

st.title("🚀 AI-Powered FinOps Dashboard")
st.markdown("Real-time AWS cost analysis and optimization")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    days = st.slider("Analysis Period (days)", 1, 90, 7)
    
    st.header("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### System Status")
    try:
        # Check Lambda function
        lambda_resp = lambda_client.get_function(FunctionName='finops-cost-analysis')
        st.success("✓ Lambda: Active")
    except:
        st.error("✗ Lambda: Not found")
    
    # Load config
    try:
        with open('finops_config.json', 'r') as f:
            config = json.load(f)
        st.success("✓ Config: Loaded")
        
        if 'agents' in config and config['agents']:
            st.info(f"Agent ID: {config['agents'][0]['agent_id'][:10]}...")
    except:
        st.warning("Config not found")

# Cache data fetching
@st.cache_data(ttl=300)
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

@st.cache_data(ttl=600)
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
                    'AvgCPU': round(avg_cpu, 2),
                    'MaxCPU': round(max_cpu, 2),
                    'State': instance['State']['Name']
                })
        
        return instances
    except Exception as e:
        st.error(f"Error getting EC2 data: {e}")
        return []

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Cost Overview", "📈 Trends", "🖥️ EC2 Analysis", "💡 Optimizations", "🧪 Test Lambda"])

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
                
                # Trend summary
                st.subheader("Trend Summary")
                
                trend_data = []
                for service, costs in service_trends.items():
                    if len(costs) > 1:
                        start_cost = costs[0]
                        end_cost = costs[-1]
                        change = ((end_cost - start_cost) / start_cost * 100) if start_cost > 0 else 0
                        
                        trend_data.append({
                            'Service': service,
                            'Start Cost': f"${start_cost:.2f}",
                            'End Cost': f"${end_cost:.2f}",
                            'Change %': f"{change:+.1f}%",
                            'Total Cost': f"${sum(costs):.2f}"
                        })
                
                df_trends = pd.DataFrame(trend_data)
                df_trends = df_trends.sort_values('Total Cost', ascending=False, key=lambda x: x.str.replace('$', '').str.replace(',', '').astype(float))
                
                st.dataframe(df_trends.head(10), use_container_width=True)
                
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
        
        # Color code based on utilization
        def highlight_utilization(row):
            if row['AvgCPU'] < 10:
                return ['background-color: #ffcccc'] * len(row)
            elif row['AvgCPU'] < 50:
                return ['background-color: #ffffcc'] * len(row)
            else:
                return ['background-color: #ccffcc'] * len(row)
        
        styled_df = df_instances.style.apply(highlight_utilization, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Utilization distribution
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
        
        # Display recommendations
        df_recs = pd.DataFrame(recommendations)
        
        st.dataframe(df_recs, use_container_width=True)
        
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
        ri_savings = monthly_estimate * (ri_percentage / 100) * 0.5  # Assume 50% discount
        rs_savings = monthly_estimate * (rightsizing_savings / 100)
        spot_savings = monthly_estimate * (spot_percentage / 100) * 0.7  # Assume 70% discount
        
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
    st.header("Lambda Function Testing")
    
    st.markdown("Test the deployed Lambda function directly")
    
    # Test options
    test_function = st.selectbox("Select Function", ["getCostBreakdown", "analyzeTrends", "getOptimizations"])
    
    if test_function == "getCostBreakdown":
        test_days = st.number_input("Days to analyze", 1, 90, 7)
        test_params = [{"name": "days", "value": str(test_days)}]
    else:
        test_params = []
    
    if st.button("Test Lambda Function"):
        with st.spinner("Invoking Lambda..."):
            test_event = {
                'apiPath': f'/{test_function}',
                'parameters': test_params,
                'actionGroup': 'test',
                'httpMethod': 'POST'
            }
            
            try:
                response = lambda_client.invoke(
                    FunctionName='finops-cost-analysis',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_event)
                )
                
                result = json.loads(response['Payload'].read())
                
                st.success("Lambda invoked successfully!")
                
                # Display response
                st.subheader("Response")
                
                if 'response' in result and 'responseBody' in result['response']:
                    body = result['response']['responseBody']['application/json']['body']
                    parsed_body = json.loads(body)
                    
                    st.json(parsed_body)
                    
                    # Visualize if cost data
                    if 'cost_by_service' in parsed_body:
                        df = pd.DataFrame(
                            list(parsed_body['cost_by_service'].items()),
                            columns=['Service', 'Cost']
                        )
                        
                        fig = px.bar(df, x='Service', y='Cost',
                                    title="Cost by Service from Lambda")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.json(result)
                    
            except Exception as e:
                st.error(f"Error invoking Lambda: {e}")
                st.code(str(e))

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🤖 **AI-Powered FinOps**")
    st.caption("AWS Bedrock Integration")

with col2:
    st.markdown("💰 **Cost Optimization**")
    st.caption("Real-time Analysis")

with col3:
    st.markdown("📊 **Data-Driven Insights**")
    st.caption("Automated Recommendations")