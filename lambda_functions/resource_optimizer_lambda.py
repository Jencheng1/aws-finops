import json
import boto3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

def lambda_handler(event, context):
    """
    Lambda function for resource optimization scanning
    """
    # Extract parameters
    scan_days = event.get('scan_days', 7)
    user_id = event.get('user_id', 'unknown')
    session_id = event.get('session_id', str(datetime.now().timestamp()))
    
    try:
        # Initialize clients
        ec2 = boto3.client('ec2')
        cloudwatch = boto3.client('cloudwatch')
        
        # Results container
        optimization_results = {
            'stopped_instances': [],
            'unattached_volumes': [],
            'unused_eips': [],
            'underutilized_instances': [],
            'total_monthly_savings': 0.0
        }
        
        # 1. Find stopped EC2 instances
        instances_response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['stopped']}
            ]
        )
        
        for reservation in instances_response['Reservations']:
            for instance in reservation['Instances']:
                # Calculate storage cost for stopped instance
                storage_gb = 0
                for bdm in instance.get('BlockDeviceMappings', []):
                    if 'Ebs' in bdm and 'VolumeId' in bdm['Ebs']:
                        try:
                            vol_response = ec2.describe_volumes(
                                VolumeIds=[bdm['Ebs']['VolumeId']]
                            )
                            if vol_response['Volumes']:
                                storage_gb += vol_response['Volumes'][0]['Size']
                        except:
                            pass
                
                monthly_cost = storage_gb * 0.10  # $0.10/GB/month
                
                optimization_results['stopped_instances'].append({
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'launch_time': instance['LaunchTime'].isoformat(),
                    'storage_gb': storage_gb,
                    'monthly_cost': round(monthly_cost, 2),
                    'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                })
                
                optimization_results['total_monthly_savings'] += monthly_cost
        
        # 2. Find unattached EBS volumes
        volumes_response = ec2.describe_volumes(
            Filters=[
                {'Name': 'status', 'Values': ['available']}
            ]
        )
        
        for volume in volumes_response['Volumes']:
            monthly_cost = volume['Size'] * 0.10  # $0.10/GB/month
            
            optimization_results['unattached_volumes'].append({
                'volume_id': volume['VolumeId'],
                'size_gb': volume['Size'],
                'volume_type': volume['VolumeType'],
                'create_time': volume['CreateTime'].isoformat(),
                'monthly_cost': round(monthly_cost, 2),
                'availability_zone': volume['AvailabilityZone']
            })
            
            optimization_results['total_monthly_savings'] += monthly_cost
        
        # 3. Find unused Elastic IPs
        addresses_response = ec2.describe_addresses()
        
        for address in addresses_response['Addresses']:
            if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                monthly_cost = 0.005 * 24 * 30  # $0.005/hour
                
                optimization_results['unused_eips'].append({
                    'allocation_id': address.get('AllocationId', 'N/A'),
                    'public_ip': address['PublicIp'],
                    'monthly_cost': round(monthly_cost, 2)
                })
                
                optimization_results['total_monthly_savings'] += monthly_cost
        
        # 4. Find underutilized running instances (simplified check)
        running_instances = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        # Check CPU utilization for running instances
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=scan_days)
        
        for reservation in running_instances['Reservations']:
            for instance in reservation['Instances']:
                try:
                    cpu_stats = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[
                            {
                                'Name': 'InstanceId',
                                'Value': instance['InstanceId']
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Average']
                    )
                    
                    if cpu_stats['Datapoints']:
                        avg_cpu = sum(dp['Average'] for dp in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
                        
                        if avg_cpu < 10:  # Less than 10% average CPU
                            optimization_results['underutilized_instances'].append({
                                'instance_id': instance['InstanceId'],
                                'instance_type': instance['InstanceType'],
                                'avg_cpu_percent': round(avg_cpu, 2),
                                'recommendation': 'Consider downsizing or consolidating'
                            })
                except:
                    pass
        
        # Round total savings
        optimization_results['total_monthly_savings'] = round(
            optimization_results['total_monthly_savings'], 2
        )
        
        # Add summary
        optimization_results['summary'] = {
            'stopped_instances_count': len(optimization_results['stopped_instances']),
            'unattached_volumes_count': len(optimization_results['unattached_volumes']),
            'unused_eips_count': len(optimization_results['unused_eips']),
            'underutilized_instances_count': len(optimization_results['underutilized_instances']),
            'total_resources': sum([
                len(optimization_results['stopped_instances']),
                len(optimization_results['unattached_volumes']),
                len(optimization_results['unused_eips']),
                len(optimization_results['underutilized_instances'])
            ])
        }
        
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'optimization_results': optimization_results,
                'metadata': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'scan_days': scan_days,
                    'scan_timestamp': datetime.now().isoformat()
                }
            })
        }
        
    except Exception as e:
        result = {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to complete resource optimization scan'
            })
        }
    
    return result