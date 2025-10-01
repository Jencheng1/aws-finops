import json
import boto3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
ce = boto3.client('ce')
dynamodb = boto3.resource('dynamodb')
rds = boto3.client('rds')
elb = boto3.client('elb')
elbv2 = boto3.client('elbv2')

def lambda_handler(event, context):
    """
    Lambda function to find idle and underutilized resources
    """
    try:
        user_id = event.get('user_id', 'anonymous')
        session_id = event.get('session_id', str(datetime.now().timestamp()))
        scan_days = event.get('scan_days', 30)
        
        # Thread-safe results collection
        results_lock = threading.Lock()
        idle_resources = {
            'ec2_instances': [],
            'ebs_volumes': [],
            'elastic_ips': [],
            'rds_instances': [],
            'load_balancers': [],
            'total_monthly_waste': 0
        }
        
        # Scan functions
        def scan_ec2_instances():
            """Find stopped and underutilized EC2 instances"""
            instances = ec2.describe_instances()
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    state = instance['State']['Name']
                    
                    if state == 'stopped':
                        # Calculate storage cost for stopped instance
                        volumes = instance.get('BlockDeviceMappings', [])
                        total_storage = sum(
                            v.get('Ebs', {}).get('VolumeSize', 0) 
                            for v in volumes if 'Ebs' in v
                        )
                        monthly_cost = total_storage * 0.10  # $0.10/GB/month
                        
                        with results_lock:
                            idle_resources['ec2_instances'].append({
                                'resource_id': instance_id,
                                'type': 'Stopped EC2 Instance',
                                'instance_type': instance['InstanceType'],
                                'name': next((tag['Value'] for tag in instance.get('Tags', []) 
                                            if tag['Key'] == 'Name'), 'Unnamed'),
                                'state': state,
                                'storage_gb': total_storage,
                                'monthly_cost': monthly_cost,
                                'launch_time': instance.get('LaunchTime', '').isoformat() if 'LaunchTime' in instance else 'N/A',
                                'recommendation': 'Terminate or create AMI and terminate'
                            })
                            idle_resources['total_monthly_waste'] += monthly_cost
                            
                    elif state == 'running':
                        # Check CPU utilization for running instances
                        end_time = datetime.utcnow()
                        start_time = end_time - timedelta(days=scan_days)
                        
                        try:
                            cpu_stats = cloudwatch.get_metric_statistics(
                                Namespace='AWS/EC2',
                                MetricName='CPUUtilization',
                                Dimensions=[
                                    {'Name': 'InstanceId', 'Value': instance_id}
                                ],
                                StartTime=start_time,
                                EndTime=end_time,
                                Period=3600,
                                Statistics=['Average']
                            )
                            
                            if cpu_stats['Datapoints']:
                                avg_cpu = sum(d['Average'] for d in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
                                
                                if avg_cpu < 10:  # Less than 10% CPU usage
                                    # Get instance cost
                                    instance_cost = get_instance_monthly_cost(instance['InstanceType'])
                                    
                                    with results_lock:
                                        idle_resources['ec2_instances'].append({
                                            'resource_id': instance_id,
                                            'type': 'Underutilized EC2 Instance',
                                            'instance_type': instance['InstanceType'],
                                            'name': next((tag['Value'] for tag in instance.get('Tags', []) 
                                                        if tag['Key'] == 'Name'), 'Unnamed'),
                                            'avg_cpu_utilization': f"{avg_cpu:.1f}%",
                                            'monthly_cost': instance_cost,
                                            'recommendation': 'Downsize or terminate'
                                        })
                                        idle_resources['total_monthly_waste'] += instance_cost * 0.5  # 50% potential savings
                                        
                        except Exception as e:
                            print(f"Error checking CPU for {instance_id}: {e}")
        
        def scan_ebs_volumes():
            """Find unattached EBS volumes"""
            volumes = ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )
            
            for volume in volumes['Volumes']:
                volume_id = volume['VolumeId']
                size = volume['Size']
                volume_type = volume['VolumeType']
                
                # Calculate monthly cost based on volume type
                cost_per_gb = {
                    'gp3': 0.08,
                    'gp2': 0.10,
                    'io1': 0.125,
                    'io2': 0.125,
                    'st1': 0.045,
                    'sc1': 0.025
                }
                
                monthly_cost = size * cost_per_gb.get(volume_type, 0.10)
                
                with results_lock:
                    idle_resources['ebs_volumes'].append({
                        'resource_id': volume_id,
                        'type': 'Unattached EBS Volume',
                        'size_gb': size,
                        'volume_type': volume_type,
                        'monthly_cost': monthly_cost,
                        'created': volume['CreateTime'].isoformat(),
                        'recommendation': 'Delete or create snapshot and delete'
                    })
                    idle_resources['total_monthly_waste'] += monthly_cost
        
        def scan_elastic_ips():
            """Find unassociated Elastic IPs"""
            addresses = ec2.describe_addresses()
            
            for address in addresses['Addresses']:
                if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                    monthly_cost = 0.005 * 24 * 30  # $0.005 per hour
                    
                    with results_lock:
                        idle_resources['elastic_ips'].append({
                            'resource_id': address.get('AllocationId', 'N/A'),
                            'type': 'Unassociated Elastic IP',
                            'public_ip': address.get('PublicIp', 'N/A'),
                            'monthly_cost': monthly_cost,
                            'recommendation': 'Release the Elastic IP'
                        })
                        idle_resources['total_monthly_waste'] += monthly_cost
        
        def scan_rds_instances():
            """Find idle RDS instances"""
            db_instances = rds.describe_db_instances()
            
            for db in db_instances['DBInstances']:
                db_id = db['DBInstanceIdentifier']
                
                # Check database connections
                try:
                    connection_stats = cloudwatch.get_metric_statistics(
                        Namespace='AWS/RDS',
                        MetricName='DatabaseConnections',
                        Dimensions=[
                            {'Name': 'DBInstanceIdentifier', 'Value': db_id}
                        ],
                        StartTime=datetime.utcnow() - timedelta(days=scan_days),
                        EndTime=datetime.utcnow(),
                        Period=3600,
                        Statistics=['Average']
                    )
                    
                    if connection_stats['Datapoints']:
                        avg_connections = sum(d['Average'] for d in connection_stats['Datapoints']) / len(connection_stats['Datapoints'])
                        
                        if avg_connections < 1:  # Less than 1 connection on average
                            # Estimate monthly cost
                            instance_class = db['DBInstanceClass']
                            monthly_cost = get_rds_monthly_cost(instance_class)
                            
                            with results_lock:
                                idle_resources['rds_instances'].append({
                                    'resource_id': db_id,
                                    'type': 'Idle RDS Instance',
                                    'instance_class': instance_class,
                                    'engine': db['Engine'],
                                    'avg_connections': f"{avg_connections:.1f}",
                                    'monthly_cost': monthly_cost,
                                    'recommendation': 'Stop, downsize, or switch to Aurora Serverless'
                                })
                                idle_resources['total_monthly_waste'] += monthly_cost
                                
                except Exception as e:
                    print(f"Error checking RDS {db_id}: {e}")
        
        # Execute scans in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(scan_ec2_instances),
                executor.submit(scan_ebs_volumes),
                executor.submit(scan_elastic_ips),
                executor.submit(scan_rds_instances)
            ]
            
            # Wait for all scans to complete
            for future in futures:
                future.result()
        
        # Store results in DynamoDB for feedback
        feedback_table = dynamodb.Table('FinOpsAIContext')
        feedback_table.put_item(
            Item={
                'context_id': f"optimization_{session_id}",
                'user_id': user_id,
                'scan_results': json.dumps(idle_resources, default=str),
                'total_resources_found': sum(len(v) for k, v in idle_resources.items() if isinstance(v, list)),
                'total_monthly_waste': idle_resources['total_monthly_waste'],
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(idle_resources, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_instance_monthly_cost(instance_type):
    """Estimate monthly cost for EC2 instance type"""
    # Simplified pricing (actual prices vary by region)
    hourly_prices = {
        't3.micro': 0.0104,
        't3.small': 0.0208,
        't3.medium': 0.0416,
        't3.large': 0.0832,
        'm5.large': 0.096,
        'm5.xlarge': 0.192,
        'm5.2xlarge': 0.384,
        'c5.large': 0.085,
        'c5.xlarge': 0.17
    }
    
    hourly_price = hourly_prices.get(instance_type, 0.10)  # Default if not found
    return hourly_price * 24 * 30

def get_rds_monthly_cost(instance_class):
    """Estimate monthly cost for RDS instance class"""
    hourly_prices = {
        'db.t3.micro': 0.017,
        'db.t3.small': 0.034,
        'db.t3.medium': 0.068,
        'db.m5.large': 0.171,
        'db.m5.xlarge': 0.342
    }
    
    hourly_price = hourly_prices.get(instance_class, 0.20)  # Default if not found
    return hourly_price * 24 * 30