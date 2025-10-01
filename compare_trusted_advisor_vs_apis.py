#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare AWS Trusted Advisor cost findings with direct API calls for resource usage
Shows the difference between using Trusted Advisor vs manual API scanning
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import time

def get_trusted_advisor_cost_findings():
    """Get cost optimization findings from Trusted Advisor"""
    print("\n=== TRUSTED ADVISOR COST FINDINGS ===")
    
    support = boto3.client('support', region_name='us-east-1')
    findings = {
        'low_utilization_ec2': [],
        'idle_rds': [],
        'unattached_volumes': [],
        'unused_eips': [],
        'total_monthly_savings': 0
    }
    
    try:
        # Get all available checks
        checks_response = support.describe_trusted_advisor_checks(language='en')
        
        # Key cost optimization check IDs
        cost_check_ids = {
            'Low Utilization Amazon EC2 Instances': 'Qch7DwouX1',
            'Idle Load Balancers': 'hjLMh88uM8',
            'Unassociated Elastic IP Addresses': 'Z4AUBRNSmz',
            'Underutilized Amazon EBS Volumes': 'DAvU99Dc4C',
            'Amazon RDS Idle DB Instances': 'Ti39halfu8'
        }
        
        for check_name, check_id in cost_check_ids.items():
            try:
                result = support.describe_trusted_advisor_check_result(
                    checkId=check_id,
                    language='en'
                )
                
                if result['result']['status'] in ['warning', 'error']:
                    resources = result['result']['flaggedResources']
                    
                    for resource in resources:
                        metadata = resource.get('metadata', [])
                        
                        if check_name == 'Low Utilization Amazon EC2 Instances' and len(metadata) > 13:
                            findings['low_utilization_ec2'].append({
                                'instance_id': metadata[1],
                                'instance_type': metadata[3],
                                'region': metadata[0],
                                'average_cpu': float(metadata[11]) if metadata[11] else 0,
                                'estimated_monthly_savings': float(metadata[13]) if metadata[13] else 0
                            })
                            findings['total_monthly_savings'] += float(metadata[13]) if metadata[13] else 0
                        
                        elif check_name == 'Unassociated Elastic IP Addresses' and len(metadata) > 1:
                            findings['unused_eips'].append({
                                'eip': metadata[1],
                                'region': metadata[0],
                                'monthly_cost': 3.6  # $0.005/hour
                            })
                            findings['total_monthly_savings'] += 3.6
                        
                        elif check_name == 'Underutilized Amazon EBS Volumes' and len(metadata) > 6:
                            findings['unattached_volumes'].append({
                                'volume_id': metadata[1],
                                'region': metadata[0],
                                'size_gb': int(metadata[3]) if metadata[3] else 0,
                                'monthly_savings': float(metadata[6]) if metadata[6] else 0
                            })
                            findings['total_monthly_savings'] += float(metadata[6]) if metadata[6] else 0
                        
                        elif check_name == 'Amazon RDS Idle DB Instances' and len(metadata) > 8:
                            findings['idle_rds'].append({
                                'db_instance': metadata[1],
                                'region': metadata[0],
                                'multi_az': metadata[3],
                                'instance_type': metadata[4],
                                'storage_gb': metadata[5],
                                'days_since_last_connection': int(metadata[7]) if metadata[7] else 0,
                                'estimated_monthly_savings': float(metadata[8]) if metadata[8] else 0
                            })
                            findings['total_monthly_savings'] += float(metadata[8]) if metadata[8] else 0
                
                print(f"✅ Checked: {check_name} - Found {len(resources)} issues")
                
            except Exception as e:
                print(f"❌ Error checking {check_name}: {str(e)}")
        
        # Summary
        print(f"\n📊 TRUSTED ADVISOR SUMMARY:")
        print(f"  - Low utilization EC2: {len(findings['low_utilization_ec2'])} instances")
        print(f"  - Idle RDS instances: {len(findings['idle_rds'])} databases")
        print(f"  - Unattached EBS volumes: {len(findings['unattached_volumes'])} volumes")
        print(f"  - Unused Elastic IPs: {len(findings['unused_eips'])} IPs")
        print(f"  💰 Total Monthly Savings: ${findings['total_monthly_savings']:,.2f}")
        
    except Exception as e:
        print(f"❌ Error accessing Trusted Advisor: {e}")
    
    return findings


