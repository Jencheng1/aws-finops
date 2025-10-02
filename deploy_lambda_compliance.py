#!/usr/bin/env python3
"""
Deploy Lambda function for tag compliance
"""

import boto3
import zipfile
import json
import os
import sys

def create_lambda_deployment_package():
    """Create deployment package for Lambda"""
    print("Creating Lambda deployment package...")
    
    # Create a zip file with the Lambda function
    with zipfile.ZipFile('lambda_tag_compliance.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the main Lambda function
        zipf.write('lambda_tag_compliance.py', 'lambda_tag_compliance.py')
    
    print("Deployment package created: lambda_tag_compliance.zip")
    return 'lambda_tag_compliance.zip'

def create_lambda_role():
    """Create IAM role for Lambda function"""
    iam = boto3.client('iam')
    
    role_name = 'tag-compliance-lambda-role'
    
    # Check if role already exists
    try:
        role = iam.get_role(RoleName=role_name)
        print("Role {} already exists".format(role_name))
        return role['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        pass
    
    # Create the role
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description='Role for tag compliance Lambda function'
        )
        
        print("Created IAM role: {}".format(role_name))
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/ResourceGroupsandTagEditorReadOnlyAccess',
            'arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess',
            'arn:aws:iam::aws:policy/AmazonRDSReadOnlyAccess',
            'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
        ]
        
        for policy_arn in policies:
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        # Create and attach custom policy for tagging
        tag_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "tag:GetResources",
                        "tag:TagResources",
                        "tag:UntagResources",
                        "tag:GetTagKeys",
                        "tag:GetTagValues",
                        "ec2:CreateTags",
                        "ec2:DeleteTags",
                        "rds:AddTagsToResource",
                        "rds:RemoveTagsFromResource",
                        "rds:ListTagsForResource",
                        "s3:GetBucketTagging",
                        "s3:PutBucketTagging",
                        "sns:Publish",
                        "sts:GetCallerIdentity"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='TagCompliancePolicy',
            PolicyDocument=json.dumps(tag_policy)
        )
        
        # Wait for role to be available
        import time
        time.sleep(10)
        
        return response['Role']['Arn']
        
    except Exception as e:
        print("Error creating IAM role: {}".format(str(e)))
        sys.exit(1)

def create_dynamodb_table():
    """Create DynamoDB table for compliance history"""
    dynamodb = boto3.client('dynamodb')
    table_name = 'tag-compliance-history'
    
    try:
        # Check if table exists
        dynamodb.describe_table(TableName=table_name)
        print("DynamoDB table {} already exists".format(table_name))
        return
    except dynamodb.exceptions.ResourceNotFoundException:
        pass
    
    # Create table
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},
                {'AttributeName': 'sk', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'Owner', 'Value': 'finops-team'},
                {'Key': 'CostCenter', 'Value': 'operations'},
                {'Key': 'Project', 'Value': 'tag-compliance'}
            ]
        )
        print("Created DynamoDB table: {}".format(table_name))
    except Exception as e:
        print("Error creating DynamoDB table: {}".format(str(e)))

def deploy_lambda_function(zip_file, role_arn):
    """Deploy the Lambda function"""
    lambda_client = boto3.client('lambda')
    
    function_name = 'tag-compliance-checker'
    
    # Read the zip file
    with open(zip_file, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Check if function exists
        lambda_client.get_function(FunctionName=function_name)
        
        # Update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print("Updated Lambda function: {}".format(function_name))
        
        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Runtime='python3.9',
            Handler='lambda_tag_compliance.lambda_handler',
            Timeout=300,
            MemorySize=512,
            Environment={
                'Variables': {
                    'REQUIRED_TAGS': 'Environment,Owner,CostCenter,Project'
                }
            }
        )
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_tag_compliance.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='AWS Resource Tag Compliance Checker',
            Timeout=300,
            MemorySize=512,
            Environment={
                'Variables': {
                    'REQUIRED_TAGS': 'Environment,Owner,CostCenter,Project'
                }
            },
            Tags={
                'Environment': 'production',
                'Owner': 'finops-team',
                'CostCenter': 'operations',
                'Project': 'tag-compliance'
            }
        )
        print("Created Lambda function: {}".format(function_name))
    
    return response['FunctionArn']

def test_lambda_function():
    """Test the deployed Lambda function"""
    lambda_client = boto3.client('lambda')
    
    print("\nTesting Lambda function...")
    
    # Test 1: Basic scan
    test_event = {
        'action': 'scan'
    }
    
    response = lambda_client.invoke(
        FunctionName='tag-compliance-checker',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    
    result = json.loads(response['Payload'].read())
    print("Test 1 - Scan: Status Code = {}".format(result.get('statusCode', 'N/A')))
    
    # Test 2: Get report
    test_event = {
        'action': 'report',
        'report_type': 'summary'
    }
    
    response = lambda_client.invoke(
        FunctionName='tag-compliance-checker',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    
    result = json.loads(response['Payload'].read())
    print("Test 2 - Report: Status Code = {}".format(result.get('statusCode', 'N/A')))
    
    print("\nLambda function deployed and tested successfully!")

def main():
    """Main deployment function"""
    print("Deploying Tag Compliance Lambda Function...")
    
    # Create DynamoDB table first
    create_dynamodb_table()
    
    # Create deployment package
    zip_file = create_lambda_deployment_package()
    
    # Create IAM role
    role_arn = create_lambda_role()
    
    # Deploy Lambda function
    function_arn = deploy_lambda_function(zip_file, role_arn)
    
    print("\nDeployment completed!")
    print("Function ARN: {}".format(function_arn))
    
    # Test the function
    test_lambda_function()
    
    # Clean up zip file
    os.remove(zip_file)
    
    print("\nLambda function is ready to use!")

if __name__ == '__main__':
    main()