#!/usr/bin/env python3
"""
AWS Lambda function for Resource Tag Compliance
Checks resources for required tags and generates compliance reports
"""

import json
import boto3
from datetime import datetime
from typing import Dict, List, Any

# Initialize AWS clients
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
resource_tagging = boto3.client('resourcegroupstaggingapi')

# Required tags for compliance
REQUIRED_TAGS = ['Environment', 'Owner', 'CostCenter', 'Project']

# DynamoDB table for storing compliance history
COMPLIANCE_TABLE = 'tag-compliance-history'

def lambda_handler(event, context):
    """
    Main Lambda handler for tag compliance checking
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Compliance report
    """
    
    # Determine action from event
    action = event.get('action', 'scan')
    
    if action == 'scan':
        # Perform compliance scan
        compliance_report = perform_compliance_scan()
        
        # Store results in DynamoDB
        store_compliance_results(compliance_report)
        
        # Send notifications for non-compliant resources
        if compliance_report['non_compliant_count'] > 0:
            send_compliance_notifications(compliance_report)
        
        return {
            'statusCode': 200,
            'body': json.dumps(compliance_report)
        }
        
    elif action == 'report':
        # Generate compliance report
        report_type = event.get('report_type', 'summary')
        report = generate_compliance_report(report_type)
        
        return {
            'statusCode': 200,
            'body': json.dumps(report)
        }
        
    elif action == 'remediate':
        # Auto-remediate missing tags (with default values)
        resource_arns = event.get('resource_arns', [])
        remediation_report = auto_remediate_tags(resource_arns)
        
        return {
            'statusCode': 200,
            'body': json.dumps(remediation_report)
        }
        
    elif action == 'get_resource':
        # Get specific resource compliance
        resource_arn = event.get('resource_arn')
        if not resource_arn:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'resource_arn is required'})
            }
        
        compliance = check_resource_compliance(resource_arn)
        
        return {
            'statusCode': 200,
            'body': json.dumps(compliance)
        }
    
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unknown action: {action}'})
        }

def perform_compliance_scan():
    """
    Perform comprehensive tag compliance scan across all resources
    
    Returns:
        Compliance report dictionary
    """
    print("Starting compliance scan...")
    
    compliant_resources = []
    non_compliant_resources = []
    resources_by_type = {}
    missing_tags_summary = {tag: 0 for tag in REQUIRED_TAGS}
    
    # Scan all resources using Resource Groups Tagging API
    try:
        paginator = resource_tagging.get_paginator('get_resources')
        
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                resource_arn = resource['ResourceARN']
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                
                # Check compliance
                missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
                resource_type = get_resource_type_from_arn(resource_arn)
                
                # Track by type
                if resource_type not in resources_by_type:
                    resources_by_type[resource_type] = {
                        'total': 0,
                        'compliant': 0,
                        'non_compliant': 0
                    }
                
                resources_by_type[resource_type]['total'] += 1
                
                if missing_tags:
                    # Non-compliant resource
                    non_compliant_resources.append({
                        'resource_arn': resource_arn,
                        'resource_type': resource_type,
                        'missing_tags': missing_tags,
                        'existing_tags': tags
                    })
                    
                    resources_by_type[resource_type]['non_compliant'] += 1
                    
                    # Update missing tags summary
                    for tag in missing_tags:
                        missing_tags_summary[tag] += 1
                else:
                    # Compliant resource
                    compliant_resources.append({
                        'resource_arn': resource_arn,
                        'resource_type': resource_type,
                        'tags': tags
                    })
                    
                    resources_by_type[resource_type]['compliant'] += 1
        
        # Additional specific resource scans
        # EC2 Instances
        ec2_compliance = scan_ec2_resources()
        non_compliant_resources.extend(ec2_compliance['non_compliant'])
        compliant_resources.extend(ec2_compliance['compliant'])
        
        # RDS Instances
        rds_compliance = scan_rds_resources()
        non_compliant_resources.extend(rds_compliance['non_compliant'])
        compliant_resources.extend(rds_compliance['compliant'])
        
        # S3 Buckets
        s3_compliance = scan_s3_resources()
        non_compliant_resources.extend(s3_compliance['non_compliant'])
        compliant_resources.extend(s3_compliance['compliant'])
        
    except Exception as e:
        print(f"Error during compliance scan: {str(e)}")
    
    # Calculate compliance metrics
    total_resources = len(compliant_resources) + len(non_compliant_resources)
    compliance_rate = (len(compliant_resources) / total_resources * 100) if total_resources > 0 else 100
    
    # Create compliance report
    compliance_report = {
        'scan_timestamp': datetime.utcnow().isoformat(),
        'total_resources': total_resources,
        'compliant_count': len(compliant_resources),
        'non_compliant_count': len(non_compliant_resources),
        'compliance_rate': compliance_rate,
        'resources_by_type': resources_by_type,
        'missing_tags_summary': missing_tags_summary,
        'required_tags': REQUIRED_TAGS,
        'non_compliant_resources': non_compliant_resources[:100],  # Limit to 100 for response size
        'summary': {
            'high_risk_resources': identify_high_risk_resources(non_compliant_resources),
            'cost_impact': estimate_cost_impact(non_compliant_resources)
        }
    }
    
    print(f"Compliance scan completed. Rate: {compliance_rate:.1f}%")
    
    return compliance_report

