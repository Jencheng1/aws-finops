#!/usr/bin/env python3
"""
Check actual AWS resources to verify optimizer is working correctly
"""

import boto3
from datetime import datetime

print("Checking Actual AWS Resources")
print("=" * 60)

# Initialize clients
ec2 = boto3.client('ec2')

# 1. Check EBS Volumes
print("\n1. EBS VOLUMES:")
print("-" * 40)
try:
    volumes = ec2.describe_volumes()
    
    all_volumes = volumes['Volumes']
    unattached = [v for v in all_volumes if v['State'] == 'available']
    attached = [v for v in all_volumes if v['State'] == 'in-use']
    
    print(f"Total EBS Volumes: {len(all_volumes)}")
    print(f"Attached (in-use): {len(attached)}")
    print(f"Unattached (available): {len(unattached)}")
    
    if unattached:
        print("\nUnattached Volumes Details:")
        for vol in unattached:
            print(f"  - Volume ID: {vol['VolumeId']}")
            print(f"    Size: {vol['Size']} GB")
            print(f"    Type: {vol['VolumeType']}")
            print(f"    Created: {vol['CreateTime']}")
            print(f"    Monthly Cost: ~${vol['Size'] * 0.10:.2f}")
            print()
    
except Exception as e:
    print(f"Error checking volumes: {e}")

# 2. Check Elastic IPs
print("\n2. ELASTIC IPs:")
print("-" * 40)
try:
    eips = ec2.describe_addresses()
    
    all_eips = eips['Addresses']
    associated = [e for e in all_eips if 'AssociationId' in e]
    unassociated = [e for e in all_eips if 'AssociationId' not in e]
    
    print(f"Total Elastic IPs: {len(all_eips)}")
    print(f"Associated: {len(associated)}")
    print(f"Unassociated (unused): {len(unassociated)}")
    
    if unassociated:
        print("\nUnassociated EIPs Details:")
        for eip in unassociated:
            print(f"  - Allocation ID: {eip['AllocationId']}")
            print(f"    Public IP: {eip['PublicIp']}")
            print(f"    Domain: {eip.get('Domain', 'standard')}")
            print(f"    Monthly Cost: ~$3.60 (when not attached)")
            print()
    
except Exception as e:
    print(f"Error checking EIPs: {e}")

# 3. Check EC2 Instances
print("\n3. EC2 INSTANCES:")
print("-" * 40)
try:
    instances = ec2.describe_instances()
    
    all_instances = []
    stopped_instances = []
    running_instances = []
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            all_instances.append(instance)
            if instance['State']['Name'] == 'stopped':
                stopped_instances.append(instance)
            elif instance['State']['Name'] == 'running':
                running_instances.append(instance)
    
    print(f"Total EC2 Instances: {len(all_instances)}")
    print(f"Running: {len(running_instances)}")
    print(f"Stopped: {len(stopped_instances)}")
    
    if stopped_instances:
        print("\nStopped Instances (still incur storage costs):")
        for inst in stopped_instances:
            name = next((tag['Value'] for tag in inst.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            print(f"  - {inst['InstanceId']} ({name})")
            print(f"    Type: {inst['InstanceType']}")
            print(f"    Storage Cost: ~$5-10/month")
    
except Exception as e:
    print(f"Error checking instances: {e}")

# 4. Check for orphaned snapshots
print("\n4. EBS SNAPSHOTS:")
print("-" * 40)
try:
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])
    
    all_snapshots = snapshots['Snapshots']
    print(f"Total Snapshots: {len(all_snapshots)}")
    
    # Check for snapshots of non-existent volumes
    volume_ids = [v['VolumeId'] for v in volumes['Volumes']]
    orphaned = [s for s in all_snapshots if s.get('VolumeId') and s['VolumeId'] not in volume_ids]
    
    if orphaned:
        print(f"Orphaned Snapshots (volume deleted): {len(orphaned)}")
        total_size = sum(s.get('VolumeSize', 0) for s in orphaned)
        print(f"Total Size: {total_size} GB")
        print(f"Monthly Cost: ~${total_size * 0.05:.2f}")
    
except Exception as e:
    print(f"Error checking snapshots: {e}")

print("\n" + "=" * 60)
print("Resource check complete!")
print("\nIf unattached volumes or unused EIPs exist above,")
print("the optimizer should find them.")