import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class EC2CostAnalyzer:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.cost_explorer_client = boto3.client('ce')
        
    def analyze_instance_utilization(self, instance_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """Analyze EC2 instance utilization over the specified period"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            utilization_data = {}
            
            for instance_id in instance_ids:
                # Get CPU utilization metrics
                cpu_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Average', 'Maximum']
                )
                
                # Calculate average CPU utilization
                cpu_values = [point['Average'] for point in cpu_response['Datapoints']]
                avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
                max_cpu = max([point['Maximum'] for point in cpu_response['Datapoints']]) if cpu_response['Datapoints'] else 0
                
                utilization_data[instance_id] = {
                    'avg_cpu': avg_cpu,
                    'max_cpu': max_cpu,
                    'data_points': len(cpu_values)
                }
            
            return utilization_data
            
        except Exception as e:
            logger.error(f"Error analyzing instance utilization: {str(e)}")
            return {}
    
    def get_instance_details(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Get detailed information about EC2 instances"""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=instance_ids)
            
            instances_info = {}
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instances_info[instance_id] = {
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'availability_zone': instance['Placement']['AvailabilityZone'],
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId')
                    }
            
            return instances_info
            
        except Exception as e:
            logger.error(f"Error getting instance details: {str(e)}")
            return {}
    
    def get_instance_costs(self, instance_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """Get cost information for specific instances"""
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
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
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
            
            return {
                'total_cost': total_cost,
                'daily_costs': daily_costs,
                'average_daily_cost': total_cost / days if days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting instance costs: {str(e)}")
            return {}
    
    def identify_optimization_opportunities(self, utilization_data: Dict[str, Any], 
                                         instances_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify cost optimization opportunities based on utilization data"""
        opportunities = []
        
        for instance_id, utilization in utilization_data.items():
            instance_info = instances_info.get(instance_id, {})
            instance_type = instance_info.get('instance_type', 'unknown')
            
            # Check for underutilized instances (avg CPU < 20%)
            if utilization['avg_cpu'] < 20:
                opportunities.append({
                    'type': 'right_sizing',
                    'instance_id': instance_id,
                    'instance_type': instance_type,
                    'current_avg_cpu': utilization['avg_cpu'],
                    'recommendation': 'Consider downsizing to a smaller instance type',
                    'priority': 'high' if utilization['avg_cpu'] < 10 else 'medium',
                    'estimated_savings_percent': 30 if utilization['avg_cpu'] < 10 else 20
                })
            
            # Check for idle instances (max CPU < 5% over the period)
            if utilization['max_cpu'] < 5:
                opportunities.append({
                    'type': 'idle_instance',
                    'instance_id': instance_id,
                    'instance_type': instance_type,
                    'max_cpu': utilization['max_cpu'],
                    'recommendation': 'Consider stopping or terminating this idle instance',
                    'priority': 'high',
                    'estimated_savings_percent': 100
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
        
        return opportunities

def lambda_handler(event, context):
    """AWS Lambda handler for EC2 cost analysis"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize the analyzer
        analyzer = EC2CostAnalyzer()
        
        # Extract parameters from the event
        action = event.get('action', 'analyze_all')
        instance_ids = event.get('instance_ids', [])
        days = event.get('days', 30)
        
        # If no specific instances provided, get all running instances
        if not instance_ids:
            try:
                ec2_response = analyzer.ec2_client.describe_instances(
                    Filters=[
                        {
                            'Name': 'instance-state-name',
                            'Values': ['running']
                        }
                    ]
                )
                
                instance_ids = []
                for reservation in ec2_response['Reservations']:
                    for instance in reservation['Instances']:
                        instance_ids.append(instance['InstanceId'])
                        
            except Exception as e:
                logger.error(f"Error getting running instances: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Failed to retrieve running instances',
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
                    # Estimate savings based on average daily cost
                    daily_cost = cost_data.get('average_daily_cost', 0) / len(instance_ids)
                    monthly_savings = daily_cost * 30 * (opp['estimated_savings_percent'] / 100)
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
