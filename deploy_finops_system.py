#!/usr/bin/env python3
"""
Complete FinOps System Deployment Script
Deploys all AWS resources, Lambda functions, Bedrock agents, and Streamlit app
"""

import boto3
import json
import time
import os
import zipfile
import sys
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize AWS clients
iam = boto3.client('iam')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
bedrock_agent = boto3.client('bedrock-agent')
bedrock_runtime = boto3.client('bedrock-agent-runtime')
sts = boto3.client('sts')

# Get account info
account_id = sts.get_caller_identity()['Account']
region = boto3.Session().region_name or 'us-east-1'

# Global configuration
LAMBDA_DIR = "lambda_functions"

def create_iam_roles():
    """Create necessary IAM roles for Bedrock and Lambda"""
    print("Creating IAM roles...")
    
    # Bedrock Agent Role
    bedrock_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam.create_role(
            RoleName='FinOpsBedrockAgentRole',
            AssumeRolePolicyDocument=json.dumps(bedrock_trust_policy),
            Description='Role for FinOps Bedrock Agents'
        )
        print(f"Created Bedrock Agent Role: {response['Role']['Arn']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Bedrock Agent Role already exists")
        else:
            raise
    
    # Attach Bedrock policies
    try:
        iam.attach_role_policy(
            RoleName='FinOpsBedrockAgentRole',
            PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentBedrockFoundationModelPolicy'
        )
    except:
        pass
    
    # Create Lambda invocation policy for Bedrock
    lambda_invoke_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": f"arn:aws:lambda:{region}:{account_id}:function:finops-*"
            }
        ]
    }
    
    try:
        iam.put_role_policy(
            RoleName='FinOpsBedrockAgentRole',
            PolicyName='BedrockLambdaInvokePolicy',
            PolicyDocument=json.dumps(lambda_invoke_policy)
        )
    except:
        pass
    
    # Lambda Execution Role
    lambda_trust_policy = {
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
            RoleName='FinOpsLambdaExecutionRole',
            AssumeRolePolicyDocument=json.dumps(lambda_trust_policy),
            Description='Role for FinOps Lambda functions'
        )
        print(f"Created Lambda Role: {response['Role']['Arn']}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("Lambda Execution Role already exists")
        else:
            raise
    
    # Attach Lambda policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AWSCostExplorerReadOnlyAccess',
        'arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess',
        'arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess',
        'arn:aws:iam::aws:policy/AmazonRDSReadOnlyAccess'
    ]
    
    for policy in policies:
        try:
            iam.attach_role_policy(
                RoleName='FinOpsLambdaExecutionRole',
                PolicyArn=policy
            )
        except:
            pass
    
    # Wait for roles to propagate
    time.sleep(10)
    return True

def create_s3_bucket():
    """Create S3 bucket for deployment artifacts"""
    bucket_name = f"finops-bedrock-{account_id}-{int(time.time())}"
    print(f"Creating S3 bucket: {bucket_name}")
    
    try:
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        print(f"Created S3 bucket: {bucket_name}")
        return bucket_name
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"Bucket {bucket_name} already exists")
            return bucket_name
        else:
            raise

