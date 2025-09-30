#!/usr/bin/env python3
"""
Fix Bedrock Agent Action Group with correct OpenAPI schema
"""

import boto3
import json

# Read config
with open('finops_config.json', 'r') as f:
    config = json.load(f)

bedrock = boto3.client('bedrock-agent')
bucket_name = config['bucket_name']
agent_id = config['agents'][0]['agent_id']

# Correct OpenAPI schema
api_schema = {
    "openapi": "3.0.1",
    "info": {
        "title": "FinOps API",
        "version": "1.0"
    },
    "paths": {
        "/getCostBreakdown": {
            "post": {
                "description": "Get cost breakdown by service",
                "operationId": "getCostBreakdown",
                "parameters": [{
                    "name": "days",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"}
                }],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Upload corrected schema
s3 = boto3.client('s3')
s3.put_object(
    Bucket=bucket_name,
    Key='schemas/fixed-api.json',
    Body=json.dumps(api_schema)
)

# Try to create action group again
try:
    response = bedrock.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='CostActions',
        actionGroupExecutor={
            'lambda': f"arn:aws:lambda:{config['region']}:{config['account_id']}:function:finops-cost-analysis"
        },
        apiSchema={
            's3': {
                's3BucketName': bucket_name,
                's3ObjectKey': 'schemas/fixed-api.json'
            }
        }
    )
    print("✓ Created action group successfully")
    
    # Prepare agent again
    bedrock.prepare_agent(agentId=agent_id)
    print("✓ Agent prepared")
    
except Exception as e:
    print(f"Error: {e}")