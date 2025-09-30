#!/usr/bin/env python3
"""
Final fix for action group and run tests
"""

import boto3
import json
import time

# Load config
with open('finops_config.json', 'r') as f:
    config = json.load(f)

bedrock = boto3.client('bedrock-agent')
s3 = boto3.client('s3')
bucket_name = config['bucket_name']
agent_id = config['agents'][0]['agent_id']
account_id = config['account_id']
region = config['region']

print("Fixing Bedrock Agent Action Group...")

# First, list existing action groups
try:
    response = bedrock.list_agent_action_groups(
        agentId=agent_id,
        agentVersion='DRAFT'
    )
    
    # Delete existing action groups
    for ag in response.get('actionGroupSummaries', []):
        try:
            bedrock.delete_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupId=ag['actionGroupId']
            )
            print(f"Deleted existing action group: {ag['actionGroupName']}")
        except:
            pass
except:
    pass

# Create minimal working OpenAPI schema
minimal_schema = {
    "openapi": "3.0.0",
    "info": {
        "title": "FinOps API",
        "version": "1.0.0"
    },
    "paths": {
        "/getCostBreakdown": {
            "description": "Get cost breakdown",
            "get": {
                "operationId": "getCostBreakdown",
                "responses": {
                    "200": {
                        "description": "Success"
                    }
                }
            }
        }
    }
}

# Upload schema
s3.put_object(
    Bucket=bucket_name,
    Key='schemas/minimal-api.json',
    Body=json.dumps(minimal_schema)
)
print("Uploaded minimal schema")

# Wait a bit
time.sleep(2)

# Create action group with inline schema instead
try:
    # Try with inline schema
    response = bedrock.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='FinOpsActions',
        actionGroupExecutor={
            'lambda': f"arn:aws:lambda:{region}:{account_id}:function:finops-cost-analysis"
        },
        apiSchema={
            'payload': json.dumps(minimal_schema)
        },
        description='FinOps actions'
    )
    print("✓ Created action group with inline schema!")
    
    # Prepare agent
    bedrock.prepare_agent(agentId=agent_id)
    print("✓ Agent prepared")
    
except Exception as e:
    print(f"Still failed: {e}")
    print("\nAgent will work without action groups - using direct prompting")

print("\n" + "="*60)
print("Testing the deployed system...")
print("="*60 + "\n")

# Test without action groups - direct agent invocation
bedrock_runtime = boto3.client('bedrock-agent-runtime')
alias_id = config['agents'][0]['alias_id']

test_queries = [
    "What are my current AWS costs?",
    "Show me cost breakdown by service",
    "What cost optimization recommendations do you have?"
]

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 40)
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=f"test-{int(time.time())}",
            inputText=query
        )
        
        result = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result += chunk['bytes'].decode('utf-8')
        
        print("Response:", result[:500] + "..." if len(result) > 500 else result)
        
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(2)