def scan_ec2_resources():
    """
    Scan EC2 resources for tag compliance
    
    Returns:
        Dictionary with compliant and non-compliant resources
    """
    compliant = []
    non_compliant = []
    
    try:
        # Scan EC2 instances
        instances = ec2.describe_instances()
        
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] != 'terminated':
                    instance_id = instance['InstanceId']
                    instance_arn = f"arn:aws:ec2:{instance['Placement']['AvailabilityZone'][:-1]}:{boto3.client('sts').get_caller_identity()['Account']}:instance/{instance_id}"
                    
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
                    
                    resource_info = {
                        'resource_arn': instance_arn,
                        'resource_type': 'ec2:instance',
                        'resource_id': instance_id,
                        'state': instance['State']['Name'],
                        'instance_type': instance.get('InstanceType', 'unknown')
                    }
                    
                    if missing_tags:
                        resource_info['missing_tags'] = missing_tags
                        resource_info['existing_tags'] = tags
                        non_compliant.append(resource_info)
                    else:
                        resource_info['tags'] = tags
                        compliant.append(resource_info)
        
        # Scan EBS volumes
        volumes = ec2.describe_volumes()
        
        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            volume_arn = f"arn:aws:ec2:{volume['AvailabilityZone']}:{boto3.client('sts').get_caller_identity()['Account']}:volume/{volume_id}"
            
            tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
            missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
            
            resource_info = {
                'resource_arn': volume_arn,
                'resource_type': 'ec2:volume',
                'resource_id': volume_id,
                'state': volume['State'],
                'size': volume['Size']
            }
            
            if missing_tags:
                resource_info['missing_tags'] = missing_tags
                resource_info['existing_tags'] = tags
                non_compliant.append(resource_info)
            else:
                resource_info['tags'] = tags
                compliant.append(resource_info)
                
    except Exception as e:
        print(f"Error scanning EC2 resources: {str(e)}")
    
    return {'compliant': compliant, 'non_compliant': non_compliant}

def scan_rds_resources():
    """
    Scan RDS resources for tag compliance
    
    Returns:
        Dictionary with compliant and non-compliant resources
    """
    compliant = []
    non_compliant = []
    
    try:
        # Scan RDS instances
        db_instances = rds.describe_db_instances()
        
        for db in db_instances['DBInstances']:
            db_arn = db['DBInstanceArn']
            db_id = db['DBInstanceIdentifier']
            
            # Get tags
            tags_response = rds.list_tags_for_resource(ResourceName=db_arn)
            tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
            missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
            
            resource_info = {
                'resource_arn': db_arn,
                'resource_type': 'rds:instance',
                'resource_id': db_id,
                'engine': db['Engine'],
                'status': db['DBInstanceStatus'],
                'instance_class': db['DBInstanceClass']
            }
            
            if missing_tags:
                resource_info['missing_tags'] = missing_tags
                resource_info['existing_tags'] = tags
                non_compliant.append(resource_info)
            else:
                resource_info['tags'] = tags
                compliant.append(resource_info)
                
    except Exception as e:
        print(f"Error scanning RDS resources: {str(e)}")
    
    return {'compliant': compliant, 'non_compliant': non_compliant}

