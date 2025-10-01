#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test EC2 Cost Explorer API to understand why instance details aren't showing
"""

import boto3
from datetime import datetime, timedelta
import json

def test_ec2_cost_grouping():
    ce = boto3.client('ce')
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print("Testing EC2 Cost Explorer API grouping options...")
    print("=" * 80)
    
    # Test different grouping options
    grouping_tests = [
        ('RESOURCE_ID', 'Resource ID (Instance-level)'),
        ('USAGE_TYPE', 'Usage Type'),
        ('INSTANCE_TYPE', 'Instance Type'),
        ('LINKED_ACCOUNT', 'Linked Account')
    ]
    
    for group_key, description in grouping_tests:
        print(f"\n{description} Grouping:")
        print("-" * 40)
        
        try:
            response = ce.get_cost_and_usage(
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
                GroupBy=[{'Type': 'DIMENSION', 'Key': group_key}]
            )
            
            # Collect all unique groups and their total costs
            groups = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    key = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    if key not in groups:
                        groups[key] = 0
                    groups[key] += cost
            
            # Show top 10 by cost
            sorted_groups = sorted(groups.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if sorted_groups:
                print(f"✅ Success! Found {len(groups)} unique items")
                print("Top 10 by cost:")
                for i, (name, cost) in enumerate(sorted_groups):
                    # Truncate long names
                    display_name = name[:60] + '...' if len(name) > 60 else name
                    print(f"  {i+1:2d}. {display_name:<65} ${cost:>8.2f}")
                    
                    # Check if this looks like an instance ID
                    if group_key == 'RESOURCE_ID' and name.startswith('i-'):
                        print(f"      ^ This is an EC2 instance ID!")
            else:
                print("❌ No data found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            
    # Test with tags
    print("\n\nTesting Tag-based grouping:")
    print("-" * 40)
    
    try:
        # First, enable cost allocation tags if needed
        response = ce.get_cost_and_usage(
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
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'TAG', 'Key': 'Name'}  # Try grouping by Name tag
            ]
        )
        print("✅ Tag grouping works! You can group by instance Name tags.")
        
    except Exception as e:
        if 'not enabled' in str(e):
            print("⚠️ Cost allocation tags not enabled. Enable 'Name' tag in Cost Management Console.")
        else:
            print(f"❌ Tag grouping error: {str(e)}")

    # Test filters
    print("\n\nTesting EC2 instance type filters:")
    print("-" * 40)
    
    try:
        # Get costs filtered by running instances
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            Filter={
                'And': [
                    {
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': ['AmazonEC2']
                        }
                    },
                    {
                        'Dimensions': {
                            'Key': 'USAGE_TYPE_GROUP',
                            'Values': ['EC2: Running Hours']
                        }
                    }
                ]
            },
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}]
        )
        
        print("✅ Can filter for EC2 Running Hours")
        
        # Show instance types
        instance_types = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                itype = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                hours = float(group['Metrics']['UsageQuantity'].get('Amount', 0))
                if itype not in instance_types:
                    instance_types[itype] = {'cost': 0, 'hours': 0}
                instance_types[itype]['cost'] += cost
                instance_types[itype]['hours'] += hours
        
        if instance_types:
            print("\nEC2 Instance Types (Running Hours):")
            for itype, data in sorted(instance_types.items(), key=lambda x: x[1]['cost'], reverse=True)[:5]:
                print(f"  • {itype}: ${data['cost']:.2f} ({data['hours']:.1f} hours)")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("1. If RESOURCE_ID grouping doesn't show instance IDs:")
    print("   - This might be a permissions issue")
    print("   - Or Cost Explorer hasn't processed instance-level data yet")
    print("   - Or the account doesn't have detailed billing enabled")
    print("\n2. Alternative approaches:")
    print("   - Use EC2 API to list instances + CloudWatch for metrics")
    print("   - Enable cost allocation tags for 'Name' tag")
    print("   - Use AWS Cost and Usage Report (CUR) for detailed data")


if __name__ == "__main__":
    test_ec2_cost_grouping()