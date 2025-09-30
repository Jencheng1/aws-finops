#!/usr/bin/env python3
"""
Complete FinOps System with Bedrock Agents, Lambda Functions, and Streamlit
"""

import boto3
import json
import time
import os
import zipfile
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize clients
iam = boto3.client('iam')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
bedrock = boto3.client('bedrock-agent')
bedrock_runtime = boto3.client('bedrock-agent-runtime')
ce = boto3.client('ce')
sts = boto3.client('sts')

# Get account info
account_id = sts.get_caller_identity()['Account']
region = boto3.Session().region_name or 'us-east-1'
timestamp = int(time.time())
bucket_name = f"finops-bedrock-{account_id}-{timestamp}"

print(f"Deploying FinOps System")
print(f"Account: {account_id}")
print(f"Region: {region}")
print(f"Bucket: {bucket_name}")
print("=" * 60)

# Clean up directory
os.makedirs('lambda_code', exist_ok=True)

def create_iam_roles():
    """Create IAM roles for Bedrock and Lambda"""
    print("\n1. Creating IAM Roles...")
    
    # Bedrock Agent Role
    bedrock_trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        iam.create_role(
            RoleName='FinOpsBedrockAgentRole',
            AssumeRolePolicyDocument=json.dumps(bedrock_trust)
        )
        print("   ✓ Created Bedrock Agent Role")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("   ✓ Bedrock Agent Role exists")
    
    # Lambda Role
    lambda_trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        iam.create_role(
            RoleName='FinOpsLambdaRole',
            AssumeRolePolicyDocument=json.dumps(lambda_trust)
        )
        print("   ✓ Created Lambda Role")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("   ✓ Lambda Role exists")
    
    # Attach policies
    policies = {
        'FinOpsBedrockAgentRole': [
            'arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentBedrockFoundationModelPolicy'
        ],
        'FinOpsLambdaRole': [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AWSCostExplorerReadOnlyAccess',
            'arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess',
            'arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess',
            'arn:aws:iam::aws:policy/AmazonRDSReadOnlyAccess'
        ]
    }
    
    for role_name, policy_arns in policies.items():
        for policy_arn in policy_arns:
            try:
                iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            except:
                pass
    
    # Add Lambda invoke permission to Bedrock role
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": f"arn:aws:lambda:{region}:{account_id}:function:finops-*"
        }]
    }
    
    try:
        iam.put_role_policy(
            RoleName='FinOpsBedrockAgentRole',
            PolicyName='LambdaInvokePolicy',
            PolicyDocument=json.dumps(lambda_policy)
        )
    except:
        pass
    
    print("   ✓ Policies attached")
    time.sleep(10)  # Wait for IAM propagation

def create_s3_bucket():
    """Create S3 bucket for artifacts"""
    print("\n2. Creating S3 Bucket...")
    
    try:
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"   ✓ Created bucket: {bucket_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"   ✓ Bucket exists: {bucket_name}")

