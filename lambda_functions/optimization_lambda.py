import json
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
