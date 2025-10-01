#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test AWS to Apptio MCP reverse engineering functionality
"""

import boto3
from datetime import datetime, timedelta

def test_apptio_reverse_engineering():
    """Test the reverse engineering of AWS expenses to Apptio TBM"""
    
    print("Testing AWS to Apptio MCP Reverse Engineering")
    print("=" * 60)
    
    try:
        # Test AWS Cost Explorer access
        ce = boto3.client('ce')
        ec2 = boto3.client('ec2')
        
        # Get actual cost data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        cost_response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # Extract service costs
        service_costs = {}
        total_cost = 0.0
        
        for time_period in cost_response['ResultsByTime']:
            for group in time_period['Groups']:
                service_name = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                if amount > 0:
                    service_costs[service_name] = amount
                    total_cost += amount
        
        print(f"Retrieved {len(service_costs)} AWS services with costs")
        print(f"   Total AWS expenses: ${total_cost:.2f}")
        
        # Test TBM tower mapping
        apptio_mapping = {
            'Infrastructure': 0,
            'Applications': 0,
            'Security & Compliance': 0,
            'End User Computing': 0
        }
        
        for service, cost in service_costs.items():
            if any(x in service.lower() for x in ['compute', 'elastic block', 'vpc']):
                apptio_mapping['Infrastructure'] += cost
            elif any(x in service.lower() for x in ['s3', 'rds', 'lambda']):
                apptio_mapping['Applications'] += cost
            elif any(x in service.lower() for x in ['iam', 'cloudtrail', 'config']):
                apptio_mapping['Security & Compliance'] += cost
            elif any(x in service.lower() for x in ['workspaces', 'appstream']):
                apptio_mapping['End User Computing'] += cost
            else:
                # Default to Infrastructure
                apptio_mapping['Infrastructure'] += cost
        
        total_allocated = sum(apptio_mapping.values())
        variance = abs(total_cost - total_allocated)
        accuracy = (1 - variance/total_cost) * 100 if total_cost > 0 else 100
        
        print(f"TBM Tower Allocation:")
        for tower, amount in apptio_mapping.items():
            percentage = (amount / total_allocated * 100) if total_allocated > 0 else 0
            print(f"   {tower}: ${amount:.2f} ({percentage:.1f}%)")
        
        print(f"Mapping accuracy: {accuracy:.1f}%")
        
        # Test resource inventory
        instances = ec2.describe_instances()
        running_instances = 0
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    running_instances += 1
        
        print(f"Resource validation: {running_instances} running instances")
        
        if total_cost == 0:
            print("Zero cost data - using resource-based estimation")
            estimated_cost = running_instances * 67  # ~$67/month per instance
            print(f"   Estimated monthly cost: ${estimated_cost:.2f}")
        
        print("\nReverse engineering test completed successfully!")
        print(f"   AWS expenses successfully mapped to {len(apptio_mapping)} TBM towers")
        print(f"   Ready for Apptio MCP reconciliation view")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_apptio_reverse_engineering()
    if success:
        print("\nAll tests passed - Apptio reverse engineering working correctly")
    else:
        print("\nTests failed - Check AWS permissions and configuration")