def scan_s3_resources():
    """
    Scan S3 buckets for tag compliance
    
    Returns:
        Dictionary with compliant and non-compliant resources
    """
    compliant = []
    non_compliant = []
    
    try:
        # Get account ID
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Scan S3 buckets
        buckets = s3.list_buckets()
        
        for bucket in buckets['Buckets']:
            bucket_name = bucket['Name']
            bucket_arn = f"arn:aws:s3:::{bucket_name}"
            
            # Get tags
            tags = {}
            try:
                tags_response = s3.get_bucket_tagging(Bucket=bucket_name)
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
            except s3.exceptions.NoSuchTagSet:
                tags = {}
            except Exception:
                continue
            
            missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
            
            resource_info = {
                'resource_arn': bucket_arn,
                'resource_type': 's3:bucket',
                'resource_id': bucket_name,
                'creation_date': bucket['CreationDate'].isoformat()
            }
            
            if missing_tags:
                resource_info['missing_tags'] = missing_tags
                resource_info['existing_tags'] = tags
                non_compliant.append(resource_info)
            else:
                resource_info['tags'] = tags
                compliant.append(resource_info)
                
    except Exception as e:
        print(f"Error scanning S3 resources: {str(e)}")
    
    return {'compliant': compliant, 'non_compliant': non_compliant}

def check_resource_compliance(resource_arn: str):
    """
    Check compliance for a specific resource
    
    Args:
        resource_arn: ARN of the resource to check
        
    Returns:
        Compliance status for the resource
    """
    try:
        # Get tags for the resource
        response = resource_tagging.get_resources(
            ResourceARNList=[resource_arn]
        )
        
        if response['ResourceTagMappingList']:
            resource = response['ResourceTagMappingList'][0]
            tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
            missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
            
            return {
                'resource_arn': resource_arn,
                'resource_type': get_resource_type_from_arn(resource_arn),
                'compliant': len(missing_tags) == 0,
                'missing_tags': missing_tags,
                'existing_tags': tags,
                'required_tags': REQUIRED_TAGS
            }
        else:
            return {
                'resource_arn': resource_arn,
                'error': 'Resource not found'
            }
            
    except Exception as e:
        return {
            'resource_arn': resource_arn,
            'error': str(e)
        }