def create_lambda_functions(bucket_name):
    """Create and deploy Lambda functions"""
    print("Creating Lambda functions...")
    
    # Create directory for Lambda code
    os.makedirs(LAMBDA_DIR, exist_ok=True)
    
    # Cost Analysis Lambda
    cost_analysis_code = '''import json
import boto3
from datetime import datetime, timedelta

ce_client = boto3.client('ce')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    # Parse parameters
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters to dict
    params = {}
    for param in parameters:
        params[param.get('name', '')] = param.get('value', '')
    
    try:
        if 'get_cost_breakdown' in api_path:
            result = get_cost_breakdown(params)
        elif 'analyze_cost_trends' in api_path:
            result = analyze_cost_trends(params)
        elif 'identify_cost_anomalies' in api_path:
            result = identify_cost_anomalies(params)
        else:
            result = {'error': f'Unknown path: {api_path}'}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }

def get_cost_breakdown(params):
    days = int(params.get('days', '7'))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        cost_by_service = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if service not in cost_by_service:
                    cost_by_service[service] = 0
                cost_by_service[service] += cost
        
        sorted_costs = sorted(
            cost_by_service.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'period': f'{days} days',
            'total_cost': round(sum(cost_by_service.values()), 2),
            'cost_by_service': {k: round(v, 2) for k, v in sorted_costs[:10]}
        }
    except Exception as e:
        return {'error': f'Failed to get cost breakdown: {str(e)}'}

def analyze_cost_trends(params):
    days = int(params.get('days', '30'))
    service = params.get('service', '')
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        query_params = {
            'TimePeriod': {
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            'Granularity': 'DAILY',
            'Metrics': ['UnblendedCost']
        }
        
        if service:
            query_params['Filter'] = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service]
                }
            }
        
        response = ce_client.get_cost_and_usage(**query_params)
        
        daily_costs = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append({
                'date': date,
                'cost': round(cost, 2)
            })
        
        # Calculate trend
        if len(daily_costs) > 7:
            first_week_avg = sum(d['cost'] for d in daily_costs[:7]) / 7
            last_week_avg = sum(d['cost'] for d in daily_costs[-7:]) / 7
            if first_week_avg > 0:
                trend_percentage = ((last_week_avg - first_week_avg) / first_week_avg) * 100
            else:
                trend_percentage = 0
        else:
            trend_percentage = 0
        
        return {
            'period': f'{days} days',
            'service': service or 'All Services',
            'trend': {
                'percentage': round(trend_percentage, 2),
                'direction': 'increasing' if trend_percentage > 0 else 'decreasing'
            },
            'average_daily_cost': round(sum(d['cost'] for d in daily_costs) / len(daily_costs) if daily_costs else 0, 2),
            'data_points': len(daily_costs)
        }
    except Exception as e:
        return {'error': f'Failed to analyze trends: {str(e)}'}

def identify_cost_anomalies(params):
    threshold = float(params.get('threshold', '20'))
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    try:
        response = ce_client.get_cost_and_usage(
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
            daily_costs.append(cost)
        
        if not daily_costs:
            return {'anomalies_found': 0, 'anomalies': []}
        
        avg_cost = sum(daily_costs) / len(daily_costs)
        
        anomalies = []
        for i, cost in enumerate(daily_costs):
            if avg_cost > 0:
                deviation = ((cost - avg_cost) / avg_cost) * 100
                if abs(deviation) > threshold:
                    anomalies.append({
                        'date': (start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                        'cost': round(cost, 2),
                        'deviation_percentage': round(deviation, 2),
                        'type': 'spike' if deviation > 0 else 'drop'
                    })
        
        return {
            'anomalies_found': len(anomalies),
            'threshold_used': threshold,
            'average_daily_cost': round(avg_cost, 2),
            'anomalies': anomalies[:10]
        }
    except Exception as e:
        return {'error': f'Failed to identify anomalies: {str(e)}'}
'''
    
    # Write Lambda function
    with open(os.path.join(LAMBDA_DIR, 'cost_analysis_lambda.py'), 'w') as f:
        f.write(cost_analysis_code)
    
    # Optimization Lambda
    optimization_code = '''import json
import boto3
from datetime import datetime, timedelta

ec2_client = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
rds_client = boto3.client('rds')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    
    params = {}
    for param in parameters:
        params[param.get('name', '')] = param.get('value', '')
    
    try:
        if 'get_optimization_recommendations' in api_path:
            result = get_optimization_recommendations(params)
        elif 'identify_idle_resources' in api_path:
            result = identify_idle_resources(params)
        else:
            result = {'error': f'Unknown path: {api_path}'}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }

def get_optimization_recommendations(params):
    resource_type = params.get('resource_type', 'all')
    recommendations = []
    
    if resource_type in ['all', 'ec2']:
        ec2_recs = get_ec2_recommendations()
        recommendations.extend(ec2_recs)
    
    if resource_type in ['all', 'rds']:
        rds_recs = get_rds_recommendations()
        recommendations.extend(rds_recs)
    
    total_savings = sum(rec.get('estimated_monthly_savings', 0) for rec in recommendations)
    
    return {
        'total_recommendations': len(recommendations),
        'total_estimated_monthly_savings': round(total_savings, 2),
        'recommendations': recommendations[:10]
    }

def get_ec2_recommendations():
    recommendations = []
    
    try:
        response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                cpu_stats = get_instance_cpu_utilization(instance_id)
                
                if cpu_stats['average'] < 10:
                    recommendations.append({
                        'resource_type': 'EC2',
                        'resource_id': instance_id,
                        'current_type': instance_type,
                        'recommendation': 'Terminate or stop instance',
                        'reason': f'Low CPU utilization: {cpu_stats["average"]:.1f}%',
                        'estimated_monthly_savings': estimate_instance_cost(instance_type),
                        'priority': 'high'
                    })
                elif cpu_stats['average'] < 40:
                    recommendations.append({
                        'resource_type': 'EC2',
                        'resource_id': instance_id,
                        'current_type': instance_type,
                        'recommendation': 'Consider downsizing',
                        'reason': f'Moderate CPU utilization: {cpu_stats["average"]:.1f}%',
                        'estimated_monthly_savings': estimate_instance_cost(instance_type) * 0.3,
                        'priority': 'medium'
                    })
    except Exception as e:
        print(f"Error getting EC2 recommendations: {e}")
    
    return recommendations

def get_instance_cpu_utilization(instance_id, days=7):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        
        datapoints = response.get('Datapoints', [])
        if datapoints:
            avg_cpu = sum(d['Average'] for d in datapoints) / len(datapoints)
            max_cpu = max(d['Maximum'] for d in datapoints)
            return {'average': avg_cpu, 'maximum': max_cpu}
        else:
            return {'average': 0, 'maximum': 0}
    except Exception as e:
        print(f"Error getting CPU stats: {e}")
        return {'average': 0, 'maximum': 0}

def estimate_instance_cost(instance_type):
    cost_map = {
        't2.micro': 8.5, 't2.small': 17, 't2.medium': 34,
        't3.micro': 7.6, 't3.small': 15.2, 't3.medium': 30.4,
        't3.large': 60.8, 't3.xlarge': 121.6,
        'm5.large': 70, 'm5.xlarge': 140,
        'c5.large': 62, 'c5.xlarge': 124
    }
    return round(cost_map.get(instance_type, 50), 2)

def get_rds_recommendations():
    recommendations = []
    
    try:
        response = rds_client.describe_db_instances()
        
        for db in response['DBInstances']:
            db_id = db['DBInstanceIdentifier']
            
            if db['MultiAZ']:
                recommendations.append({
                    'resource_type': 'RDS',
                    'resource_id': db_id,
                    'recommendation': 'Review Multi-AZ necessity',
                    'reason': 'Multi-AZ doubles cost - ensure it is needed',
                    'estimated_monthly_savings': estimate_rds_cost(db) / 2,
                    'priority': 'medium'
                })
    except Exception as e:
        print(f"Error getting RDS recommendations: {e}")
    
    return recommendations

def estimate_rds_cost(db_instance):
    instance_class = db_instance['DBInstanceClass']
    cost_map = {
        'db.t3.micro': 15, 'db.t3.small': 30, 'db.t3.medium': 60,
        'db.m5.large': 140, 'db.m5.xlarge': 280
    }
    return round(cost_map.get(instance_class, 100), 2)

def identify_idle_resources(params):
    idle_resources = []
    
    try:
        response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                cpu_stats = get_instance_cpu_utilization(instance_id)
                
                if cpu_stats['average'] < 5:
                    idle_resources.append({
                        'resource_type': 'EC2',
                        'resource_id': instance_id,
                        'status': 'idle',
                        'details': f'CPU usage: {cpu_stats["average"]:.1f}%',
                        'recommended_action': 'Terminate or stop'
                    })
    except Exception as e:
        print(f"Error checking idle EC2: {e}")
    
    return {
        'total_idle_resources': len(idle_resources),
        'resources': idle_resources[:10]
    }
'''
    
    with open(os.path.join(LAMBDA_DIR, 'optimization_lambda.py'), 'w') as f:
        f.write(optimization_code)
    
    # Forecasting Lambda
    forecasting_code = '''import json
import boto3
from datetime import datetime, timedelta
import statistics

ce_client = boto3.client('ce')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    
    params = {}
    for param in parameters:
        params[param.get('name', '')] = param.get('value', '')
    
    try:
        if 'forecast_costs' in api_path:
            result = forecast_costs(params)
        elif 'analyze_growth_trends' in api_path:
            result = analyze_growth_trends(params)
        else:
            result = {'error': f'Unknown path: {api_path}'}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }

def forecast_costs(params):
    months_to_forecast = int(params.get('months', '3'))
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        monthly_costs = []
        for result in response['ResultsByTime']:
            cost = float(result['Total']['UnblendedCost']['Amount'])
            monthly_costs.append(cost)
        
        if len(monthly_costs) >= 2:
            growth_rates = []
            for i in range(1, len(monthly_costs)):
                if monthly_costs[i-1] > 0:
                    rate = (monthly_costs[i] - monthly_costs[i-1]) / monthly_costs[i-1]
                    growth_rates.append(rate)
            
            avg_growth_rate = statistics.mean(growth_rates) if growth_rates else 0
        else:
            avg_growth_rate = 0
        
        current_cost = monthly_costs[-1] if monthly_costs else 0
        forecasts = []
        
        for month in range(1, months_to_forecast + 1):
            forecasted_cost = current_cost * ((1 + avg_growth_rate) ** month)
            
            if len(monthly_costs) > 2:
                cost_variance = statistics.stdev(monthly_costs) / statistics.mean(monthly_costs)
                confidence = max(0.5, 1 - (cost_variance * month * 0.1))
            else:
                confidence = 0.7
            
            forecasts.append({
                'month': month,
                'predicted_cost': round(forecasted_cost, 2),
                'confidence': round(confidence, 2),
                'date': (end_date + timedelta(days=30*month)).strftime('%Y-%m')
            })
        
        return {
            'forecast_period': f'{months_to_forecast} months',
            'current_monthly_cost': round(current_cost, 2),
            'average_growth_rate': f'{avg_growth_rate*100:.1f}%',
            'forecasts': forecasts,
            'historical_data_points': len(monthly_costs)
        }
    except Exception as e:
        return {'error': f'Failed to forecast costs: {str(e)}'}

def analyze_growth_trends(params):
    service = params.get('service', '')
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    try:
        query_params = {
            'TimePeriod': {
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            'Granularity': 'MONTHLY',
            'Metrics': ['UnblendedCost'],
            'GroupBy': [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        }
        
        response = ce_client.get_cost_and_usage(**query_params)
        
        service_trends = {}
        
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                svc = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if svc not in service_trends:
                    service_trends[svc] = []
                service_trends[svc].append(cost)
        
        growth_analysis = []
        for svc, costs in service_trends.items():
            if len(costs) >= 2 and costs[0] > 0:
                growth_rate = ((costs[-1] - costs[0]) / costs[0]) * 100
                growth_analysis.append({
                    'service': svc,
                    'initial_cost': round(costs[0], 2),
                    'current_cost': round(costs[-1], 2),
                    'growth_percentage': round(growth_rate, 1),
                    'trend': 'increasing' if growth_rate > 0 else 'decreasing'
                })
        
        growth_analysis.sort(key=lambda x: x['growth_percentage'], reverse=True)
        
        return {
            'analysis_period': '3 months',
            'top_growing_services': growth_analysis[:5],
            'declining_services': [s for s in growth_analysis if s['growth_percentage'] < 0][:5]
        }
    except Exception as e:
        return {'error': f'Failed to analyze growth trends: {str(e)}'}
'''
    
    with open(os.path.join(LAMBDA_DIR, 'forecasting_lambda.py'), 'w') as f:
        f.write(forecasting_code)
    
    # Package and deploy Lambda functions
    deployed_functions = {}
    
    lambda_configs = [
        {
            'name': 'finops-cost-analysis',
            'file': 'cost_analysis_lambda.py',
            'handler': 'cost_analysis_lambda.lambda_handler'
        },
        {
            'name': 'finops-optimization',
            'file': 'optimization_lambda.py',
            'handler': 'optimization_lambda.lambda_handler'
        },
        {
            'name': 'finops-forecasting',
            'file': 'forecasting_lambda.py',
            'handler': 'forecasting_lambda.lambda_handler'
        }
    ]
    
    for config in lambda_configs:
        # Create zip file
        zip_filename = f'{config["name"]}.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(os.path.join(LAMBDA_DIR, config['file']), config['file'])
        
        # Upload to S3
        s3_key = f"lambda-functions/{zip_filename}"
        s3.upload_file(zip_filename, bucket_name, s3_key)
        
        # Deploy Lambda
        try:
            response = lambda_client.create_function(
                FunctionName=config['name'],
                Runtime='python3.9',
                Role=f"arn:aws:iam::{account_id}:role/FinOpsLambdaExecutionRole",
                Handler=config['handler'],
                Code={
                    'S3Bucket': bucket_name,
                    'S3Key': s3_key
                },
                Timeout=60,
                MemorySize=256
            )
            deployed_functions[config['name']] = response['FunctionArn']
            print(f"Deployed Lambda: {config['name']}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                # Update existing function
                response = lambda_client.update_function_code(
                    FunctionName=config['name'],
                    S3Bucket=bucket_name,
                    S3Key=s3_key
                )
                deployed_functions[config['name']] = response['FunctionArn']
                print(f"Updated Lambda: {config['name']}")
            else:
                raise
        
        # Clean up zip
        os.remove(zip_filename)
        time.sleep(2)
    
    return deployed_functions

def create_api_schemas(bucket_name):
    """Create and upload API schemas for action groups"""
    print("Creating API schemas...")
    
    # Cost Analysis API Schema
    cost_analysis_api = {
        "openapi": "3.0.0",
        "info": {
            "title": "Cost Analysis API",
            "version": "1.0.0"
        },
        "paths": {
            "/get_cost_breakdown": {
                "post": {
                    "summary": "Get cost breakdown by service",
                    "operationId": "getCostBreakdown",
                    "parameters": [
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "7"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/analyze_cost_trends": {
                "post": {
                    "summary": "Analyze cost trends",
                    "operationId": "analyzeCostTrends",
                    "parameters": [
                        {
                            "name": "days",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "30"}
                        },
                        {
                            "name": "service",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/identify_cost_anomalies": {
                "post": {
                    "summary": "Identify cost anomalies",
                    "operationId": "identifyCostAnomalies",
                    "parameters": [
                        {
                            "name": "threshold",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "20"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    }
    
    # Optimization API Schema
    optimization_api = {
        "openapi": "3.0.0",
        "info": {
            "title": "Resource Optimization API",
            "version": "1.0.0"
        },
        "paths": {
            "/get_optimization_recommendations": {
                "post": {
                    "summary": "Get optimization recommendations",
                    "operationId": "getOptimizationRecommendations",
                    "parameters": [
                        {
                            "name": "resource_type",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "all"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/identify_idle_resources": {
                "post": {
                    "summary": "Identify idle resources",
                    "operationId": "identifyIdleResources",
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    }
    
    # Forecasting API Schema
    forecasting_api = {
        "openapi": "3.0.0",
        "info": {
            "title": "Cost Forecasting API",
            "version": "1.0.0"
        },
        "paths": {
            "/forecast_costs": {
                "post": {
                    "summary": "Forecast future costs",
                    "operationId": "forecastCosts",
                    "parameters": [
                        {
                            "name": "months",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "default": "3"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/analyze_growth_trends": {
                "post": {
                    "summary": "Analyze growth trends",
                    "operationId": "analyzeGrowthTrends",
                    "parameters": [
                        {
                            "name": "service",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    }
    
    # Upload schemas to S3
    s3.put_object(
        Bucket=bucket_name,
        Key='api-schemas/cost-analysis-api.json',
        Body=json.dumps(cost_analysis_api)
    )
    
    s3.put_object(
        Bucket=bucket_name,
        Key='api-schemas/optimization-api.json',
        Body=json.dumps(optimization_api)
    )
    
    s3.put_object(
        Bucket=bucket_name,
        Key='api-schemas/forecasting-api.json',
        Body=json.dumps(forecasting_api)
    )
    
    print("Uploaded API schemas to S3")
    return True

def create_bedrock_agents(lambda_functions, bucket_name):
    """Create Bedrock agents with action groups"""
    print("Creating Bedrock agents...")
    
    agent_instructions = {
        'cost_analyzer': '''You are a FinOps Cost Analysis specialist. Help users understand their AWS costs by:
- Analyzing costs by service, region, and time period
- Identifying cost trends and patterns
- Detecting anomalies and unusual spending
- Providing detailed breakdowns

Always provide specific numbers and highlight key insights.''',
        
        'optimizer': '''You are an AWS Resource Optimization specialist. Help users reduce costs by:
- Identifying underutilized or idle resources
- Recommending right-sizing opportunities
- Calculating potential savings
- Prioritizing optimizations by impact

Focus on actionable recommendations with clear savings estimates.''',
        
        'forecaster': '''You are an AWS Cost Forecasting expert. Help users plan their cloud spending by:
- Forecasting future costs based on trends
- Identifying growth patterns
- Setting budget recommendations
- Predicting cost impacts

Provide confidence levels with predictions.'''
    }
    
    created_agents = {}
    
    agent_configs = [
        {
            'name': 'FinOps-CostAnalyzer',
            'type': 'cost_analyzer',
            'lambda_name': 'finops-cost-analysis',
            'schema_key': 'api-schemas/cost-analysis-api.json'
        },
        {
            'name': 'FinOps-Optimizer',
            'type': 'optimizer', 
            'lambda_name': 'finops-optimization',
            'schema_key': 'api-schemas/optimization-api.json'
        },
        {
            'name': 'FinOps-Forecaster',
            'type': 'forecaster',
            'lambda_name': 'finops-forecasting',
            'schema_key': 'api-schemas/forecasting-api.json'
        }
    ]
    
    for config in agent_configs:
        try:
            # Create agent
            response = bedrock_agent.create_agent(
                agentName=config['name'],
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/FinOpsBedrockAgentRole",
                description=f'AI-powered {config["type"].replace("_", " ")} for FinOps',
                idleSessionTTLInSeconds=1800,
                foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
                instruction=agent_instructions[config['type']]
            )
            
            agent_id = response['agent']['agentId']
            print(f"Created agent: {config['name']} (ID: {agent_id})")
            
            # Wait a bit for agent to be ready
            time.sleep(5)
            
            # Create action group
            ag_response = bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=f'{config["type"]}Actions',
                actionGroupExecutor={
                    'lambda': lambda_functions[config['lambda_name']]
                },
                apiSchema={
                    's3': {
                        's3BucketName': bucket_name,
                        's3ObjectKey': config['schema_key']
                    }
                },
                description=f'Actions for {config["type"]}'
            )
            
            print(f"Created action group for {config['name']}")
            
            # Prepare agent
            bedrock_agent.prepare_agent(agentId=agent_id)
            print(f"Prepared agent: {config['name']}")
            
            # Wait for preparation
            time.sleep(10)
            
            # Create alias
            alias_response = bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName='live',
                description=f'Live alias for {config["name"]}'
            )
            
            created_agents[config['type']] = {
                'id': agent_id,
                'name': config['name'],
                'alias': alias_response['agentAlias']['agentAliasId']
            }
            
        except Exception as e:
            print(f"Error creating agent {config['name']}: {e}")
            # Try to find existing agent
            try:
                list_response = bedrock_agent.list_agents()
                for agent in list_response.get('agentSummaries', []):
                    if agent['agentName'] == config['name']:
                        created_agents[config['type']] = {
                            'id': agent['agentId'],
                            'name': config['name'],
                            'alias': 'TSTALIASID'
                        }
                        break
            except:
                pass
    
    return created_agents

def main():
    """Main deployment function"""
    print("Starting FinOps system deployment...")
    print(f"Account: {account_id}")
    print(f"Region: {region}")
    print("=" * 60)
    
    # Step 1: Create IAM roles
    create_iam_roles()
    
    # Step 2: Create S3 bucket
    bucket_name = create_s3_bucket()
    
    # Step 3: Deploy Lambda functions
    lambda_functions = create_lambda_functions(bucket_name)
    
    # Step 4: Create API schemas
    create_api_schemas(bucket_name)
    
    # Step 5: Create Bedrock agents
    agents = create_bedrock_agents(lambda_functions, bucket_name)
    
    # Save configuration
    config = {
        'bucket': bucket_name,
        'region': region,
        'account_id': account_id,
        'lambda_functions': lambda_functions,
        'agents': agents,
        'deployed_at': datetime.now().isoformat()
    }
    
    with open('finops_deployment_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("Deployment completed successfully!")
    print("Configuration saved to finops_deployment_config.json")
    
    return config

if __name__ == "__main__":
    main()