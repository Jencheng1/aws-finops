#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get detailed EC2 instance information with costs and real-time usage
"""

import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

def get_ec2_instance_details_with_costs(days_lookback: int = 7) -> Tuple[pd.DataFrame, Dict]:
    """
    Get comprehensive EC2 instance details including costs and real-time usage
    """
    ec2 = boto3.client('ec2')
    ce = boto3.client('ce')
    cloudwatch = boto3.client('cloudwatch')
    
    # Get all EC2 instances
    instances_response = ec2.describe_instances()
    
    instance_data = []
    total_monthly_cost = 0
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_lookback)
    
    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            state = instance['State']['Name']
            
            # Get instance name from tags
            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) 
                                if tag['Key'] == 'Name'), 'No Name')
            
            # Get cost data for this specific instance
            try:
                cost_response = ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost'],
                    Filter={
                        'Dimensions': {
                            'Key': 'RESOURCE_ID',
                            'Values': [f"arn:aws:ec2:{instance['Placement']['AvailabilityZone'][:-1]}:{instance['OwnerId']}:instance/{instance_id}"]
                        }
                    }
                )
                
                # Calculate total cost for the period
                instance_cost = sum(float(result['Total']['UnblendedCost']['Amount']) 
                                  for result in cost_response['ResultsByTime'])
                
                # Estimate monthly cost
                daily_avg = instance_cost / days_lookback if days_lookback > 0 else 0
                monthly_cost = daily_avg * 30
                
            except:
                # Fallback cost estimation based on instance type
                instance_costs = {
                    't2.micro': 8.5, 't2.small': 17, 't2.medium': 34,
                    't3.micro': 7.5, 't3.small': 15, 't3.medium': 30,
                    't3a.micro': 6.8, 't3a.small': 13.5, 't3a.medium': 27,
                    'm5.large': 70, 'm5.xlarge': 140, 'm5.2xlarge': 280,
                    'c5.large': 62, 'c5.xlarge': 124, 'c5.2xlarge': 248
                }
                monthly_cost = instance_costs.get(instance_type, 50)
                instance_cost = monthly_cost / 30 * days_lookback
            
            # Get CPU utilization metrics if instance is running
            cpu_avg = 0
            cpu_max = 0
            if state == 'running':
                try:
                    cpu_stats = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_date,
                        EndTime=end_date,
                        Period=3600,
                        Statistics=['Average', 'Maximum']
                    )
                    
                    if cpu_stats['Datapoints']:
                        cpu_avg = sum(dp['Average'] for dp in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
                        cpu_max = max(dp['Maximum'] for dp in cpu_stats['Datapoints'])
                except:
                    pass
            
            # Get network metrics
            network_in = 0
            network_out = 0
            if state == 'running':
                try:
                    # Network In
                    net_in = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='NetworkIn',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_date,
                        EndTime=end_date,
                        Period=86400,  # Daily
                        Statistics=['Sum']
                    )
                    if net_in['Datapoints']:
                        network_in = sum(dp['Sum'] for dp in net_in['Datapoints']) / 1024 / 1024  # Convert to MB
                    
                    # Network Out
                    net_out = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='NetworkOut',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_date,
                        EndTime=end_date,
                        Period=86400,
                        Statistics=['Sum']
                    )
                    if net_out['Datapoints']:
                        network_out = sum(dp['Sum'] for dp in net_out['Datapoints']) / 1024 / 1024
                except:
                    pass
            
            # Calculate storage
            storage_gb = sum(vol.get('Ebs', {}).get('VolumeSize', 8) 
                           for vol in instance.get('BlockDeviceMappings', []))
            
            instance_data.append({
                'Instance ID': instance_id,
                'Name': instance_name,
                'Type': instance_type,
                'State': state,
                'Region': instance['Placement']['AvailabilityZone'][:-1],
                'AZ': instance['Placement']['AvailabilityZone'],
                'Platform': instance.get('Platform', 'Linux'),
                'Launch Time': instance.get('LaunchTime', '').strftime('%Y-%m-%d %H:%M') if instance.get('LaunchTime') else '',
                'CPU Avg %': round(cpu_avg, 1),
                'CPU Max %': round(cpu_max, 1),
                'Network In (MB)': round(network_in, 1),
                'Network Out (MB)': round(network_out, 1),
                'Storage (GB)': storage_gb,
                f'{days_lookback}d Cost': round(instance_cost, 2),
                'Monthly Cost': round(monthly_cost, 2),
                'Annual Cost': round(monthly_cost * 12, 2),
                'Optimization': 'Underutilized' if cpu_avg < 10 and state == 'running' else 
                               'Stop to save' if state == 'stopped' else 'OK'
            })
            
            total_monthly_cost += monthly_cost
    
    # Create DataFrame
    df = pd.DataFrame(instance_data)
    
    # Sort by monthly cost descending
    df = df.sort_values('Monthly Cost', ascending=False)
    
    # Summary statistics
    summary = {
        'total_instances': len(df),
        'running_instances': len(df[df['State'] == 'running']),
        'stopped_instances': len(df[df['State'] == 'stopped']),
        'total_monthly_cost': round(total_monthly_cost, 2),
        'total_annual_cost': round(total_monthly_cost * 12, 2),
        'underutilized_count': len(df[df['Optimization'] == 'Underutilized']),
        'potential_monthly_savings': round(
            df[df['Optimization'].isin(['Underutilized', 'Stop to save'])]['Monthly Cost'].sum() * 0.5, 2
        )
    }
    
    return df, summary


def main():
    """Demo the EC2 details function"""
    print("Fetching EC2 instance details with costs and usage...")
    
    df, summary = get_ec2_instance_details_with_costs(days_lookback=7)
    
    print("\n=== EC2 INSTANCE SUMMARY ===")
    print(f"Total Instances: {summary['total_instances']}")
    print(f"Running: {summary['running_instances']}")
    print(f"Stopped: {summary['stopped_instances']}")
    print(f"Total Monthly Cost: ${summary['total_monthly_cost']:,.2f}")
    print(f"Total Annual Cost: ${summary['total_annual_cost']:,.2f}")
    print(f"Underutilized Instances: {summary['underutilized_count']}")
    print(f"Potential Monthly Savings: ${summary['potential_monthly_savings']:,.2f}")
    
    print("\n=== TOP 10 INSTANCES BY COST ===")
    print(df[['Instance ID', 'Name', 'Type', 'State', 'CPU Avg %', 'Monthly Cost', 'Optimization']].head(10))
    
    # Save to CSV
    df.to_csv('ec2_instance_details.csv', index=False)
    print("\nDetailed data saved to ec2_instance_details.csv")


if __name__ == "__main__":
    main()