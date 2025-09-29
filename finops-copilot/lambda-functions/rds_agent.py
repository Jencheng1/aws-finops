import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class RDSCostAnalyzer:
    def __init__(self):
        self.rds_client = boto3.client('rds')
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.cost_explorer_client = boto3.client('ce')
        
    def analyze_instance_utilization(self, instance_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """Analyze RDS instance utilization over the specified period"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            utilization_data = {}
            
            for instance_id in instance_ids:
                # Get CPU utilization metrics
                cpu_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Average', 'Maximum']
                )
                
                # Get database connections
                connections_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='DatabaseConnections',
                    Dimensions=[
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Average', 'Maximum']
                )
                
                # Get read IOPS
                read_iops_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='ReadIOPS',
                    Dimensions=[
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average', 'Maximum']
                )
                
                # Get write IOPS
                write_iops_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='WriteIOPS',
                    Dimensions=[
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average', 'Maximum']
                )
                
                # Calculate average metrics
                cpu_values = [point['Average'] for point in cpu_response['Datapoints']]
                avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
                max_cpu = max([point['Maximum'] for point in cpu_response['Datapoints']]) if cpu_response['Datapoints'] else 0
                
                connection_values = [point['Average'] for point in connections_response['Datapoints']]
                avg_connections = sum(connection_values) / len(connection_values) if connection_values else 0
                max_connections = max([point['Maximum'] for point in connections_response['Datapoints']]) if connections_response['Datapoints'] else 0
                
                read_iops_values = [point['Average'] for point in read_iops_response['Datapoints']]
                avg_read_iops = sum(read_iops_values) / len(read_iops_values) if read_iops_values else 0
                
                write_iops_values = [point['Average'] for point in write_iops_response['Datapoints']]
                avg_write_iops = sum(write_iops_values) / len(write_iops_values) if write_iops_values else 0
                
                utilization_data[instance_id] = {
                    'avg_cpu': avg_cpu,
                    'max_cpu': max_cpu,
                    'avg_connections': avg_connections,
                    'max_connections': max_connections,
                    'avg_read_iops': avg_read_iops,
                    'avg_write_iops': avg_write_iops,
                    'data_points': len(cpu_values)
                }
            
            return utilization_data
            
        except Exception as e:
            logger.error(f"Error analyzing RDS instance utilization: {str(e)}")
            return {}
    
    def get_instance_details(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Get detailed information about RDS instances"""
        try:
            instances_info = {}
            
            for instance_id in instance_ids:
                try:
                    response = self.rds_client.describe_db_instances(
                        DBInstanceIdentifier=instance_id
                    )
                    
                    if response['DBInstances']:
                        instance = response['DBInstances'][0]
                        instances_info[instance_id] = {
                            'instance_class': instance['DBInstanceClass'],
                            'engine': instance['Engine'],
                            'engine_version': instance['EngineVersion'],
                            'allocated_storage': instance['AllocatedStorage'],
                            'storage_type': instance['StorageType'],
                            'multi_az': instance['MultiAZ'],
                            'status': instance['DBInstanceStatus'],
                            'availability_zone': instance['AvailabilityZone'],
                            'tags': {tag['Key']: tag['Value'] for tag in instance.get('TagList', [])},
                            'backup_retention_period': instance.get('BackupRetentionPeriod', 0),
                            'storage_encrypted': instance.get('StorageEncrypted', False),
                            'creation_time': instance['InstanceCreateTime'].isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error getting details for instance {instance_id}: {str(e)}")
                    instances_info[instance_id] = {'error': str(e)}
            
            return instances_info
            
        except Exception as e:
            logger.error(f"Error getting RDS instance details: {str(e)}")
            return {}
    
    def get_instance_costs(self, instance_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """Get cost information for specific RDS instances"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get cost data from Cost Explorer
            response = self.cost_explorer_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Relational Database Service']
                    }
                }
            )
            
            # Process cost data
            total_cost = 0
            daily_costs = []
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                if result['Groups']:
                    cost = float(result['Groups'][0]['Metrics']['BlendedCost']['Amount'])
                    total_cost += cost
                    daily_costs.append({'date': date, 'cost': cost})
            
            # Estimate per-instance cost (simple division)
            per_instance_cost = total_cost / len(instance_ids) if instance_ids else 0
            
            return {
                'total_cost': total_cost,
                'daily_costs': daily_costs,
                'average_daily_cost': total_cost / days if days > 0 else 0,
                'estimated_per_instance_cost': per_instance_cost
            }
            
        except Exception as e:
            logger.error(f"Error getting RDS instance costs: {str(e)}")
            return {}
    
    def identify_optimization_opportunities(self, utilization_data: Dict[str, Any], 
                                         instances_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify cost optimization opportunities based on utilization data"""
        opportunities = []
        
        for instance_id, utilization in utilization_data.items():
            instance_info = instances_info.get(instance_id, {})
            
            if 'error' in instance_info:
                continue
                
            instance_class = instance_info.get('instance_class', 'unknown')
            multi_az = instance_info.get('multi_az', False)
            
            # Check for underutilized instances (avg CPU < 20%)
            if utilization['avg_cpu'] < 20:
                opportunities.append({
                    'type': 'right_sizing',
                    'instance_id': instance_id,
                    'instance_class': instance_class,
                    'current_avg_cpu': utilization['avg_cpu'],
                    'recommendation': 'Consider downsizing to a smaller instance class',
                    'priority': 'high' if utilization['avg_cpu'] < 10 else 'medium',
                    'estimated_savings_percent': 30 if utilization['avg_cpu'] < 10 else 20
                })
            
            # Check for idle instances (no connections and low CPU)
            if utilization['avg_connections'] < 1 and utilization['max_cpu'] < 5:
                opportunities.append({
                    'type': 'idle_instance',
                    'instance_id': instance_id,
                    'instance_class': instance_class,
                    'avg_connections': utilization['avg_connections'],
                    'max_cpu': utilization['max_cpu'],
                    'recommendation': 'Consider stopping or terminating this idle database instance',
                    'priority': 'high',
                    'estimated_savings_percent': 100
                })
            
            # Check for Multi-AZ deployments with low utilization
            if multi_az and utilization['avg_cpu'] < 30:
                opportunities.append({
                    'type': 'multi_az_optimization',
                    'instance_id': instance_id,
                    'recommendation': 'Consider switching to single-AZ deployment for non-critical low-utilization databases',
                    'priority': 'medium',
                    'estimated_savings_percent': 50
                })
            
            # Check for low IOPS instances that could use burstable performance
            if (utilization['avg_read_iops'] + utilization['avg_write_iops']) < 100:
                if not instance_class.startswith('db.t'):
                    opportunities.append({
                        'type': 'burstable_instance',
                        'instance_id': instance_id,
                        'current_class': instance_class,
                        'avg_total_iops': utilization['avg_read_iops'] + utilization['avg_write_iops'],
                        'recommendation': 'Consider switching to burstable performance instance (db.t3/db.t4g)',
                        'priority': 'medium',
                        'estimated_savings_percent': 25
                    })
            
            # Check for instances without proper tagging
            tags = instance_info.get('tags', {})
            required_tags = ['Environment', 'Owner', 'Project']
            missing_tags = [tag for tag in required_tags if tag not in tags]
            
            if missing_tags:
                opportunities.append({
                    'type': 'tagging_compliance',
                    'instance_id': instance_id,
                    'missing_tags': missing_tags,
                    'recommendation': f'Add missing tags: {", ".join(missing_tags)}',
                    'priority': 'low'
                })
            
            # Check backup retention
            backup_retention = instance_info.get('backup_retention_period', 0)
            if backup_retention > 7:
                opportunities.append({
                    'type': 'backup_optimization',
                    'instance_id': instance_id,
                    'current_retention_days': backup_retention,
                    'recommendation': 'Consider reducing backup retention period for non-critical databases',
                    'priority': 'low',
                    'estimated_savings_percent': 5
                })
        
        return opportunities

def lambda_handler(event, context):
    """AWS Lambda handler for RDS cost analysis"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize the analyzer
        analyzer = RDSCostAnalyzer()
        
        # Extract parameters from the event
        action = event.get('action', 'analyze_all')
        instance_ids = event.get('instance_ids', [])
        days = event.get('days', 30)
        
        # If no specific instances provided, get all running instances
        if not instance_ids:
            try:
                rds_response = analyzer.rds_client.describe_db_instances()
                instance_ids = []
                for instance in rds_response['DBInstances']:
                    if instance['DBInstanceStatus'] == 'available':
                        instance_ids.append(instance['DBInstanceIdentifier'])
                        
            except Exception as e:
                logger.error(f"Error getting RDS instances: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Failed to retrieve RDS instances',
                        'details': str(e)
                    })
                }
        
        # Perform analysis based on action
        if action == 'analyze_utilization':
            utilization_data = analyzer.analyze_instance_utilization(instance_ids, days)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'utilization_data': utilization_data,
                    'instance_count': len(instance_ids),
                    'analysis_period_days': days
                })
            }
            
        elif action == 'get_recommendations':
            # Get comprehensive analysis
            utilization_data = analyzer.analyze_instance_utilization(instance_ids, days)
            instances_info = analyzer.get_instance_details(instance_ids)
            cost_data = analyzer.get_instance_costs(instance_ids, days)
            opportunities = analyzer.identify_optimization_opportunities(utilization_data, instances_info)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'recommendations': opportunities,
                    'cost_summary': cost_data,
                    'instance_count': len(instance_ids),
                    'analysis_period_days': days
                })
            }
            
        elif action == 'analyze_all':
            # Comprehensive analysis
            utilization_data = analyzer.analyze_instance_utilization(instance_ids, days)
            instances_info = analyzer.get_instance_details(instance_ids)
            cost_data = analyzer.get_instance_costs(instance_ids, days)
            opportunities = analyzer.identify_optimization_opportunities(utilization_data, instances_info)
            
            # Calculate potential savings
            total_potential_savings = 0
            high_priority_count = 0
            
            for opp in opportunities:
                if opp.get('estimated_savings_percent'):
                    # Estimate savings based on per-instance cost
                    per_instance_cost = cost_data.get('estimated_per_instance_cost', 0) / 30  # Daily cost
                    monthly_savings = per_instance_cost * 30 * (opp['estimated_savings_percent'] / 100)
                    total_potential_savings += monthly_savings
                    opp['estimated_monthly_savings'] = monthly_savings
                
                if opp.get('priority') == 'high':
                    high_priority_count += 1
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'summary': {
                        'instance_count': len(instance_ids),
                        'total_monthly_cost': cost_data.get('average_daily_cost', 0) * 30,
                        'potential_monthly_savings': total_potential_savings,
                        'high_priority_recommendations': high_priority_count,
                        'total_recommendations': len(opportunities)
                    },
                    'utilization_data': utilization_data,
                    'instances_info': instances_info,
                    'cost_data': cost_data,
                    'recommendations': opportunities,
                    'analysis_period_days': days
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'supported_actions': ['analyze_utilization', 'get_recommendations', 'analyze_all']
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'action': 'analyze_all',
        'days': 7
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))