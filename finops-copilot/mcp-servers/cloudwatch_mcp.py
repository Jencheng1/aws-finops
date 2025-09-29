#!/usr/bin/env python3
"""
CloudWatch MCP Server

This MCP server provides access to AWS CloudWatch metrics and logs through the Model Context Protocol.
It exposes monitoring and performance data to AI agents and applications.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudWatchMCPServer:
    """MCP Server for AWS CloudWatch integration"""
    
    def __init__(self):
        """Initialize the CloudWatch MCP Server"""
        try:
            self.cloudwatch_client = boto3.client('cloudwatch')
            self.logs_client = boto3.client('logs')
            logger.info("CloudWatch MCP Server initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing CloudWatch client: {str(e)}")
            raise
    
    async def get_metric_statistics(self, 
                                   namespace: str,
                                   metric_name: str,
                                   dimensions: List[Dict[str, str]],
                                   start_time: datetime,
                                   end_time: datetime,
                                   period: int = 3600,
                                   statistics: List[str] = None) -> Dict[str, Any]:
        """
        Get metric statistics from CloudWatch
        
        Args:
            namespace: CloudWatch namespace (e.g., 'AWS/EC2')
            metric_name: Name of the metric
            dimensions: List of dimension filters
            start_time: Start time for the query
            end_time: End time for the query
            period: Period in seconds for data points
            statistics: List of statistics to retrieve
        
        Returns:
            Dict containing metric statistics
        """
        try:
            if statistics is None:
                statistics = ['Average', 'Maximum', 'Minimum']
            
            params = {
                'Namespace': namespace,
                'MetricName': metric_name,
                'Dimensions': dimensions,
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'Statistics': statistics
            }
            
            logger.info(f"Querying CloudWatch metrics: {namespace}/{metric_name}")
            response = self.cloudwatch_client.get_metric_statistics(**params)
            
            # Process and sort datapoints by timestamp
            datapoints = sorted(response.get('Datapoints', []), key=lambda x: x['Timestamp'])
            
            # Calculate additional statistics
            values = []
            for stat in statistics:
                values.extend([dp.get(stat, 0) for dp in datapoints if dp.get(stat) is not None])
            
            processed_data = {
                'namespace': namespace,
                'metric_name': metric_name,
                'dimensions': dimensions,
                'period': period,
                'statistics': statistics,
                'datapoints': [
                    {
                        'timestamp': dp['Timestamp'].isoformat(),
                        'values': {stat: dp.get(stat) for stat in statistics if dp.get(stat) is not None},
                        'unit': dp.get('Unit', 'None')
                    }
                    for dp in datapoints
                ],
                'summary': {
                    'total_datapoints': len(datapoints),
                    'time_range': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    },
                    'aggregated_stats': {
                        'average': sum(values) / len(values) if values else 0,
                        'max': max(values) if values else 0,
                        'min': min(values) if values else 0,
                        'count': len(values)
                    }
                }
            }
            
            return processed_data
            
        except ClientError as e:
            logger.error(f"AWS API error in get_metric_statistics: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_metric_statistics: {str(e)}")
            raise
    
    async def list_metrics(self, 
                          namespace: str = None,
                          metric_name: str = None,
                          dimensions: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        List available metrics in CloudWatch
        
        Args:
            namespace: Optional namespace filter
            metric_name: Optional metric name filter
            dimensions: Optional dimension filters
        
        Returns:
            Dict containing available metrics
        """
        try:
            params = {}
            
            if namespace:
                params['Namespace'] = namespace
            if metric_name:
                params['MetricName'] = metric_name
            if dimensions:
                params['Dimensions'] = dimensions
            
            response = self.cloudwatch_client.list_metrics(**params)
            
            metrics = []
            for metric in response.get('Metrics', []):
                metrics.append({
                    'namespace': metric.get('Namespace'),
                    'metric_name': metric.get('MetricName'),
                    'dimensions': metric.get('Dimensions', [])
                })
            
            return {
                'metrics': metrics,
                'total_count': len(metrics),
                'filters_applied': {
                    'namespace': namespace,
                    'metric_name': metric_name,
                    'dimensions': dimensions
                }
            }
            
        except ClientError as e:
            logger.error(f"AWS API error in list_metrics: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in list_metrics: {str(e)}")
            raise
    
    async def get_ec2_metrics(self, 
                             instance_ids: List[str],
                             start_time: datetime,
                             end_time: datetime,
                             period: int = 3600) -> Dict[str, Any]:
        """
        Get comprehensive EC2 metrics for specified instances
        
        Args:
            instance_ids: List of EC2 instance IDs
            start_time: Start time for the query
            end_time: End time for the query
            period: Period in seconds for data points
        
        Returns:
            Dict containing EC2 metrics for all instances
        """
        try:
            ec2_metrics = [
                'CPUUtilization',
                'NetworkIn',
                'NetworkOut',
                'DiskReadOps',
                'DiskWriteOps',
                'DiskReadBytes',
                'DiskWriteBytes'
            ]
            
            instance_data = {}
            
            for instance_id in instance_ids:
                instance_metrics = {}
                
                for metric_name in ec2_metrics:
                    try:
                        metric_data = await self.get_metric_statistics(
                            namespace='AWS/EC2',
                            metric_name=metric_name,
                            dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                            start_time=start_time,
                            end_time=end_time,
                            period=period
                        )
                        instance_metrics[metric_name] = metric_data
                    except Exception as e:
                        logger.warning(f"Failed to get {metric_name} for {instance_id}: {str(e)}")
                        instance_metrics[metric_name] = {'error': str(e)}
                
                instance_data[instance_id] = {
                    'metrics': instance_metrics,
                    'analysis': self._analyze_ec2_metrics(instance_metrics)
                }
            
            return {
                'instance_data': instance_data,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'period': period,
                'metrics_collected': ec2_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in get_ec2_metrics: {str(e)}")
            raise
    
    def _analyze_ec2_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze EC2 metrics to provide insights"""
        analysis = {
            'utilization_summary': {},
            'recommendations': [],
            'alerts': []
        }
        
        try:
            # Analyze CPU utilization
            cpu_data = metrics.get('CPUUtilization', {})
            if 'summary' in cpu_data:
                cpu_avg = cpu_data['summary']['aggregated_stats']['average']
                cpu_max = cpu_data['summary']['aggregated_stats']['max']
                
                analysis['utilization_summary']['cpu'] = {
                    'average': cpu_avg,
                    'maximum': cpu_max,
                    'status': 'underutilized' if cpu_avg < 20 else 'normal' if cpu_avg < 80 else 'high'
                }
                
                if cpu_avg < 10:
                    analysis['recommendations'].append('Consider downsizing instance - very low CPU utilization')
                elif cpu_avg > 80:
                    analysis['alerts'].append('High CPU utilization detected - consider scaling up')
            
            # Analyze network metrics
            network_in = metrics.get('NetworkIn', {})
            network_out = metrics.get('NetworkOut', {})
            
            if 'summary' in network_in and 'summary' in network_out:
                net_in_avg = network_in['summary']['aggregated_stats']['average']
                net_out_avg = network_out['summary']['aggregated_stats']['average']
                
                analysis['utilization_summary']['network'] = {
                    'average_in_bytes': net_in_avg,
                    'average_out_bytes': net_out_avg,
                    'total_transfer_mb': (net_in_avg + net_out_avg) / (1024 * 1024)
                }
            
            # Analyze disk metrics
            disk_read = metrics.get('DiskReadOps', {})
            disk_write = metrics.get('DiskWriteOps', {})
            
            if 'summary' in disk_read and 'summary' in disk_write:
                read_ops = disk_read['summary']['aggregated_stats']['average']
                write_ops = disk_write['summary']['aggregated_stats']['average']
                
                analysis['utilization_summary']['disk'] = {
                    'average_read_ops': read_ops,
                    'average_write_ops': write_ops,
                    'total_iops': read_ops + write_ops
                }
                
                if read_ops + write_ops < 10:
                    analysis['recommendations'].append('Low disk activity - consider smaller instance type')
        
        except Exception as e:
            logger.warning(f"Error analyzing metrics: {str(e)}")
            analysis['analysis_error'] = str(e)
        
        return analysis
    
    async def get_s3_metrics(self, 
                            bucket_names: List[str],
                            start_time: datetime,
                            end_time: datetime) -> Dict[str, Any]:
        """
        Get S3 bucket metrics from CloudWatch
        
        Args:
            bucket_names: List of S3 bucket names
            start_time: Start time for the query
            end_time: End time for the query
        
        Returns:
            Dict containing S3 metrics for all buckets
        """
        try:
            s3_metrics = [
                'BucketSizeBytes',
                'NumberOfObjects'
            ]
            
            bucket_data = {}
            
            for bucket_name in bucket_names:
                bucket_metrics = {}
                
                # Get bucket size for different storage types
                storage_types = ['StandardStorage', 'StandardIAStorage', 'ReducedRedundancyStorage']
                
                for storage_type in storage_types:
                    try:
                        size_data = await self.get_metric_statistics(
                            namespace='AWS/S3',
                            metric_name='BucketSizeBytes',
                            dimensions=[
                                {'Name': 'BucketName', 'Value': bucket_name},
                                {'Name': 'StorageType', 'Value': storage_type}
                            ],
                            start_time=start_time,
                            end_time=end_time,
                            period=86400  # Daily metrics for S3
                        )
                        bucket_metrics[f'BucketSizeBytes_{storage_type}'] = size_data
                    except Exception as e:
                        logger.warning(f"Failed to get size for {bucket_name}/{storage_type}: {str(e)}")
                
                # Get number of objects
                try:
                    objects_data = await self.get_metric_statistics(
                        namespace='AWS/S3',
                        metric_name='NumberOfObjects',
                        dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                        ],
                        start_time=start_time,
                        end_time=end_time,
                        period=86400
                    )
                    bucket_metrics['NumberOfObjects'] = objects_data
                except Exception as e:
                    logger.warning(f"Failed to get object count for {bucket_name}: {str(e)}")
                
                bucket_data[bucket_name] = {
                    'metrics': bucket_metrics,
                    'analysis': self._analyze_s3_metrics(bucket_metrics)
                }
            
            return {
                'bucket_data': bucket_data,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_s3_metrics: {str(e)}")
            raise
    
    def _analyze_s3_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze S3 metrics to provide insights"""
        analysis = {
            'storage_summary': {},
            'recommendations': []
        }
        
        try:
            total_size = 0
            storage_breakdown = {}
            
            # Calculate total size across storage types
            for key, metric_data in metrics.items():
                if key.startswith('BucketSizeBytes_') and 'summary' in metric_data:
                    storage_type = key.replace('BucketSizeBytes_', '')
                    size = metric_data['summary']['aggregated_stats']['average']
                    storage_breakdown[storage_type] = size
                    total_size += size
            
            analysis['storage_summary'] = {
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024**3),
                'storage_breakdown': storage_breakdown
            }
            
            # Get object count
            if 'NumberOfObjects' in metrics and 'summary' in metrics['NumberOfObjects']:
                object_count = metrics['NumberOfObjects']['summary']['aggregated_stats']['average']
                analysis['storage_summary']['object_count'] = object_count
                
                if object_count > 0:
                    analysis['storage_summary']['average_object_size_bytes'] = total_size / object_count
            
            # Generate recommendations
            if total_size > 1024**3:  # > 1GB
                if 'StandardStorage' in storage_breakdown and storage_breakdown['StandardStorage'] > total_size * 0.8:
                    analysis['recommendations'].append('Consider using S3 Intelligent-Tiering for cost optimization')
            
        except Exception as e:
            logger.warning(f"Error analyzing S3 metrics: {str(e)}")
            analysis['analysis_error'] = str(e)
        
        return analysis
    
    async def process_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an MCP request and route to appropriate method
        
        Args:
            request: MCP request dictionary
        
        Returns:
            Dict containing the response
        """
        try:
            method = request.get('method')
            params = request.get('params', {})
            
            # Convert string timestamps to datetime objects
            if 'start_time' in params and isinstance(params['start_time'], str):
                params['start_time'] = datetime.fromisoformat(params['start_time'].replace('Z', '+00:00'))
            if 'end_time' in params and isinstance(params['end_time'], str):
                params['end_time'] = datetime.fromisoformat(params['end_time'].replace('Z', '+00:00'))
            
            if method == 'get_metric_statistics':
                return await self.get_metric_statistics(**params)
            elif method == 'list_metrics':
                return await self.list_metrics(**params)
            elif method == 'get_ec2_metrics':
                return await self.get_ec2_metrics(**params)
            elif method == 'get_s3_metrics':
                return await self.get_s3_metrics(**params)
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            logger.error(f"Error processing MCP request: {str(e)}")
            return {
                'error': str(e),
                'method': request.get('method'),
                'params': request.get('params')
            }

# Example usage and testing
async def main():
    """Main function for testing the MCP server"""
    server = CloudWatchMCPServer()
    
    # Test EC2 metrics query
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    try:
        # Test listing metrics
        metrics_list = await server.list_metrics(namespace='AWS/EC2')
        print(f"Found {metrics_list['total_count']} EC2 metrics")
        
        # Test getting specific metric (this would need actual instance IDs)
        # ec2_data = await server.get_ec2_metrics(
        #     instance_ids=['i-1234567890abcdef0'],
        #     start_time=start_time,
        #     end_time=end_time
        # )
        
        print("CloudWatch MCP Server test completed successfully")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