def auto_remediate_tags(resource_arns: List[str]):
    """
    Auto-remediate missing tags with default values
    
    Args:
        resource_arns: List of resource ARNs to remediate
        
    Returns:
        Remediation report
    """
    remediation_results = []
    
    # Default tag values
    default_tags = {
        'Environment': 'unspecified',
        'Owner': 'unassigned',
        'CostCenter': 'unallocated',
        'Project': 'unassigned'
    }
    
    for resource_arn in resource_arns:
        try:
            # Check current compliance
            compliance = check_resource_compliance(resource_arn)
            
            if not compliance.get('compliant', True):
                missing_tags = compliance.get('missing_tags', [])
                tags_to_add = []
                
                for tag in missing_tags:
                    tags_to_add.append({
                        'Key': tag,
                        'Value': default_tags[tag]
                    })
                
                # Apply tags
                resource_tagging.tag_resources(
                    ResourceARNList=[resource_arn],
                    Tags=tags_to_add
                )
                
                remediation_results.append({
                    'resource_arn': resource_arn,
                    'status': 'success',
                    'tags_added': tags_to_add
                })
            else:
                remediation_results.append({
                    'resource_arn': resource_arn,
                    'status': 'already_compliant'
                })
                
        except Exception as e:
            remediation_results.append({
                'resource_arn': resource_arn,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'remediation_timestamp': datetime.utcnow().isoformat(),
        'total_resources': len(resource_arns),
        'successful': len([r for r in remediation_results if r['status'] == 'success']),
        'already_compliant': len([r for r in remediation_results if r['status'] == 'already_compliant']),
        'failed': len([r for r in remediation_results if r['status'] == 'error']),
        'results': remediation_results
    }

def generate_compliance_report(report_type: str):
    """
    Generate compliance report
    
    Args:
        report_type: Type of report ('summary', 'detailed', 'trends')
        
    Returns:
        Report data
    """
    try:
        table = dynamodb.Table(COMPLIANCE_TABLE)
        
        if report_type == 'summary':
            # Get latest scan result
            response = table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={':pk': 'SCAN'},
                ScanIndexForward=False,
                Limit=1
            )
            
            if response['Items']:
                latest_scan = response['Items'][0]
                return {
                    'report_type': 'summary',
                    'generated_at': datetime.utcnow().isoformat(),
                    'latest_scan': latest_scan
                }
            
        elif report_type == 'trends':
            # Get historical trend data
            response = table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={':pk': 'SCAN'},
                ScanIndexForward=False,
                Limit=30  # Last 30 scans
            )
            
            trends = []
            for item in response['Items']:
                trends.append({
                    'timestamp': item['timestamp'],
                    'compliance_rate': item.get('compliance_rate', 0),
                    'total_resources': item.get('total_resources', 0),
                    'non_compliant_count': item.get('non_compliant_count', 0)
                })
            
            return {
                'report_type': 'trends',
                'generated_at': datetime.utcnow().isoformat(),
                'trends': trends
            }
            
        elif report_type == 'detailed':
            # Perform new scan for detailed report
            compliance_report = perform_compliance_scan()
            
            return {
                'report_type': 'detailed',
                'generated_at': datetime.utcnow().isoformat(),
                'scan_results': compliance_report
            }
            
        else:
            return {
                'error': f'Unknown report type: {report_type}'
            }
            
    except Exception as e:
        return {
            'error': f'Error generating report: {str(e)}'
        }

def store_compliance_results(compliance_report: Dict[str, Any]):
    """
    Store compliance results in DynamoDB
    
    Args:
        compliance_report: Compliance report to store
    """
    try:
        table = dynamodb.Table(COMPLIANCE_TABLE)
        
        # Store scan results
        table.put_item(
            Item={
                'pk': 'SCAN',
                'sk': compliance_report['scan_timestamp'],
                'timestamp': compliance_report['scan_timestamp'],
                'total_resources': compliance_report['total_resources'],
                'compliant_count': compliance_report['compliant_count'],
                'non_compliant_count': compliance_report['non_compliant_count'],
                'compliance_rate': compliance_report['compliance_rate'],
                'resources_by_type': compliance_report['resources_by_type'],
                'missing_tags_summary': compliance_report['missing_tags_summary']
            }
        )
        
        print(f"Stored compliance results in DynamoDB")
        
    except Exception as e:
        print(f"Error storing compliance results: {str(e)}")

def send_compliance_notifications(compliance_report: Dict[str, Any]):
    """
    Send notifications for non-compliant resources
    
    Args:
        compliance_report: Compliance report
    """
    try:
        # Get SNS topic ARN from environment variable
        topic_arn = os.environ.get('COMPLIANCE_SNS_TOPIC')
        
        if not topic_arn:
            print("No SNS topic configured for compliance notifications")
            return
        
        # Create notification message
        message = f"""
Tag Compliance Alert

Compliance Rate: {compliance_report['compliance_rate']:.1f}%
Non-Compliant Resources: {compliance_report['non_compliant_count']}
Total Resources Scanned: {compliance_report['total_resources']}

Missing Tags Summary:
"""
        
        for tag, count in compliance_report['missing_tags_summary'].items():
            message += f"  - {tag}: {count} resources\n"
        
        message += f"\nHigh Risk Resources: {len(compliance_report['summary']['high_risk_resources'])}"
        message += f"\nEstimated Cost Impact: ${compliance_report['summary']['cost_impact']:,.2f}/month"
        
        # Send notification
        sns.publish(
            TopicArn=topic_arn,
            Subject='AWS Tag Compliance Alert',
            Message=message
        )
        
        print(f"Sent compliance notification to SNS topic")
        
    except Exception as e:
        print(f"Error sending compliance notification: {str(e)}")

