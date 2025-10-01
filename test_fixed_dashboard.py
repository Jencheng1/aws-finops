#!/usr/bin/env python3
"""
Test the fixed EC2 drill-down functionality
"""

import boto3
import pandas as pd
from datetime import datetime, timedelta

# Test getting EC2 costs through Cost Explorer
ce_client = boto3.client('ce')

end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

# Get EC2 costs by usage type
response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date.strftime('%Y-%m-%d'),
        'End': end_date.strftime('%Y-%m-%d')
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    Filter={
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['AmazonEC2']
        }
    },
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}]
)

print("EC2 Costs by Usage Type:")
print("-" * 50)

usage_costs = {}
for result in response['ResultsByTime']:
    for group in result['Groups']:
        usage_type = group['Keys'][0]
        cost = float(group['Metrics']['UnblendedCost']['Amount'])
        if usage_type not in usage_costs:
            usage_costs[usage_type] = 0
        usage_costs[usage_type] += cost

# Sort by cost
sorted_usage = sorted(usage_costs.items(), key=lambda x: x[1], reverse=True)
for usage, cost in sorted_usage[:10]:
    print(f"{usage}: ${cost:.2f}")

# Test EC2 instance details utility
try:
    from get_ec2_details_with_costs import get_ec2_instance_details_with_costs
    print("\n\nEC2 Instance Details:")
    print("-" * 50)
    
    df_instances, summary = get_ec2_instance_details_with_costs(days_lookback=7)
    
    print(f"Total instances: {summary['total_instances']}")
    print(f"Running: {summary['running_instances']}")
    print(f"Stopped: {summary['stopped_instances']}")
    print(f"Monthly cost: ${summary['total_monthly_cost']:,.2f}")
    
    if not df_instances.empty:
        print("\nInstance Details:")
        print(df_instances[['Instance ID', 'Name', 'Type', 'State', 'Monthly Cost']].to_string(index=False))
        
except Exception as e:
    print(f"\nError loading EC2 details utility: {str(e)}")