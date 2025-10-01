#!/usr/bin/env python3
"""
Verify EC2 drill-down functionality
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing EC2 drill-down components...")
print("-" * 50)

# Test 1: Check if EC2 utility is available
print("\n1. Checking EC2 utility availability:")
try:
    from get_ec2_details_with_costs import get_ec2_instance_details_with_costs
    print("✅ EC2 utility is available")
    
    # Test getting instance details
    print("\n2. Testing EC2 instance retrieval:")
    df_instances, summary = get_ec2_instance_details_with_costs(days_lookback=7)
    
    print(f"✅ Found {summary['total_instances']} EC2 instances")
    print(f"   - Running: {summary['running_instances']}")
    print(f"   - Stopped: {summary['stopped_instances']}")
    print(f"   - Monthly Cost: ${summary['total_monthly_cost']:,.2f}")
    
    if not df_instances.empty:
        print("\n3. Sample instance data:")
        print(df_instances[['Instance ID', 'Name', 'State', 'Monthly Cost']].head(3).to_string(index=False))
        
except ImportError as e:
    print(f"❌ EC2 utility not available: {e}")
except Exception as e:
    print(f"❌ Error testing EC2 utility: {e}")

# Test 2: Check Cost Explorer grouping
print("\n\n4. Testing Cost Explorer EC2 grouping:")
try:
    import boto3
    from datetime import datetime, timedelta
    
    ce_client = boto3.client('ce')
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
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
    
    # Count usage types
    usage_types = set()
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            usage_types.add(group['Keys'][0])
    
    print(f"✅ Found {len(usage_types)} EC2 usage types")
    print("   Sample usage types:", list(usage_types)[:5])
    
except Exception as e:
    print(f"❌ Error testing Cost Explorer: {e}")

print("\n\n✅ EC2 drill-down verification complete!")
print("\nThe dashboard should now:")
print("1. Show EC2 usage type breakdown from Cost Explorer")
print("2. Display detailed EC2 instance information with metrics")
print("3. Allow filtering by state, type, and optimization status")
print("4. Provide CSV export functionality")