def create_lambda_functions():
    """Create and deploy Lambda functions"""
    print("\n3. Creating Lambda Functions...")
    
    # Lambda function configurations
    lambda_configs = [
        {
            'name': 'finops-cost-analysis',
            'handler': 'lambda_function.lambda_handler',
            'code': '''import json
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    
    # Get API path from event
    api_path = event.get('apiPath', '')
    
    # Parse parameters
    params = {}
    for param in event.get('parameters', []):
        params[param['name']] = param['value']
    
    # Route to appropriate function
    if '/getCostBreakdown' in api_path:
        result = get_cost_breakdown(params)
    elif '/analyzeTrends' in api_path:
        result = analyze_trends(params)
    elif '/getOptimizations' in api_path:
        result = get_optimizations(params)
    else:
        result = {'error': 'Unknown API path'}
    
    # Return Bedrock-formatted response
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup', ''),
            'apiPath': api_path,
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
        }
    }

def get_cost_breakdown(params):
    days = int(params.get('days', '7'))
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
        
        costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                costs[service] = costs.get(service, 0) + cost
        
        sorted_costs = sorted(costs.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_cost': round(sum(costs.values()), 2),
            'cost_by_service': {k: round(v, 2) for k, v in sorted_costs[:10]},
            'period': f'{days} days'
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_trends(params):
    days = int(params.get('days', '30'))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
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
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append({'date': date, 'cost': round(cost, 2)})
        
        # Calculate trend
        if len(daily_costs) > 7:
            first_week = sum(d['cost'] for d in daily_costs[:7]) / 7
            last_week = sum(d['cost'] for d in daily_costs[-7:]) / 7
            trend = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
        else:
            trend = 0
        
        return {
            'trend_percentage': round(trend, 2),
            'trend_direction': 'increasing' if trend > 0 else 'decreasing',
            'average_daily_cost': round(sum(d['cost'] for d in daily_costs) / len(daily_costs), 2),
            'period': f'{days} days'
        }
    except Exception as e:
        return {'error': str(e)}

def get_optimizations(params):
    # Simple optimization recommendations
    return {
        'recommendations': [
            {
                'type': 'Reserved Instances',
                'potential_savings': '20-40%',
                'description': 'Purchase RIs for consistently running instances'
            },
            {
                'type': 'Spot Instances',
                'potential_savings': 'Up to 90%',
                'description': 'Use Spot for fault-tolerant workloads'
            },
            {
                'type': 'Right-sizing',
                'potential_savings': '15-30%',
                'description': 'Adjust instance sizes based on utilization'
            }
        ]
    }
'''
        }
    ]
    
    for config in lambda_configs:
        # Write Lambda code
        with open(f"lambda_code/{config['name']}.py", 'w') as f:
            f.write(config['code'])
        
        # Create zip
        zip_path = f"{config['name']}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(f"lambda_code/{config['name']}.py", 'lambda_function.py')
        
        # Upload to S3
        s3_key = f"lambda/{zip_path}"
        s3.upload_file(zip_path, bucket_name, s3_key)
        
        # Deploy Lambda
        try:
            response = lambda_client.create_function(
                FunctionName=config['name'],
                Runtime='python3.9',
                Role=f"arn:aws:iam::{account_id}:role/FinOpsLambdaRole",
                Handler=config['handler'],
                Code={'S3Bucket': bucket_name, 'S3Key': s3_key},
                Timeout=60,
                MemorySize=256
            )
            print(f"   ✓ Created Lambda: {config['name']}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                # Update existing
                lambda_client.update_function_code(
                    FunctionName=config['name'],
                    S3Bucket=bucket_name,
                    S3Key=s3_key
                )
                print(f"   ✓ Updated Lambda: {config['name']}")
        
        # Clean up
        os.remove(zip_path)
        time.sleep(2)

def create_api_schemas():
    """Create OpenAPI schemas for Bedrock agents"""
    print("\n4. Creating API Schemas...")
    
    # Complete OpenAPI schema
    api_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "FinOps Cost Analysis API",
            "version": "1.0.0",
            "description": "API for AWS cost analysis and optimization"
        },
        "paths": {
            "/getCostBreakdown": {
                "post": {
                    "summary": "Get cost breakdown by service",
                    "description": "Returns AWS costs broken down by service",
                    "operationId": "getCostBreakdown",
                    "parameters": [
                        {
                            "name": "days",
                            "in": "query",
                            "description": "Number of days to analyze",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "default": "7"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "total_cost": {"type": "number"},
                                            "cost_by_service": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/analyzeTrends": {
                "post": {
                    "summary": "Analyze cost trends",
                    "description": "Analyzes cost trends over time",
                    "operationId": "analyzeTrends",
                    "parameters": [
                        {
                            "name": "days",
                            "in": "query",
                            "description": "Number of days to analyze",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "default": "30"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response"
                        }
                    }
                }
            },
            "/getOptimizations": {
                "post": {
                    "summary": "Get optimization recommendations",
                    "description": "Returns cost optimization recommendations",
                    "operationId": "getOptimizations",
                    "responses": {
                        "200": {
                            "description": "Successful response"
                        }
                    }
                }
            }
        }
    }
    
    # Upload schema
    s3.put_object(
        Bucket=bucket_name,
        Key='schemas/cost-api.json',
        Body=json.dumps(api_schema)
    )
    print("   ✓ Created API schema")

def create_bedrock_agents():
    """Create Bedrock agents with action groups"""
    print("\n5. Creating Bedrock Agents...")
    
    agent_configs = [
        {
            'name': 'FinOpsCostAnalyzer',
            'description': 'AI agent for AWS cost analysis',
            'instruction': '''You are a FinOps specialist focused on helping users understand and optimize their AWS costs.

Your capabilities:
1. Analyze AWS costs using the getCostBreakdown function
2. Identify spending trends with analyzeTrends
3. Provide optimization recommendations with getOptimizations

When users ask about costs:
- Always fetch real data using the available functions
- Provide specific numbers and percentages
- Highlight the top cost drivers
- Suggest actionable optimizations

Be proactive in identifying cost-saving opportunities.''',
            'lambda_name': 'finops-cost-analysis',
            'schema_key': 'schemas/cost-api.json'
        }
    ]
    
    created_agents = []
    
    for config in agent_configs:
        try:
            # Create agent
            response = bedrock.create_agent(
                agentName=config['name'],
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/FinOpsBedrockAgentRole",
                description=config['description'],
                idleSessionTTLInSeconds=1800,
                foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
                instruction=config['instruction']
            )
            
            agent_id = response['agent']['agentId']
            print(f"   ✓ Created agent: {config['name']} ({agent_id})")
            
            # Wait for agent to be ready
            time.sleep(5)
            
            # Create action group
            try:
                bedrock.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    actionGroupName='CostAnalysisActions',
                    actionGroupExecutor={
                        'lambda': f"arn:aws:lambda:{region}:{account_id}:function:{config['lambda_name']}"
                    },
                    apiSchema={
                        's3': {
                            's3BucketName': bucket_name,
                            's3ObjectKey': config['schema_key']
                        }
                    },
                    description='Actions for cost analysis'
                )
                print("   ✓ Created action group")
            except Exception as e:
                print(f"   ! Error creating action group: {e}")
            
            # Prepare agent
            bedrock.prepare_agent(agentId=agent_id)
            print("   ✓ Prepared agent")
            
            time.sleep(10)
            
            # Create alias
            alias_response = bedrock.create_agent_alias(
                agentId=agent_id,
                agentAliasName='production',
                description='Production alias'
            )
            
            alias_id = alias_response['agentAlias']['agentAliasId']
            print(f"   ✓ Created alias: {alias_id}")
            
            created_agents.append({
                'name': config['name'],
                'agent_id': agent_id,
                'alias_id': alias_id
            })
            
        except Exception as e:
            print(f"   ! Error creating agent: {e}")
    
    return created_agents

def create_streamlit_app(agents):
    """Create Streamlit app for testing"""
    print("\n6. Creating Streamlit App...")
    
    streamlit_code = f'''import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-agent-runtime')
ce = boto3.client('ce')

# Agent configuration
AGENT_ID = "{agents[0]['agent_id'] if agents else 'AGENT_ID'}"
AGENT_ALIAS = "{agents[0]['alias_id'] if agents else 'ALIAS_ID'}"

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
            TimePeriod={{
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            }},
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{{'Type': 'DIMENSION', 'Key': 'SERVICE'}}]
        )
        
        # Process data
        costs_by_service = {{}}
        daily_costs = []
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total_daily = 0
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                costs_by_service[service] = costs_by_service.get(service, 0) + cost
                total_daily += cost
            
            daily_costs.append({{'date': date, 'cost': total_daily}})
        
        total_cost = sum(costs_by_service.values())
        
        # Display metrics
        col1.metric("Total Cost", f"${{total_cost:,.2f}}", f"Last {{days}} days")
        col2.metric("Daily Average", f"${{total_cost/days:,.2f}}")
        col3.metric("Services Used", len(costs_by_service))
        
        # Top services chart
        st.subheader("Top Services by Cost")
        top_services = sorted(costs_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
        
        df = pd.DataFrame(top_services, columns=['Service', 'Cost'])
        fig = px.bar(df, x='Cost', y='Service', orientation='h', 
                     title=f"Top 10 Services (Last {{days}} days)")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Daily costs chart
        st.subheader("Daily Cost Trend")
        df_daily = pd.DataFrame(daily_costs)
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        
        fig_daily = px.line(df_daily, x='date', y='cost', 
                           title=f"Daily Costs (Last {{days}} days)")
        fig_daily.update_layout(height=300)
        st.plotly_chart(fig_daily, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error fetching cost data: {{e}}")

with tab2:
    st.header("Cost Trends Analysis")
    
    trend_period = st.selectbox("Select Period", ["7 days", "30 days", "90 days"])
    trend_days = int(trend_period.split()[0])
    
    if st.button("Analyze Trends"):
        with st.spinner("Analyzing trends..."):
            try:
                # Call Bedrock agent
                session_id = f"trend-{{datetime.now().timestamp()}}"
                
                response = bedrock_runtime.invoke_agent(
                    agentId=AGENT_ID,
                    agentAliasId=AGENT_ALIAS,
                    sessionId=session_id,
                    inputText=f"Analyze my cost trends for the last {{trend_days}} days"
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
                st.error(f"Error: {{e}}")

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
    if prompt := st.chat_input("Ask about your AWS costs..."):
        # Add user message
        st.session_state.messages.append({{"role": "user", "content": prompt}})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    session_id = f"chat-{{datetime.now().timestamp()}}"
                    
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
                    st.session_state.messages.append({{"role": "assistant", "content": result}})
                    
                except Exception as e:
                    st.error(f"Error: {{e}}")

with tab4:
    st.header("Cost Optimization Recommendations")
    
    if st.button("Get AI Recommendations"):
        with st.spinner("Generating recommendations..."):
            try:
                session_id = f"opt-{{datetime.now().timestamp()}}"
                
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
                st.error(f"Error: {{e}}")
    
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
'''
    
    # Save Streamlit app
    with open('finops_dashboard.py', 'w') as f:
        f.write(streamlit_code)
    
    print("   ✓ Created finops_dashboard.py")

def create_test_suite(agents):
    """Create comprehensive test suite"""
    print("\n7. Creating Test Suite...")
    
    test_code = f'''import boto3
import json
import time
from datetime import datetime

# Initialize clients
bedrock_runtime = boto3.client('bedrock-agent-runtime')
lambda_client = boto3.client('lambda')

# Configuration
AGENT_ID = "{agents[0]['agent_id'] if agents else 'AGENT_ID'}"
AGENT_ALIAS = "{agents[0]['alias_id'] if agents else 'ALIAS_ID'}"
LAMBDA_NAME = "finops-cost-analysis"

class FinOpsTestSuite:
    def __init__(self):
        self.results = []
    
    def test_lambda_function(self):
        """Test Lambda function directly"""
        print("Testing Lambda function...")
        
        test_event = {{
            'apiPath': '/getCostBreakdown',
            'parameters': [{{'name': 'days', 'value': '7'}}]
        }}
        
        try:
            response = lambda_client.invoke(
                FunctionName=LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            assert 'response' in result
            assert result['response']['httpStatusCode'] == 200
            
            self.results.append({{'test': 'Lambda Function', 'status': 'PASSED'}})
            print("✓ Lambda function test passed")
            
        except Exception as e:
            self.results.append({{'test': 'Lambda Function', 'status': 'FAILED', 'error': str(e)}})
            print(f"✗ Lambda function test failed: {{e}}")
    
    def test_bedrock_agent(self):
        """Test Bedrock agent"""
        print("Testing Bedrock agent...")
        
        test_queries = [
            "What are my AWS costs for the last 7 days?",
            "Show me cost trends",
            "What optimization recommendations do you have?"
        ]
        
        for query in test_queries:
            try:
                session_id = f"test-{{datetime.now().timestamp()}}"
                
                response = bedrock_runtime.invoke_agent(
                    agentId=AGENT_ID,
                    agentAliasId=AGENT_ALIAS,
                    sessionId=session_id,
                    inputText=query
                )
                
                # Check response
                result = ""
                for event in response.get('completion', []):
                    if 'chunk' in event:
                        result += event['chunk']['bytes'].decode('utf-8')
                
                assert len(result) > 0
                
                self.results.append({{
                    'test': f'Agent Query: {{query[:30]}}...',
                    'status': 'PASSED'
                }})
                print(f"✓ Agent test passed: {{query[:30]}}...")
                
                time.sleep(2)  # Avoid rate limiting
                
            except Exception as e:
                self.results.append({{
                    'test': f'Agent Query: {{query[:30]}}...',
                    'status': 'FAILED',
                    'error': str(e)
                }})
                print(f"✗ Agent test failed: {{e}}")
    
    def test_cost_explorer_access(self):
        """Test Cost Explorer access"""
        print("Testing Cost Explorer access...")
        
        ce = boto3.client('ce')
        
        try:
            response = ce.get_cost_and_usage(
                TimePeriod={{
                    'Start': '2024-01-01',
                    'End': '2024-01-02'
                }},
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            assert 'ResultsByTime' in response
            
            self.results.append({{'test': 'Cost Explorer Access', 'status': 'PASSED'}})
            print("✓ Cost Explorer access test passed")
            
        except Exception as e:
            self.results.append({{
                'test': 'Cost Explorer Access',
                'status': 'FAILED',
                'error': str(e)
            }})
            print(f"✗ Cost Explorer test failed: {{e}}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\\nRunning FinOps Test Suite...")
        print("=" * 50)
        
        self.test_lambda_function()
        self.test_cost_explorer_access()
        self.test_bedrock_agent()
        
        # Summary
        print("\\nTest Summary:")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        
        for result in self.results:
            status = "✓" if result['status'] == 'PASSED' else "✗"
            print(f"{{status}} {{result['test']}}: {{result['status']}}")
            if 'error' in result:
                print(f"  Error: {{result['error']}}")
        
        print(f"\\nTotal: {{len(self.results)}} tests")
        print(f"Passed: {{passed}}")
        print(f"Failed: {{failed}}")
        
        return failed == 0

if __name__ == "__main__":
    suite = FinOpsTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print("\\n✅ All tests passed!")
    else:
        print("\\n❌ Some tests failed!")
'''
    
    with open('test_finops.py', 'w') as f:
        f.write(test_code)
    
    print("   ✓ Created test_finops.py")

def save_configuration(agents):
    """Save deployment configuration"""
    print("\n8. Saving Configuration...")
    
    config = {
        'deployment_time': datetime.now().isoformat(),
        'account_id': account_id,
        'region': region,
        'bucket_name': bucket_name,
        'agents': agents,
        'lambda_functions': ['finops-cost-analysis'],
        'streamlit_app': 'finops_dashboard.py',
        'test_suite': 'test_finops.py'
    }
    
    with open('finops_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("   ✓ Saved finops_config.json")

# Main deployment
def main():
    try:
        # Deploy everything
        create_iam_roles()
        create_s3_bucket()
        create_lambda_functions()
        create_api_schemas()
        agents = create_bedrock_agents()
        create_streamlit_app(agents)
        create_test_suite(agents)
        save_configuration(agents)
        
        print("\n" + "=" * 60)
        print("🎉 FinOps System Deployment Complete!")
        print("=" * 60)
        
        if agents:
            print(f"\nAgent ID: {agents[0]['agent_id']}")
            print(f"Alias ID: {agents[0]['alias_id']}")
        
        print("\nNext Steps:")
        print("1. Run tests: python3 test_finops.py")
        print("2. Start dashboard: streamlit run finops_dashboard.py")
        print("3. Check configuration: cat finops_config.json")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()