def identify_high_risk_resources(non_compliant_resources: List[Dict[str, Any]]):
    """
    Identify high-risk non-compliant resources
    
    Args:
        non_compliant_resources: List of non-compliant resources
        
    Returns:
        List of high-risk resources
    """
    high_risk = []
    
    # Define high-risk criteria
    high_risk_types = ['ec2:instance', 'rds:instance', 's3:bucket']
    critical_missing_tags = ['CostCenter', 'Owner']
    
    for resource in non_compliant_resources:
        resource_type = resource.get('resource_type', '')
        missing_tags = resource.get('missing_tags', [])
        
        # Check if it's a high-risk resource type
        if resource_type in high_risk_types:
            # Check if critical tags are missing
            if any(tag in missing_tags for tag in critical_missing_tags):
                high_risk.append(resource)
        
        # Also flag resources missing all required tags
        elif len(missing_tags) == len(REQUIRED_TAGS):
            high_risk.append(resource)
    
    return high_risk

def estimate_cost_impact(non_compliant_resources: List[Dict[str, Any]]):
    """
    Estimate the cost impact of non-compliant resources
    
    Args:
        non_compliant_resources: List of non-compliant resources
        
    Returns:
        Estimated monthly cost impact
    """
    # Simple cost estimation based on resource type
    # In production, this would query actual cost data
    cost_estimates = {
        'ec2:instance': 50.0,      # $50/month average per instance
        'rds:instance': 100.0,     # $100/month average per RDS instance
        'ec2:volume': 5.0,         # $5/month average per volume
        's3:bucket': 10.0,         # $10/month average per bucket
        'lambda:function': 1.0,    # $1/month average per function
    }
    
    total_cost_impact = 0.0
    
    for resource in non_compliant_resources:
        resource_type = resource.get('resource_type', '')
        
        # Get base cost estimate
        base_cost = cost_estimates.get(resource_type, 5.0)  # Default $5
        
        # Adjust based on missing tags
        missing_tags = resource.get('missing_tags', [])
        
        # Higher impact if CostCenter is missing (can't allocate costs)
        if 'CostCenter' in missing_tags:
            base_cost *= 1.5
        
        # Higher impact if Owner is missing (can't contact for optimization)
        if 'Owner' in missing_tags:
            base_cost *= 1.2
        
        total_cost_impact += base_cost
    
    return total_cost_impact

def get_resource_type_from_arn(arn: str) -> str:
    """
    Extract resource type from ARN
    
    Args:
        arn: AWS ARN
        
    Returns:
        Resource type string
    """
    try:
        # ARN format: arn:partition:service:region:account:resource
        parts = arn.split(':')
        if len(parts) >= 6:
            service = parts[2]
            resource_part = parts[5]
            
            # Extract resource type
            if '/' in resource_part:
                resource_type = resource_part.split('/')[0]
            else:
                resource_type = resource_part
            
            return f"{service}:{resource_type}"
        return 'unknown'
    except:
        return 'unknown'

# Environment variables
import os

# Create DynamoDB table if it doesn't exist
def create_compliance_table():
    """
    Create DynamoDB table for compliance history
    """
    try:
        dynamodb_client = boto3.client('dynamodb')
        
        # Check if table exists
        try:
            dynamodb_client.describe_table(TableName=COMPLIANCE_TABLE)
            print(f"Table {COMPLIANCE_TABLE} already exists")
            return
        except dynamodb_client.exceptions.ResourceNotFoundException:
            pass
        
        # Create table
        dynamodb_client.create_table(
            TableName=COMPLIANCE_TABLE,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},
                {'AttributeName': 'sk', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"Created DynamoDB table: {COMPLIANCE_TABLE}")
        
    except Exception as e:
        print(f"Error creating DynamoDB table: {str(e)}")

# Initialize table on first run
create_compliance_table()