def get_direct_api_cost_findings():
    """Get cost optimization findings using direct AWS API calls"""
    print("\n=== DIRECT API COST FINDINGS ===")
    
    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')
    rds = boto3.client('rds')
    
    findings = {
        'low_utilization_ec2': [],
        'idle_rds': [],
        'unattached_volumes': [],
        'unused_eips': [],
        'stopped_instances': [],
        'total_monthly_savings': 0
    }
    
    # 1. Check EC2 instances for low utilization
    print("\n🔍 Scanning EC2 instances...")
    try:
        instances = ec2.describe_instances()
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running':
                    instance_id = instance['InstanceId']
                    
                    # Get CPU metrics
                    cpu_response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Average']
                    )
                    
                    if cpu_response['Datapoints']:
                        avg_cpu = sum(d['Average'] for d in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
                        
                        if avg_cpu < 10:  # Less than 10% utilization
                            # Estimate cost based on instance type
                            instance_costs = {
                                't2.micro': 8.5, 't2.small': 17, 't2.medium': 34,
                                't3.micro': 7.5, 't3.small': 15, 't3.medium': 30,
                                'm5.large': 70, 'm5.xlarge': 140,
                                'c5.large': 62, 'c5.xlarge': 124
                            }
                            monthly_cost = instance_costs.get(instance['InstanceType'], 50)
                            savings = monthly_cost * 0.5  # Assume 50% savings from rightsizing
                            
                            findings['low_utilization_ec2'].append({
                                'instance_id': instance_id,
                                'instance_type': instance['InstanceType'],
                                'region': instance['Placement']['AvailabilityZone'][:-1],
                                'average_cpu': round(avg_cpu, 2),
                                'estimated_monthly_savings': savings
                            })
                            findings['total_monthly_savings'] += savings
                
                elif instance['State']['Name'] == 'stopped':
                    # Calculate storage cost for stopped instances
                    storage_gb = sum(8 for _ in instance.get('BlockDeviceMappings', []))  # Simplified
                    monthly_cost = storage_gb * 0.10
                    
                    findings['stopped_instances'].append({
                        'instance_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'storage_gb': storage_gb,
                        'monthly_cost': monthly_cost
                    })
                    findings['total_monthly_savings'] += monthly_cost
        
        print(f"  ✅ Found {len(findings['low_utilization_ec2'])} underutilized EC2 instances")
        print(f"  ✅ Found {len(findings['stopped_instances'])} stopped EC2 instances")
        
    except Exception as e:
        print(f"  ❌ Error scanning EC2: {e}")
    
    # 2. Check unattached EBS volumes
    print("\n🔍 Scanning EBS volumes...")
    try:
        volumes = ec2.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        
        for volume in volumes['Volumes']:
            monthly_cost = volume['Size'] * 0.10  # $0.10/GB/month
            
            findings['unattached_volumes'].append({
                'volume_id': volume['VolumeId'],
                'size_gb': volume['Size'],
                'region': volume['AvailabilityZone'][:-1],
                'monthly_savings': monthly_cost
            })
            findings['total_monthly_savings'] += monthly_cost
        
        print(f"  ✅ Found {len(findings['unattached_volumes'])} unattached volumes")
        
    except Exception as e:
        print(f"  ❌ Error scanning volumes: {e}")
    
    # 3. Check unused Elastic IPs
    print("\n🔍 Scanning Elastic IPs...")
    try:
        addresses = ec2.describe_addresses()
        
        for address in addresses['Addresses']:
            if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                monthly_cost = 3.6  # $0.005/hour * 720 hours
                
                findings['unused_eips'].append({
                    'eip': address['PublicIp'],
                    'region': 'global',
                    'monthly_cost': monthly_cost
                })
                findings['total_monthly_savings'] += monthly_cost
        
        print(f"  ✅ Found {len(findings['unused_eips'])} unused Elastic IPs")
        
    except Exception as e:
        print(f"  ❌ Error scanning EIPs: {e}")
    
    # 4. Check RDS instances
    print("\n🔍 Scanning RDS instances...")
    try:
        db_instances = rds.describe_db_instances()
        
        for db in db_instances['DBInstances']:
            # Check if DB has low connections (simplified check)
            # In reality, you'd check CloudWatch metrics for DatabaseConnections
            
            # For demo, we'll flag any db.t2.micro or db.t3.micro as potentially idle
            if 'micro' in db['DBInstanceClass']:
                # Estimate monthly cost
                monthly_cost = 15 if 'micro' in db['DBInstanceClass'] else 30
                
                findings['idle_rds'].append({
                    'db_instance': db['DBInstanceIdentifier'],
                    'region': db['AvailabilityZone'][:-1] if db.get('AvailabilityZone') else 'unknown',
                    'instance_type': db['DBInstanceClass'],
                    'storage_gb': db['AllocatedStorage'],
                    'estimated_monthly_savings': monthly_cost
                })
                findings['total_monthly_savings'] += monthly_cost
        
        print(f"  ✅ Found {len(findings['idle_rds'])} potentially idle RDS instances")
        
    except Exception as e:
        print(f"  ❌ Error scanning RDS: {e}")
    
    # Summary
    print(f"\n📊 DIRECT API SUMMARY:")
    print(f"  - Low utilization EC2: {len(findings['low_utilization_ec2'])} instances")
    print(f"  - Stopped EC2: {len(findings['stopped_instances'])} instances")
    print(f"  - Idle RDS instances: {len(findings['idle_rds'])} databases")
    print(f"  - Unattached EBS volumes: {len(findings['unattached_volumes'])} volumes")
    print(f"  - Unused Elastic IPs: {len(findings['unused_eips'])} IPs")
    print(f"  💰 Total Monthly Savings: ${findings['total_monthly_savings']:,.2f}")
    
    return findings


def compare_findings(ta_findings: Dict, api_findings: Dict):
    """Compare Trusted Advisor findings with direct API findings"""
    print("\n=== COMPARISON ANALYSIS ===")
    
    print("\n📊 Finding Count Comparison:")
    print(f"{'Finding Type':<30} {'Trusted Advisor':>20} {'Direct API':>20} {'Difference':>15}")
    print("-" * 85)
    
    finding_types = [
        ('Low Utilization EC2', 'low_utilization_ec2'),
        ('Idle RDS Instances', 'idle_rds'),
        ('Unattached EBS Volumes', 'unattached_volumes'),
        ('Unused Elastic IPs', 'unused_eips')
    ]
    
    for display_name, key in finding_types:
        ta_count = len(ta_findings.get(key, []))
        api_count = len(api_findings.get(key, []))
        diff = api_count - ta_count
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        
        print(f"{display_name:<30} {ta_count:>20} {api_count:>20} {diff_str:>15}")
    
    # Note: Direct API also finds stopped instances which TA doesn't report as a separate category
    if 'stopped_instances' in api_findings:
        print(f"{'Stopped EC2 Instances':<30} {'N/A':>20} {len(api_findings['stopped_instances']):>20} {'+' + str(len(api_findings['stopped_instances'])):>15}")
    
    print(f"\n{'Total Monthly Savings':<30} ${ta_findings['total_monthly_savings']:>19,.2f} ${api_findings['total_monthly_savings']:>19,.2f} ${(api_findings['total_monthly_savings'] - ta_findings['total_monthly_savings']):>14,.2f}")
    
    print("\n🔍 Analysis:")
    print("\n✅ TRUSTED ADVISOR ADVANTAGES:")
    print("  • Pre-calculated savings estimates based on AWS pricing")
    print("  • Includes complex checks (Reserved Instance optimization, etc.)")
    print("  • Considers multiple factors (CPU, Network, Disk I/O)")
    print("  • No additional API calls needed")
    print("  • Checks run automatically every 5 minutes")
    
    print("\n✅ DIRECT API ADVANTAGES:")
    print("  • Real-time data (not cached)")
    print("  • Customizable thresholds")
    print("  • Can find additional issues (e.g., stopped instances)")
    print("  • No support plan required")
    print("  • More granular control over checks")
    
    print("\n💡 RECOMMENDATION:")
    print("  Use Trusted Advisor as the primary source for cost optimization")
    print("  Supplement with direct API calls for:")
    print("    - Real-time checks")
    print("    - Custom thresholds")
    print("    - Additional checks not covered by TA")


def main():
    print("=" * 100)
    print("AWS TRUSTED ADVISOR vs DIRECT API COMPARISON")
    print("Comparing cost optimization findings")
    print("=" * 100)
    
    # Get findings from both sources
    ta_findings = get_trusted_advisor_cost_findings()
    time.sleep(1)  # Brief pause
    api_findings = get_direct_api_cost_findings()
    
    # Compare results
    compare_findings(ta_findings, api_findings)
    
    print("\n" + "=" * 100)
    print("COMPARISON COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()