import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class S3CostAnalyzer:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.cost_explorer_client = boto3.client('ce')
        
    def analyze_bucket_storage(self, bucket_names: List[str] = None) -> Dict[str, Any]:
        """Analyze S3 bucket storage metrics and costs"""
        try:
            if not bucket_names:
                # Get all buckets
                response = self.s3_client.list_buckets()
                bucket_names = [bucket['Name'] for bucket in response['Buckets']]
            
            bucket_analysis = {}
            
            for bucket_name in bucket_names:
                try:
                    # Get bucket size and object count from CloudWatch
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=2)  # S3 metrics are daily
                    
                    # Get bucket size in bytes
                    size_response = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Average']
                    )
                    
                    # Get number of objects
                    objects_response = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='NumberOfObjects',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Average']
                    )
                    
                    # Extract latest values
                    bucket_size = 0
                    object_count = 0
                    
                    if size_response['Datapoints']:
                        bucket_size = size_response['Datapoints'][-1]['Average']
                    
                    if objects_response['Datapoints']:
                        object_count = int(objects_response['Datapoints'][-1]['Average'])
                    
                    # Get bucket location and storage class information
                    try:
                        location_response = self.s3_client.get_bucket_location(Bucket=bucket_name)
                        region = location_response['LocationConstraint'] or 'us-east-1'
                    except:
                        region = 'unknown'
                    
                    # Get bucket tags
                    try:
                        tags_response = self.s3_client.get_bucket_tagging(Bucket=bucket_name)
                        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagSet']}
                    except:
                        tags = {}
                    
                    # Analyze storage classes (sample objects)
                    storage_classes = self.analyze_storage_classes(bucket_name)
                    
                    bucket_analysis[bucket_name] = {
                        'size_bytes': bucket_size,
                        'size_gb': bucket_size / (1024**3),
                        'object_count': object_count,
                        'region': region,
                        'tags': tags,
                        'storage_classes': storage_classes,
                        'last_modified': datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    logger.warning(f"Error analyzing bucket {bucket_name}: {str(e)}")
                    bucket_analysis[bucket_name] = {
                        'error': str(e),
                        'size_bytes': 0,
                        'object_count': 0
                    }
            
            return bucket_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing bucket storage: {str(e)}")
            return {}
    
    def analyze_storage_classes(self, bucket_name: str, max_objects: int = 1000) -> Dict[str, Any]:
        """Analyze storage classes distribution in a bucket"""
        try:
            storage_class_stats = {}
            total_size = 0
            
            # List objects with pagination
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                PaginationConfig={'MaxItems': max_objects}
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        storage_class = obj.get('StorageClass', 'STANDARD')
                        size = obj['Size']
                        
                        if storage_class not in storage_class_stats:
                            storage_class_stats[storage_class] = {
                                'count': 0,
                                'total_size': 0
                            }
                        
                        storage_class_stats[storage_class]['count'] += 1
                        storage_class_stats[storage_class]['total_size'] += size
                        total_size += size
            
            # Calculate percentages
            for storage_class in storage_class_stats:
                stats = storage_class_stats[storage_class]
                stats['size_percentage'] = (stats['total_size'] / total_size * 100) if total_size > 0 else 0
                stats['size_gb'] = stats['total_size'] / (1024**3)
            
            return storage_class_stats
            
        except Exception as e:
            logger.error(f"Error analyzing storage classes for {bucket_name}: {str(e)}")
            return {}
    
    def get_s3_costs(self, days: int = 30) -> Dict[str, Any]:
        """Get S3 cost information from Cost Explorer"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get S3 cost data
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
                        'Key': 'USAGE_TYPE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Simple Storage Service']
                    }
                }
            )
            
            # Process cost data by usage type
            usage_type_costs = {}
            total_cost = 0
            daily_costs = []
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_total = 0
                
                for group in result['Groups']:
                    usage_type = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if usage_type not in usage_type_costs:
                        usage_type_costs[usage_type] = 0
                    usage_type_costs[usage_type] += cost
                    daily_total += cost
                
                daily_costs.append({'date': date, 'cost': daily_total})
                total_cost += daily_total
            
            return {
                'total_cost': total_cost,
                'usage_type_costs': usage_type_costs,
                'daily_costs': daily_costs,
                'average_daily_cost': total_cost / days if days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting S3 costs: {str(e)}")
            return {}
    
    def identify_optimization_opportunities(self, bucket_analysis: Dict[str, Any], 
                                         cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify S3 cost optimization opportunities"""
        opportunities = []
        
        for bucket_name, analysis in bucket_analysis.items():
            if 'error' in analysis:
                continue
                
            size_gb = analysis.get('size_gb', 0)
            storage_classes = analysis.get('storage_classes', {})
            tags = analysis.get('tags', {})
            
            # Check for buckets using only STANDARD storage
            if 'STANDARD' in storage_classes and len(storage_classes) == 1:
                if size_gb > 1:  # Only for buckets with significant size
                    opportunities.append({
                        'type': 'storage_class_optimization',
                        'bucket_name': bucket_name,
                        'current_storage_class': 'STANDARD only',
                        'recommendation': 'Consider using S3 Intelligent-Tiering or lifecycle policies',
                        'priority': 'medium',
                        'estimated_savings_percent': 20,
                        'size_gb': size_gb
                    })
            
            # Check for large buckets without lifecycle policies
            if size_gb > 10:
                try:
                    self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                except self.s3_client.exceptions.NoSuchLifecycleConfiguration:
                    opportunities.append({
                        'type': 'lifecycle_policy',
                        'bucket_name': bucket_name,
                        'recommendation': 'Implement lifecycle policies to automatically transition objects to cheaper storage classes',
                        'priority': 'high' if size_gb > 100 else 'medium',
                        'estimated_savings_percent': 30 if size_gb > 100 else 20,
                        'size_gb': size_gb
                    })
                except Exception:
                    pass
            
            # Check for buckets without proper tagging
            required_tags = ['Environment', 'Owner', 'Project']
            missing_tags = [tag for tag in required_tags if tag not in tags]
            
            if missing_tags:
                opportunities.append({
                    'type': 'tagging_compliance',
                    'bucket_name': bucket_name,
                    'missing_tags': missing_tags,
                    'recommendation': f'Add missing tags: {", ".join(missing_tags)}',
                    'priority': 'low'
                })
            
            # Check for buckets with versioning but no lifecycle policy for old versions
            try:
                versioning_response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
                if versioning_response.get('Status') == 'Enabled':
                    opportunities.append({
                        'type': 'version_management',
                        'bucket_name': bucket_name,
                        'recommendation': 'Consider lifecycle policies for non-current versions to reduce storage costs',
                        'priority': 'medium',
                        'estimated_savings_percent': 15
                    })
            except Exception:
                pass
            
            # Check for buckets with multipart upload cleanup
            try:
                multipart_response = self.s3_client.list_multipart_uploads(Bucket=bucket_name)
                if multipart_response.get('Uploads'):
                    opportunities.append({
                        'type': 'multipart_cleanup',
                        'bucket_name': bucket_name,
                        'recommendation': 'Clean up incomplete multipart uploads to reduce storage costs',
                        'priority': 'low',
                        'incomplete_uploads': len(multipart_response['Uploads'])
                    })
            except Exception:
                pass
        
        return opportunities

def lambda_handler(event, context):
    """AWS Lambda handler for S3 cost analysis"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize the analyzer
        analyzer = S3CostAnalyzer()
        
        # Extract parameters from the event
        action = event.get('action', 'analyze_all')
        bucket_names = event.get('bucket_names', [])
        days = event.get('days', 30)
        
        if action == 'analyze_storage':
            bucket_analysis = analyzer.analyze_bucket_storage(bucket_names)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'bucket_analysis': bucket_analysis,
                    'bucket_count': len(bucket_analysis)
                })
            }
            
        elif action == 'get_recommendations':
            bucket_analysis = analyzer.analyze_bucket_storage(bucket_names)
            cost_data = analyzer.get_s3_costs(days)
            opportunities = analyzer.identify_optimization_opportunities(bucket_analysis, cost_data)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'recommendations': opportunities,
                    'cost_summary': cost_data,
                    'bucket_count': len(bucket_analysis),
                    'analysis_period_days': days
                })
            }
            
        elif action == 'analyze_all':
            # Comprehensive analysis
            bucket_analysis = analyzer.analyze_bucket_storage(bucket_names)
            cost_data = analyzer.get_s3_costs(days)
            opportunities = analyzer.identify_optimization_opportunities(bucket_analysis, cost_data)
            
            # Calculate summary statistics
            total_storage_gb = sum(analysis.get('size_gb', 0) for analysis in bucket_analysis.values() if 'error' not in analysis)
            total_objects = sum(analysis.get('object_count', 0) for analysis in bucket_analysis.values() if 'error' not in analysis)
            
            # Calculate potential savings
            total_potential_savings = 0
            high_priority_count = 0
            
            for opp in opportunities:
                if opp.get('estimated_savings_percent') and opp.get('size_gb'):
                    # Estimate savings based on storage size and average S3 pricing
                    storage_cost_per_gb = 0.023  # Approximate S3 Standard pricing
                    monthly_storage_cost = opp['size_gb'] * storage_cost_per_gb
                    monthly_savings = monthly_storage_cost * (opp['estimated_savings_percent'] / 100)
                    total_potential_savings += monthly_savings
                    opp['estimated_monthly_savings'] = monthly_savings
                
                if opp.get('priority') == 'high':
                    high_priority_count += 1
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'summary': {
                        'bucket_count': len(bucket_analysis),
                        'total_storage_gb': total_storage_gb,
                        'total_objects': total_objects,
                        'total_monthly_cost': cost_data.get('average_daily_cost', 0) * 30,
                        'potential_monthly_savings': total_potential_savings,
                        'high_priority_recommendations': high_priority_count,
                        'total_recommendations': len(opportunities)
                    },
                    'bucket_analysis': bucket_analysis,
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
                    'supported_actions': ['analyze_storage', 'get_recommendations', 'analyze_all']
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
        'days': 30
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
