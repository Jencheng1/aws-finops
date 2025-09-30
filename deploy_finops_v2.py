#!/usr/bin/env python3
"""
Simplified FinOps System Deployment Script
"""

import boto3
import json
import time
import os
import zipfile
import sys
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

print("Starting FinOps deployment...")

# Initialize AWS clients
iam = boto3.client('iam')
s3 = boto3.client('s3') 
lambda_client = boto3.client('lambda')
bedrock_agent = boto3.client('bedrock-agent')
sts = boto3.client('sts')

# Get account info
account_info = sts.get_caller_identity()
account_id = account_info['Account']
region = boto3.Session().region_name or 'us-east-1'

print("AWS Account:", account_id)
print("Region:", region)

# Create unique bucket name
timestamp = int(time.time())
BUCKET_NAME = "finops-bedrock-{}-{}".format(account_id, timestamp)
LAMBDA_DIR = "lambda_functions"

# Step 1: Create IAM Roles
print("\n=== Creating IAM Roles ===")

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
    response = iam.create_role(
        RoleName='FinOpsBedrockRole',
        AssumeRolePolicyDocument=json.dumps(bedrock_trust)
    )
    print("Created Bedrock role")
except:
    print("Bedrock role exists")

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
    response = iam.create_role(
        RoleName='FinOpsLambdaRole',
        AssumeRolePolicyDocument=json.dumps(lambda_trust)
    )
    print("Created Lambda role")
except:
    print("Lambda role exists")

# Attach policies
policies = [
    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
    'arn:aws:iam::aws:policy/AWSCostExplorerReadOnlyAccess',
    'arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess',
    'arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess'
]

for policy in policies:
    try:
        iam.attach_role_policy(
            RoleName='FinOpsLambdaRole',
            PolicyArn=policy
        )
    except:
        pass

# Bedrock policies
try:
    iam.attach_role_policy(
        RoleName='FinOpsBedrockRole',
        PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentBedrockFoundationModelPolicy'
    )
except:
    pass

# Lambda invoke policy for Bedrock
lambda_invoke_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["lambda:InvokeFunction"],
        "Resource": "arn:aws:lambda:{}:{}:function:finops-*".format(region, account_id)
    }]
}

try:
    iam.put_role_policy(
        RoleName='FinOpsBedrockRole',
        PolicyName='LambdaInvoke',
        PolicyDocument=json.dumps(lambda_invoke_policy)
    )
except:
    pass

print("IAM setup complete")
time.sleep(10)

# Step 2: Create S3 Bucket
print("\n=== Creating S3 Bucket ===")
try:
    if region == 'us-east-1':
        s3.create_bucket(Bucket=BUCKET_NAME)
    else:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
    print("Created bucket:", BUCKET_NAME)
except:
    print("Bucket exists:", BUCKET_NAME)

# Step 3: Create Lambda Functions
print("\n=== Creating Lambda Functions ===")
os.makedirs(LAMBDA_DIR, exist_ok=True)

# Cost Analysis Lambda
cost_lambda = '''import json
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    
    api_path = event.get('apiPath', '')
    params = {}
    for p in event.get('parameters', []):
        params[p.get('name', '')] = p.get('value', '')
    
    if 'get_cost_breakdown' in api_path:
        days = int(params.get('days', '7'))
        end = datetime.now().date()
        start = end - timedelta(days=days)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        costs = {}
        for r in response['ResultsByTime']:
            for g in r['Groups']:
                svc = g['Keys'][0]
                cost = float(g['Metrics']['UnblendedCost']['Amount'])
                costs[svc] = costs.get(svc, 0) + cost
        
        sorted_costs = sorted(costs.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            'total_cost': sum(costs.values()),
            'top_services': dict(sorted_costs[:5])
        }
    else:
        result = {'message': 'Function called'}
    
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
'''

with open(os.path.join(LAMBDA_DIR, 'cost_lambda.py'), 'w') as f:
    f.write(cost_lambda)

# Create zip
with zipfile.ZipFile('cost_lambda.zip', 'w') as zf:
    zf.write(os.path.join(LAMBDA_DIR, 'cost_lambda.py'), 'cost_lambda.py')

# Upload and deploy
s3.upload_file('cost_lambda.zip', BUCKET_NAME, 'lambdas/cost_lambda.zip')

try:
    lambda_client.create_function(
        FunctionName='finops-cost-analysis',
        Runtime='python3.9',
        Role="arn:aws:iam::{}:role/FinOpsLambdaRole".format(account_id),
        Handler='cost_lambda.lambda_handler',
        Code={'S3Bucket': BUCKET_NAME, 'S3Key': 'lambdas/cost_lambda.zip'},
        Timeout=60
    )
    print("Created cost analysis Lambda")
except:
    lambda_client.update_function_code(
        FunctionName='finops-cost-analysis',
        S3Bucket=BUCKET_NAME,
        S3Key='lambdas/cost_lambda.zip'
    )
    print("Updated cost analysis Lambda")

# Step 4: Create API Schema
print("\n=== Creating API Schema ===")
api_schema = {
    "openapi": "3.0.0",
    "info": {"title": "FinOps API", "version": "1.0.0"},
    "paths": {
        "/get_cost_breakdown": {
            "post": {
                "summary": "Get cost breakdown",
                "operationId": "getCostBreakdown",
                "parameters": [{
                    "name": "days",
                    "in": "query",
                    "schema": {"type": "string", "default": "7"}
                }],
                "responses": {"200": {"description": "Success"}}
            }
        }
    }
}

s3.put_object(
    Bucket=BUCKET_NAME,
    Key='schemas/cost-api.json',
    Body=json.dumps(api_schema)
)
print("Created API schema")

# Step 5: Create Bedrock Agent
print("\n=== Creating Bedrock Agent ===")

instruction = """You are a FinOps assistant. Help users understand AWS costs.
When asked about costs, use the get_cost_breakdown function to fetch data.
Provide clear insights about spending patterns."""

try:
    agent_resp = bedrock_agent.create_agent(
        agentName='FinOpsCostAgent',
        agentResourceRoleArn="arn:aws:iam::{}:role/FinOpsBedrockRole".format(account_id),
        instruction=instruction,
        foundationModel='anthropic.claude-3-sonnet-20240229-v1:0'
    )
    agent_id = agent_resp['agent']['agentId']
    print("Created agent:", agent_id)
    
    time.sleep(5)
    
    # Create action group
    bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='CostActions',
        actionGroupExecutor={
            'lambda': "arn:aws:lambda:{}:{}:function:finops-cost-analysis".format(region, account_id)
        },
        apiSchema={
            's3': {
                's3BucketName': BUCKET_NAME,
                's3ObjectKey': 'schemas/cost-api.json'
            }
        }
    )
    print("Created action group")
    
    # Prepare agent
    bedrock_agent.prepare_agent(agentId=agent_id)
    print("Prepared agent")
    
    time.sleep(10)
    
    # Create alias
    alias_resp = bedrock_agent.create_agent_alias(
        agentId=agent_id,
        agentAliasName='live'
    )
    alias_id = alias_resp['agentAlias']['agentAliasId']
    print("Created alias:", alias_id)
    
    # Save config
    config = {
        'agent_id': agent_id,
        'alias_id': alias_id,
        'bucket': BUCKET_NAME,
        'region': region
    }
    
    with open('finops_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\nDeployment complete!")
    print("Agent ID:", agent_id)
    print("Alias ID:", alias_id)
    
except Exception as e:
    print("Error creating agent:", str(e))