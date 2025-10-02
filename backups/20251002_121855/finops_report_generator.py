#!/usr/bin/env python3
"""
FinOps Report Generator Module
Generates comprehensive management reports with cost analysis, resource tagging, and optimization recommendations
"""

import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import io
import base64
from typing import Dict, List, Tuple, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
import xlsxwriter
import warnings
warnings.filterwarnings('ignore')

class FinOpsReportGenerator:
    """
    Comprehensive FinOps Report Generator
    """
    
    def __init__(self, aws_clients):
        """
        Initialize report generator with AWS clients
        """
        self.clients = aws_clients
        self.ce_client = aws_clients['ce']
        self.ec2_client = aws_clients['ec2']
        self.rds_client = boto3.client('rds')
        self.s3_client = boto3.client('s3')
        self.lambda_client = aws_clients['lambda']
        self.cloudwatch_client = aws_clients['cloudwatch']
        self.organizations_client = aws_clients['organizations']
        self.resource_tagging_client = boto3.client('resourcegroupstaggingapi')
        
    def generate_comprehensive_report(self, 
                                    report_type='full',
                                    start_date=None,
                                    end_date=None,
                                    include_charts=True,
                                    format='pdf'):
        """
        Generate comprehensive FinOps report
        
        Args:
            report_type: 'full', 'executive', 'technical', 'compliance'
            start_date: Report start date
            end_date: Report end date
            include_charts: Include visualizations
            format: 'pdf', 'excel', 'json'
            
        Returns:
            Report data and file content
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Gather all report data
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': report_type,
                'period': f"{start_date} to {end_date}",
                'account_id': self.clients['sts'].get_caller_identity()['Account']
            },
            'cost_analysis': self._analyze_costs(start_date, end_date),
            'resource_tagging': self._analyze_resource_tagging(),
            'optimization_recommendations': self._generate_optimization_recommendations(),
            'savings_plan_analysis': self._analyze_savings_plans(),
            'trend_analysis': self._analyze_trends(start_date, end_date),
            'top_services_breakdown': self._analyze_top_services(start_date, end_date),
            'untagged_resources': self._find_untagged_resources(),
            'cost_anomalies': self._detect_cost_anomalies(start_date, end_date)
        }
        
        # Generate report in requested format
        if format == 'pdf':
            return self._generate_pdf_report(report_data, include_charts)
        elif format == 'excel':
            return self._generate_excel_report(report_data, include_charts)
        elif format == 'json':
            return json.dumps(report_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _analyze_costs(self, start_date, end_date):
        """
        Analyze costs for the period
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            )
            
            total_cost = 0
            service_costs = {}
            daily_costs = []
            
            for result in response['ResultsByTime']:
                daily_total = 0
                date = result['TimePeriod']['Start']
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    usage_type = group['Keys'][1]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service not in service_costs:
                        service_costs[service] = 0
                    service_costs[service] += cost
                    daily_total += cost
                    total_cost += cost
                
                daily_costs.append({
                    'date': date,
                    'cost': daily_total
                })
            
            # Calculate statistics
            avg_daily_cost = total_cost / len(daily_costs) if daily_costs else 0
            max_daily_cost = max([d['cost'] for d in daily_costs]) if daily_costs else 0
            min_daily_cost = min([d['cost'] for d in daily_costs]) if daily_costs else 0
            
            return {
                'total_cost': total_cost,
                'average_daily_cost': avg_daily_cost,
                'max_daily_cost': max_daily_cost,
                'min_daily_cost': min_daily_cost,
                'service_costs': service_costs,
                'daily_costs': daily_costs,
                'cost_by_day_of_week': self._analyze_by_day_of_week(daily_costs)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_cost': 0,
                'service_costs': {},
                'daily_costs': []
            }
    
    def _analyze_resource_tagging(self):
        """
        Analyze resource tagging compliance
        """
        try:
            # Get all tagged resources
            tagged_resources = []
            untagged_resources = []
            
            paginator = self.resource_tagging_client.get_paginator('get_resources')
            
            # Get all resources
            for page in paginator.paginate():
                for resource in page['ResourceTagMappingList']:
                    resource_arn = resource['ResourceARN']
                    tags = resource.get('Tags', [])
                    
                    resource_info = {
                        'arn': resource_arn,
                        'type': self._get_resource_type_from_arn(resource_arn),
                        'tags': {tag['Key']: tag['Value'] for tag in tags},
                        'tag_count': len(tags)
                    }
                    
                    # Check for required tags
                    required_tags = ['Environment', 'Owner', 'CostCenter', 'Project']
                    missing_tags = [tag for tag in required_tags if tag not in resource_info['tags']]
                    
                    if missing_tags:
                        resource_info['missing_tags'] = missing_tags
                        untagged_resources.append(resource_info)
                    else:
                        tagged_resources.append(resource_info)
            
            # Calculate compliance metrics
            total_resources = len(tagged_resources) + len(untagged_resources)
            compliance_rate = (len(tagged_resources) / total_resources * 100) if total_resources > 0 else 0
            
            # Group by resource type
            resources_by_type = {}
            for resource in tagged_resources + untagged_resources:
                res_type = resource['type']
                if res_type not in resources_by_type:
                    resources_by_type[res_type] = {'tagged': 0, 'untagged': 0, 'total': 0}
                
                if 'missing_tags' in resource:
                    resources_by_type[res_type]['untagged'] += 1
                else:
                    resources_by_type[res_type]['tagged'] += 1
                resources_by_type[res_type]['total'] += 1
            
            return {
                'total_resources': total_resources,
                'tagged_resources': len(tagged_resources),
                'untagged_resources': len(untagged_resources),
                'compliance_rate': compliance_rate,
                'resources_by_type': resources_by_type,
                'untagged_resource_details': untagged_resources[:100]  # Limit to 100 for report
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_resources': 0,
                'compliance_rate': 0
            }
    
    def _generate_optimization_recommendations(self):
        """
        Generate cost optimization recommendations
        """
        recommendations = []
        potential_savings = 0
        
        try:
            # EC2 Optimization
            ec2_recommendations = self._analyze_ec2_optimization()
            recommendations.extend(ec2_recommendations['recommendations'])
            potential_savings += ec2_recommendations['potential_savings']
            
            # EBS Optimization
            ebs_recommendations = self._analyze_ebs_optimization()
            recommendations.extend(ebs_recommendations['recommendations'])
            potential_savings += ebs_recommendations['potential_savings']
            
            # RDS Optimization
            rds_recommendations = self._analyze_rds_optimization()
            recommendations.extend(rds_recommendations['recommendations'])
            potential_savings += rds_recommendations['potential_savings']
            
            # S3 Optimization
            s3_recommendations = self._analyze_s3_optimization()
            recommendations.extend(s3_recommendations['recommendations'])
            potential_savings += s3_recommendations['potential_savings']
            
            # Savings Plans Recommendations
            sp_recommendations = self._get_savings_plan_recommendations()
            recommendations.extend(sp_recommendations['recommendations'])
            potential_savings += sp_recommendations['potential_savings']
            
            return {
                'recommendations': recommendations,
                'total_potential_savings': potential_savings,
                'monthly_savings': potential_savings / 12,
                'categories': {
                    'compute': len([r for r in recommendations if r['category'] == 'compute']),
                    'storage': len([r for r in recommendations if r['category'] == 'storage']),
                    'database': len([r for r in recommendations if r['category'] == 'database']),
                    'commitments': len([r for r in recommendations if r['category'] == 'commitments'])
                }
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'recommendations': [],
                'total_potential_savings': 0
            }
    
    def _analyze_ec2_optimization(self):
        """
        Analyze EC2 instances for optimization opportunities
        """
        recommendations = []
        potential_savings = 0
        
        try:
            # Get all instances
            instances = self.ec2_client.describe_instances()
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance.get('InstanceType', 'unknown')
                    state = instance['State']['Name']
                    
                    # Check stopped instances
                    if state == 'stopped':
                        # Estimate monthly cost based on EBS volumes
                        monthly_cost = self._estimate_stopped_instance_cost(instance)
                        if monthly_cost > 0:
                            recommendations.append({
                                'category': 'compute',
                                'type': 'stopped_instance',
                                'resource_id': instance_id,
                                'recommendation': f'Terminate stopped instance {instance_id} to save on EBS costs',
                                'monthly_savings': monthly_cost,
                                'priority': 'high'
                            })
                            potential_savings += monthly_cost * 12
                    
                    elif state == 'running':
                        # Check for underutilized instances
                        cpu_utilization = self._get_instance_cpu_utilization(instance_id)
                        if cpu_utilization is not None and cpu_utilization < 10:
                            # Estimate savings from rightsizing
                            current_cost = self._estimate_instance_monthly_cost(instance_type)
                            smaller_type = self._get_smaller_instance_type(instance_type)
                            if smaller_type:
                                new_cost = self._estimate_instance_monthly_cost(smaller_type)
                                savings = current_cost - new_cost
                                if savings > 0:
                                    recommendations.append({
                                        'category': 'compute',
                                        'type': 'rightsizing',
                                        'resource_id': instance_id,
                                        'recommendation': f'Rightsize instance {instance_id} from {instance_type} to {smaller_type}',
                                        'monthly_savings': savings,
                                        'priority': 'medium',
                                        'current_utilization': f'{cpu_utilization:.1f}%'
                                    })
                                    potential_savings += savings * 12
            
            return {
                'recommendations': recommendations,
                'potential_savings': potential_savings
            }
            
        except Exception as e:
            return {
                'recommendations': [],
                'potential_savings': 0,
                'error': str(e)
            }
    
    def _analyze_ebs_optimization(self):
        """
        Analyze EBS volumes for optimization
        """
        recommendations = []
        potential_savings = 0
        
        try:
            # Get all volumes
            volumes = self.ec2_client.describe_volumes()
            
            for volume in volumes['Volumes']:
                volume_id = volume['VolumeId']
                size = volume['Size']
                volume_type = volume.get('VolumeType', 'gp2')
                state = volume['State']
                
                # Check unattached volumes
                if state == 'available':
                    monthly_cost = self._estimate_ebs_monthly_cost(size, volume_type)
                    recommendations.append({
                        'category': 'storage',
                        'type': 'unattached_volume',
                        'resource_id': volume_id,
                        'recommendation': f'Delete unattached EBS volume {volume_id} ({size} GB)',
                        'monthly_savings': monthly_cost,
                        'priority': 'high'
                    })
                    potential_savings += monthly_cost * 12
                
                # Check for gp2 to gp3 migration opportunity
                elif volume_type == 'gp2' and size >= 100:
                    current_cost = self._estimate_ebs_monthly_cost(size, 'gp2')
                    new_cost = self._estimate_ebs_monthly_cost(size, 'gp3')
                    savings = current_cost - new_cost
                    if savings > 0:
                        recommendations.append({
                            'category': 'storage',
                            'type': 'volume_type_change',
                            'resource_id': volume_id,
                            'recommendation': f'Migrate EBS volume {volume_id} from gp2 to gp3',
                            'monthly_savings': savings,
                            'priority': 'low'
                        })
                        potential_savings += savings * 12
            
            # Check for orphaned snapshots
            snapshots = self.ec2_client.describe_snapshots(OwnerIds=['self'])
            for snapshot in snapshots['Snapshots']:
                snapshot_id = snapshot['SnapshotId']
                size = snapshot.get('VolumeSize', 0)
                
                # Check if volume still exists
                if 'VolumeId' in snapshot:
                    try:
                        self.ec2_client.describe_volumes(VolumeIds=[snapshot['VolumeId']])
                    except:
                        # Volume doesn't exist - orphaned snapshot
                        monthly_cost = size * 0.05  # $0.05 per GB-month for snapshots
                        recommendations.append({
                            'category': 'storage',
                            'type': 'orphaned_snapshot',
                            'resource_id': snapshot_id,
                            'recommendation': f'Delete orphaned snapshot {snapshot_id} ({size} GB)',
                            'monthly_savings': monthly_cost,
                            'priority': 'medium'
                        })
                        potential_savings += monthly_cost * 12
            
            return {
                'recommendations': recommendations,
                'potential_savings': potential_savings
            }
            
        except Exception as e:
            return {
                'recommendations': [],
                'potential_savings': 0,
                'error': str(e)
            }
    
    def _analyze_rds_optimization(self):
        """
        Analyze RDS instances for optimization
        """
        recommendations = []
        potential_savings = 0
        
        try:
            # Get all RDS instances
            db_instances = self.rds_client.describe_db_instances()
            
            for db in db_instances['DBInstances']:
                db_id = db['DBInstanceIdentifier']
                db_class = db['DBInstanceClass']
                engine = db['Engine']
                multi_az = db.get('MultiAZ', False)
                
                # Check for idle instances (low connection count)
                try:
                    # Get connection metrics
                    metrics = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/RDS',
                        MetricName='DatabaseConnections',
                        Dimensions=[
                            {'Name': 'DBInstanceIdentifier', 'Value': db_id}
                        ],
                        StartTime=datetime.now() - timedelta(days=7),
                        EndTime=datetime.now(),
                        Period=3600,
                        Statistics=['Average']
                    )
                    
                    if metrics['Datapoints']:
                        avg_connections = sum(d['Average'] for d in metrics['Datapoints']) / len(metrics['Datapoints'])
                        if avg_connections < 1:
                            monthly_cost = self._estimate_rds_monthly_cost(db_class, engine, multi_az)
                            recommendations.append({
                                'category': 'database',
                                'type': 'idle_database',
                                'resource_id': db_id,
                                'recommendation': f'Consider removing idle RDS instance {db_id} (avg connections: {avg_connections:.1f})',
                                'monthly_savings': monthly_cost,
                                'priority': 'high'
                            })
                            potential_savings += monthly_cost * 12
                except:
                    pass
            
            return {
                'recommendations': recommendations,
                'potential_savings': potential_savings
            }
            
        except Exception as e:
            return {
                'recommendations': [],
                'potential_savings': 0,
                'error': str(e)
            }
    
    def _analyze_s3_optimization(self):
        """
        Analyze S3 buckets for optimization
        """
        recommendations = []
        potential_savings = 0
        
        try:
            # Get all buckets
            buckets = self.s3_client.list_buckets()
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket lifecycle configuration
                    try:
                        lifecycle = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                        has_lifecycle = True
                    except:
                        has_lifecycle = False
                    
                    # Get bucket metrics
                    try:
                        # Get storage metrics
                        metrics_response = self.cloudwatch_client.get_metric_statistics(
                            Namespace='AWS/S3',
                            MetricName='BucketSizeBytes',
                            Dimensions=[
                                {'Name': 'BucketName', 'Value': bucket_name},
                                {'Name': 'StorageType', 'Value': 'StandardStorage'}
                            ],
                            StartTime=datetime.now() - timedelta(days=1),
                            EndTime=datetime.now(),
                            Period=86400,
                            Statistics=['Average']
                        )
                        
                        if metrics_response['Datapoints'] and not has_lifecycle:
                            bucket_size_gb = metrics_response['Datapoints'][0]['Average'] / (1024**3)
                            if bucket_size_gb > 100:  # Only recommend for buckets > 100GB
                                # Estimate savings from lifecycle policies
                                current_cost = bucket_size_gb * 0.023  # Standard storage cost
                                ia_cost = bucket_size_gb * 0.0125  # IA storage cost
                                savings = (current_cost - ia_cost) * 0.5  # Assume 50% can move to IA
                                
                                recommendations.append({
                                    'category': 'storage',
                                    'type': 's3_lifecycle',
                                    'resource_id': bucket_name,
                                    'recommendation': f'Add lifecycle policy to bucket {bucket_name} to transition old data to IA/Glacier',
                                    'monthly_savings': savings,
                                    'priority': 'medium',
                                    'bucket_size_gb': f'{bucket_size_gb:.1f}'
                                })
                                potential_savings += savings * 12
                    except:
                        pass
                        
                except Exception as e:
                    pass
            
            return {
                'recommendations': recommendations,
                'potential_savings': potential_savings
            }
            
        except Exception as e:
            return {
                'recommendations': [],
                'potential_savings': 0,
                'error': str(e)
            }
    
    def _get_savings_plan_recommendations(self):
        """
        Get Savings Plan recommendations
        """
        recommendations = []
        potential_savings = 0
        
        try:
            # Get Compute Savings Plan recommendations
            compute_sp = self.ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='ALL_UPFRONT',
                LookbackPeriodInDays='SIXTY_DAYS'
            )
            
            if 'SavingsPlansPurchaseRecommendation' in compute_sp:
                rec = compute_sp['SavingsPlansPurchaseRecommendation']
                if 'HourlyCommitmentToPurchase' in rec:
                    hourly = float(rec['HourlyCommitmentToPurchase'])
                    annual_savings = float(rec.get('EstimatedSavingsAmount', 0))
                    
                    if hourly > 0 and annual_savings > 0:
                        recommendations.append({
                            'category': 'commitments',
                            'type': 'savings_plan',
                            'resource_id': 'compute_sp',
                            'recommendation': f'Purchase Compute Savings Plan with ${hourly:.2f}/hour commitment',
                            'monthly_savings': annual_savings / 12,
                            'priority': 'high',
                            'details': {
                                'type': 'Compute SP',
                                'term': '1 Year',
                                'payment': 'All Upfront',
                                'hourly_commitment': hourly,
                                'annual_cost': hourly * 8760
                            }
                        })
                        potential_savings += annual_savings
            
            # Get EC2 Instance Savings Plan recommendations
            ec2_sp = self.ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='EC2_INSTANCE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT',
                LookbackPeriodInDays='SIXTY_DAYS'
            )
            
            if 'SavingsPlansPurchaseRecommendation' in ec2_sp:
                rec = ec2_sp['SavingsPlansPurchaseRecommendation']
                if 'HourlyCommitmentToPurchase' in rec:
                    hourly = float(rec['HourlyCommitmentToPurchase'])
                    annual_savings = float(rec.get('EstimatedSavingsAmount', 0))
                    
                    if hourly > 0 and annual_savings > 0:
                        recommendations.append({
                            'category': 'commitments',
                            'type': 'savings_plan',
                            'resource_id': 'ec2_instance_sp',
                            'recommendation': f'Purchase EC2 Instance Savings Plan with ${hourly:.2f}/hour commitment',
                            'monthly_savings': annual_savings / 12,
                            'priority': 'medium',
                            'details': {
                                'type': 'EC2 Instance SP',
                                'term': '1 Year',
                                'payment': 'No Upfront',
                                'hourly_commitment': hourly,
                                'annual_cost': hourly * 8760
                            }
                        })
                        potential_savings += annual_savings
            
            return {
                'recommendations': recommendations,
                'potential_savings': potential_savings
            }
            
        except Exception as e:
            return {
                'recommendations': [],
                'potential_savings': 0,
                'error': str(e)
            }
    
    def _analyze_savings_plans(self):
        """
        Analyze current Savings Plans coverage and utilization
        """
        try:
            # Get current Savings Plans
            current_sps = self.ce_client.describe_savings_plans()
            
            # Get utilization
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            utilization_response = self.ce_client.get_savings_plans_utilization(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY'
            )
            
            # Get coverage
            coverage_response = self.ce_client.get_savings_plans_coverage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY'
            )
            
            # Process results
            utilization = 0
            coverage = 0
            
            if 'SavingsPlansUtilizationsByTime' in utilization_response:
                for period in utilization_response['SavingsPlansUtilizationsByTime']:
                    if 'Utilization' in period:
                        utilization = float(period['Utilization'].get('UtilizationPercentage', 0))
            
            if 'SavingsPlansCoverages' in coverage_response:
                for period in coverage_response['SavingsPlansCoverages']:
                    if 'Coverage' in period:
                        coverage = float(period['Coverage'].get('CoveragePercentage', 0))
            
            return {
                'active_plans_count': len(current_sps.get('SavingsPlans', [])),
                'utilization_percentage': utilization,
                'coverage_percentage': coverage,
                'recommendations': self._get_savings_plan_recommendations()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'active_plans_count': 0,
                'utilization_percentage': 0,
                'coverage_percentage': 0
            }
    
    def _analyze_trends(self, start_date, end_date):
        """
        Analyze cost trends over time
        """
        try:
            # Get monthly costs for trend analysis
            monthly_response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': (start_date - timedelta(days=365)).strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            monthly_costs = []
            for result in monthly_response['ResultsByTime']:
                monthly_costs.append({
                    'month': result['TimePeriod']['Start'],
                    'cost': float(result['Metrics']['UnblendedCost']['Amount'])
                })
            
            # Calculate trends
            if len(monthly_costs) >= 2:
                # Month-over-month growth
                recent_months = monthly_costs[-3:]
                if len(recent_months) >= 2:
                    mom_growth = ((recent_months[-1]['cost'] / recent_months[-2]['cost']) - 1) * 100
                else:
                    mom_growth = 0
                
                # Year-over-year growth
                if len(monthly_costs) >= 13:
                    yoy_growth = ((monthly_costs[-1]['cost'] / monthly_costs[-13]['cost']) - 1) * 100
                else:
                    yoy_growth = 0
                
                # Average monthly cost
                avg_monthly = sum(m['cost'] for m in monthly_costs[-12:]) / min(12, len(monthly_costs))
                
                # Forecast next month (simple linear regression)
                if len(monthly_costs) >= 3:
                    recent_costs = [m['cost'] for m in monthly_costs[-3:]]
                    trend = (recent_costs[-1] - recent_costs[0]) / 2
                    next_month_forecast = recent_costs[-1] + trend
                else:
                    next_month_forecast = monthly_costs[-1]['cost'] if monthly_costs else 0
                
                return {
                    'monthly_costs': monthly_costs[-12:],  # Last 12 months
                    'month_over_month_growth': mom_growth,
                    'year_over_year_growth': yoy_growth,
                    'average_monthly_cost': avg_monthly,
                    'next_month_forecast': next_month_forecast,
                    'trend_direction': 'increasing' if mom_growth > 0 else 'decreasing'
                }
            else:
                return {
                    'monthly_costs': monthly_costs,
                    'month_over_month_growth': 0,
                    'year_over_year_growth': 0,
                    'average_monthly_cost': 0,
                    'next_month_forecast': 0,
                    'trend_direction': 'stable'
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'monthly_costs': [],
                'trend_direction': 'unknown'
            }
    
    def _analyze_top_services(self, start_date, end_date):
        """
        Analyze top cost-driving services
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            service_totals = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service not in service_totals:
                        service_totals[service] = 0
                    service_totals[service] += cost
            
            # Sort by cost
            sorted_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
            
            # Calculate total
            total_cost = sum(cost for _, cost in sorted_services)
            
            # Get top 10 with percentages
            top_services = []
            for service, cost in sorted_services[:10]:
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                top_services.append({
                    'service': service,
                    'cost': cost,
                    'percentage': percentage
                })
            
            # Others
            if len(sorted_services) > 10:
                others_cost = sum(cost for _, cost in sorted_services[10:])
                others_percentage = (others_cost / total_cost * 100) if total_cost > 0 else 0
                top_services.append({
                    'service': 'Others',
                    'cost': others_cost,
                    'percentage': others_percentage
                })
            
            return {
                'top_services': top_services,
                'total_cost': total_cost,
                'service_count': len(service_totals)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'top_services': [],
                'total_cost': 0
            }
    
    def _find_untagged_resources(self):
        """
        Find resources missing required tags
        """
        try:
            untagged_resources = []
            required_tags = ['Environment', 'Owner', 'CostCenter', 'Project']
            
            # Check EC2 instances
            instances = self.ec2_client.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        missing_tags = [tag for tag in required_tags if tag not in tags]
                        
                        if missing_tags:
                            untagged_resources.append({
                                'resource_type': 'EC2 Instance',
                                'resource_id': instance['InstanceId'],
                                'missing_tags': missing_tags,
                                'existing_tags': tags,
                                'state': instance['State']['Name']
                            })
            
            # Check EBS volumes
            volumes = self.ec2_client.describe_volumes()
            for volume in volumes['Volumes']:
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                missing_tags = [tag for tag in required_tags if tag not in tags]
                
                if missing_tags:
                    untagged_resources.append({
                        'resource_type': 'EBS Volume',
                        'resource_id': volume['VolumeId'],
                        'missing_tags': missing_tags,
                        'existing_tags': tags,
                        'state': volume['State']
                    })
            
            # Check RDS instances
            db_instances = self.rds_client.describe_db_instances()
            for db in db_instances['DBInstances']:
                # Get tags for RDS instance
                tags_response = self.rds_client.list_tags_for_resource(
                    ResourceName=db['DBInstanceArn']
                )
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
                missing_tags = [tag for tag in required_tags if tag not in tags]
                
                if missing_tags:
                    untagged_resources.append({
                        'resource_type': 'RDS Instance',
                        'resource_id': db['DBInstanceIdentifier'],
                        'missing_tags': missing_tags,
                        'existing_tags': tags,
                        'state': db['DBInstanceStatus']
                    })
            
            # Check S3 buckets
            buckets = self.s3_client.list_buckets()
            for bucket in buckets['Buckets']:
                try:
                    tags_response = self.s3_client.get_bucket_tagging(Bucket=bucket['Name'])
                    tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
                except self.s3_client.exceptions.NoSuchTagSet:
                    tags = {}
                except:
                    continue
                
                missing_tags = [tag for tag in required_tags if tag not in tags]
                
                if missing_tags:
                    untagged_resources.append({
                        'resource_type': 'S3 Bucket',
                        'resource_id': bucket['Name'],
                        'missing_tags': missing_tags,
                        'existing_tags': tags,
                        'state': 'active'
                    })
            
            # Summary statistics
            summary = {
                'total_untagged': len(untagged_resources),
                'by_type': {},
                'by_missing_tag': {}
            }
            
            for resource in untagged_resources:
                # By type
                res_type = resource['resource_type']
                if res_type not in summary['by_type']:
                    summary['by_type'][res_type] = 0
                summary['by_type'][res_type] += 1
                
                # By missing tag
                for tag in resource['missing_tags']:
                    if tag not in summary['by_missing_tag']:
                        summary['by_missing_tag'][tag] = 0
                    summary['by_missing_tag'][tag] += 1
            
            return {
                'untagged_resources': untagged_resources[:100],  # Limit to 100 for report
                'summary': summary,
                'required_tags': required_tags
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'untagged_resources': [],
                'summary': {}
            }
    
    def _detect_cost_anomalies(self, start_date, end_date):
        """
        Detect cost anomalies in the period
        """
        try:
            # Get daily costs
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            daily_costs = []
            for result in response['ResultsByTime']:
                cost_amount = 0.0
                if 'Metrics' in result and 'UnblendedCost' in result['Metrics']:
                    cost_amount = float(result['Metrics']['UnblendedCost']['Amount'])
                
                daily_costs.append({
                    'date': result['TimePeriod']['Start'],
                    'cost': cost_amount
                })
            
            if len(daily_costs) < 7:
                return {
                    'anomalies': [], 
                    'message': 'Not enough data for anomaly detection',
                    'average_daily_cost': 0,
                    'standard_deviation': 0,
                    'anomaly_count': 0
                }
            
            # Calculate statistics
            costs = [d['cost'] for d in daily_costs]
            mean_cost = np.mean(costs)
            std_cost = np.std(costs)
            
            # Detect anomalies (costs > 2 standard deviations from mean)
            anomalies = []
            for day in daily_costs:
                if abs(day['cost'] - mean_cost) > 2 * std_cost:
                    # Get service breakdown for anomaly day
                    service_response = self.ce_client.get_cost_and_usage(
                        TimePeriod={
                            'Start': day['date'],
                            'End': (datetime.strptime(day['date'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                        },
                        Granularity='DAILY',
                        Metrics=['UnblendedCost'],
                        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                    )
                    
                    top_services = []
                    for result in service_response['ResultsByTime']:
                        for group in result['Groups'][:5]:  # Top 5 services
                            top_services.append({
                                'service': group['Keys'][0],
                                'cost': float(group['Metrics']['UnblendedCost']['Amount'])
                            })
                    
                    anomalies.append({
                        'date': day['date'],
                        'cost': day['cost'],
                        'deviation': (day['cost'] - mean_cost) / std_cost,
                        'percentage_above_average': ((day['cost'] / mean_cost) - 1) * 100,
                        'top_services': top_services
                    })
            
            return {
                'anomalies': anomalies,
                'average_daily_cost': mean_cost,
                'standard_deviation': std_cost,
                'anomaly_count': len(anomalies)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'anomalies': [],
                'anomaly_count': 0
            }
    
    def _generate_pdf_report(self, report_data, include_charts=True):
        """
        Generate PDF report
        """
        # Create PDF buffer
        pdf_buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30
        )
        elements.append(Paragraph("FinOps Management Report", title_style))
        
        # Metadata
        elements.append(Paragraph(f"Generated: {report_data['metadata']['generated_at']}", styles['Normal']))
        elements.append(Paragraph(f"Period: {report_data['metadata']['period']}", styles['Normal']))
        elements.append(Paragraph(f"Account: {report_data['metadata']['account_id']}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", styles['Heading1']))
        
        cost_analysis = report_data.get('cost_analysis', {})
        if 'total_cost' in cost_analysis:
            summary_data = [
                ['Metric', 'Value'],
                ['Total Cost', f"${cost_analysis['total_cost']:,.2f}"],
                ['Average Daily Cost', f"${cost_analysis.get('average_daily_cost', 0):,.2f}"],
                ['Tag Compliance Rate', f"{report_data.get('resource_tagging', {}).get('compliance_rate', 0):.1f}%"],
                ['Potential Monthly Savings', f"${report_data.get('optimization_recommendations', {}).get('monthly_savings', 0):,.2f}"]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
        
        elements.append(PageBreak())
        
        # Cost Analysis Section
        elements.append(Paragraph("Cost Analysis", styles['Heading1']))
        
        # Top Services
        if 'top_services_breakdown' in report_data:
            elements.append(Paragraph("Top Services by Cost", styles['Heading2']))
            top_services = report_data['top_services_breakdown'].get('top_services', [])
            
            if top_services:
                service_data = [['Service', 'Cost', 'Percentage']]
                for service in top_services[:10]:
                    service_data.append([
                        service['service'][:30],
                        f"${service['cost']:,.2f}",
                        f"{service['percentage']:.1f}%"
                    ])
                
                service_table = Table(service_data)
                service_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(service_table)
        
        elements.append(Spacer(1, 20))
        
        # Trend Analysis
        if 'trend_analysis' in report_data:
            elements.append(Paragraph("Trend Analysis", styles['Heading2']))
            trends = report_data['trend_analysis']
            
            trend_text = f"""
            • Month-over-Month Growth: {trends.get('month_over_month_growth', 0):.1f}%
            • Year-over-Year Growth: {trends.get('year_over_year_growth', 0):.1f}%
            • Average Monthly Cost: ${trends.get('average_monthly_cost', 0):,.2f}
            • Next Month Forecast: ${trends.get('next_month_forecast', 0):,.2f}
            • Trend Direction: {trends.get('trend_direction', 'Unknown').upper()}
            """
            elements.append(Paragraph(trend_text, styles['BodyText']))
        
        elements.append(PageBreak())
        
        # Resource Tagging Compliance
        elements.append(Paragraph("Resource Tagging Compliance", styles['Heading1']))
        
        if 'resource_tagging' in report_data:
            tagging = report_data['resource_tagging']
            
            if 'compliance_rate' in tagging:
                compliance_text = f"""
                Total Resources: {tagging.get('total_resources', 0)}
                Tagged Resources: {tagging.get('tagged_resources', 0)}
                Untagged Resources: {tagging.get('untagged_resources', 0)}
                Compliance Rate: {tagging.get('compliance_rate', 0):.1f}%
                """
                elements.append(Paragraph(compliance_text, styles['BodyText']))
            
            # Untagged resources by type
            if 'resources_by_type' in tagging:
                elements.append(Paragraph("Resources by Type", styles['Heading2']))
                type_data = [['Resource Type', 'Tagged', 'Untagged', 'Total']]
                
                for res_type, counts in tagging['resources_by_type'].items():
                    type_data.append([
                        res_type,
                        str(counts.get('tagged', 0)),
                        str(counts.get('untagged', 0)),
                        str(counts.get('total', 0))
                    ])
                
                type_table = Table(type_data)
                type_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(type_table)
        
        elements.append(PageBreak())
        
        # Optimization Recommendations
        elements.append(Paragraph("Cost Optimization Recommendations", styles['Heading1']))
        
        if 'optimization_recommendations' in report_data:
            opt = report_data['optimization_recommendations']
            
            if 'total_potential_savings' in opt:
                savings_text = f"""
                Total Annual Savings Potential: ${opt['total_potential_savings']:,.2f}
                Monthly Savings Potential: ${opt.get('monthly_savings', 0):,.2f}
                """
                elements.append(Paragraph(savings_text, styles['BodyText']))
            
            # Top recommendations
            if 'recommendations' in opt and opt['recommendations']:
                elements.append(Paragraph("Top Recommendations", styles['Heading2']))
                
                # Sort by savings
                sorted_recs = sorted(opt['recommendations'], 
                                   key=lambda x: x.get('monthly_savings', 0), 
                                   reverse=True)[:10]
                
                for i, rec in enumerate(sorted_recs, 1):
                    rec_text = f"""
                    {i}. {rec['recommendation']}
                    Category: {rec['category']} | Priority: {rec['priority'].upper()}
                    Monthly Savings: ${rec.get('monthly_savings', 0):,.2f}
                    """
                    elements.append(Paragraph(rec_text, styles['BodyText']))
                    elements.append(Spacer(1, 10))
        
        elements.append(PageBreak())
        
        # Cost Anomalies
        if 'cost_anomalies' in report_data:
            elements.append(Paragraph("Cost Anomalies", styles['Heading1']))
            anomalies = report_data['cost_anomalies']
            
            if 'anomaly_count' in anomalies and anomalies['anomaly_count'] > 0:
                elements.append(Paragraph(f"Detected {anomalies['anomaly_count']} anomalies", styles['BodyText']))
                
                for anomaly in anomalies.get('anomalies', [])[:5]:
                    anomaly_text = f"""
                    Date: {anomaly['date']}
                    Cost: ${anomaly['cost']:,.2f}
                    Deviation: {anomaly['percentage_above_average']:.1f}% above average
                    """
                    elements.append(Paragraph(anomaly_text, styles['BodyText']))
            else:
                elements.append(Paragraph("No significant cost anomalies detected", styles['BodyText']))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _generate_excel_report(self, report_data, include_charts=True):
        """
        Generate Excel report
        """
        # Create Excel buffer
        excel_buffer = io.BytesIO()
        
        # Create workbook
        with xlsxwriter.Workbook(excel_buffer, {'in_memory': True}) as workbook:
            # Formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({'num_format': '$#,##0.00'})
            percent_format = workbook.add_format({'num_format': '0.0%'})
            
            # Summary sheet
            summary_sheet = workbook.add_worksheet('Executive Summary')
            
            # Write summary data
            summary_sheet.write('A1', 'FinOps Management Report', header_format)
            summary_sheet.write('A3', 'Report Period:', header_format)
            summary_sheet.write('B3', report_data['metadata']['period'])
            summary_sheet.write('A4', 'Generated At:', header_format)
            summary_sheet.write('B4', report_data['metadata']['generated_at'])
            summary_sheet.write('A5', 'Account ID:', header_format)
            summary_sheet.write('B5', report_data['metadata']['account_id'])
            
            # Key metrics
            summary_sheet.write('A7', 'Key Metrics', header_format)
            
            cost_analysis = report_data.get('cost_analysis', {})
            summary_sheet.write('A8', 'Total Cost:')
            summary_sheet.write('B8', cost_analysis.get('total_cost', 0), currency_format)
            summary_sheet.write('A9', 'Average Daily Cost:')
            summary_sheet.write('B9', cost_analysis.get('average_daily_cost', 0), currency_format)
            summary_sheet.write('A10', 'Tag Compliance Rate:')
            summary_sheet.write('B10', report_data.get('resource_tagging', {}).get('compliance_rate', 0) / 100, percent_format)
            summary_sheet.write('A11', 'Monthly Savings Potential:')
            summary_sheet.write('B11', report_data.get('optimization_recommendations', {}).get('monthly_savings', 0), currency_format)
            
            # Cost Analysis sheet
            if 'cost_analysis' in report_data and 'daily_costs' in report_data['cost_analysis']:
                cost_sheet = workbook.add_worksheet('Cost Analysis')
                
                # Daily costs
                cost_sheet.write('A1', 'Daily Cost Trend', header_format)
                cost_sheet.write('A2', 'Date', header_format)
                cost_sheet.write('B2', 'Cost', header_format)
                
                row = 2
                for day in report_data['cost_analysis']['daily_costs']:
                    cost_sheet.write(row, 0, day['date'])
                    cost_sheet.write(row, 1, day['cost'], currency_format)
                    row += 1
                
                # Add chart if requested
                if include_charts and len(report_data['cost_analysis']['daily_costs']) > 0:
                    chart = workbook.add_chart({'type': 'line'})
                    chart.add_series({
                        'categories': ['Cost Analysis', 2, 0, row-1, 0],
                        'values': ['Cost Analysis', 2, 1, row-1, 1],
                        'name': 'Daily Cost'
                    })
                    chart.set_title({'name': 'Daily Cost Trend'})
                    chart.set_x_axis({'name': 'Date'})
                    chart.set_y_axis({'name': 'Cost ($)'})
                    cost_sheet.insert_chart('D2', chart, {'width': 480, 'height': 360})
            
            # Service Breakdown sheet
            if 'top_services_breakdown' in report_data:
                service_sheet = workbook.add_worksheet('Service Breakdown')
                
                service_sheet.write('A1', 'Top Services by Cost', header_format)
                service_sheet.write('A2', 'Service', header_format)
                service_sheet.write('B2', 'Cost', header_format)
                service_sheet.write('C2', 'Percentage', header_format)
                
                row = 2
                for service in report_data['top_services_breakdown'].get('top_services', []):
                    service_sheet.write(row, 0, service['service'])
                    service_sheet.write(row, 1, service['cost'], currency_format)
                    service_sheet.write(row, 2, service['percentage'] / 100, percent_format)
                    row += 1
            
            # Tagging Compliance sheet
            if 'untagged_resources' in report_data:
                tagging_sheet = workbook.add_worksheet('Tagging Compliance')
                
                tagging_sheet.write('A1', 'Untagged Resources', header_format)
                tagging_sheet.write('A2', 'Resource Type', header_format)
                tagging_sheet.write('B2', 'Resource ID', header_format)
                tagging_sheet.write('C2', 'Missing Tags', header_format)
                tagging_sheet.write('D2', 'State', header_format)
                
                row = 2
                for resource in report_data['untagged_resources'].get('untagged_resources', [])[:100]:
                    tagging_sheet.write(row, 0, resource.get('resource_type', ''))
                    tagging_sheet.write(row, 1, resource.get('resource_id', ''))
                    tagging_sheet.write(row, 2, ', '.join(resource.get('missing_tags', [])))
                    tagging_sheet.write(row, 3, resource.get('state', ''))
                    row += 1
            
            # Optimization Recommendations sheet
            if 'optimization_recommendations' in report_data:
                opt_sheet = workbook.add_worksheet('Optimizations')
                
                opt_sheet.write('A1', 'Cost Optimization Recommendations', header_format)
                opt_sheet.write('A2', 'Category', header_format)
                opt_sheet.write('B2', 'Type', header_format)
                opt_sheet.write('C2', 'Resource', header_format)
                opt_sheet.write('D2', 'Recommendation', header_format)
                opt_sheet.write('E2', 'Monthly Savings', header_format)
                opt_sheet.write('F2', 'Priority', header_format)
                
                row = 2
                for rec in report_data['optimization_recommendations'].get('recommendations', []):
                    opt_sheet.write(row, 0, rec.get('category', ''))
                    opt_sheet.write(row, 1, rec.get('type', ''))
                    opt_sheet.write(row, 2, rec.get('resource_id', ''))
                    opt_sheet.write(row, 3, rec.get('recommendation', ''))
                    opt_sheet.write(row, 4, rec.get('monthly_savings', 0), currency_format)
                    opt_sheet.write(row, 5, rec.get('priority', ''))
                    row += 1
            
            # Auto-fit columns
            for sheet in [summary_sheet, cost_sheet if 'cost_analysis' in report_data else None,
                         service_sheet if 'top_services_breakdown' in report_data else None,
                         tagging_sheet if 'untagged_resources' in report_data else None,
                         opt_sheet if 'optimization_recommendations' in report_data else None]:
                if sheet:
                    sheet.autofit()
        
        # Get Excel data
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    # Helper methods
    def _get_resource_type_from_arn(self, arn):
        """Extract resource type from ARN"""
        try:
            parts = arn.split(':')
            if len(parts) >= 6:
                service = parts[2]
                resource_part = parts[5]
                
                if '/' in resource_part:
                    resource_type = resource_part.split('/')[0]
                else:
                    resource_type = resource_part
                
                return f"{service}:{resource_type}"
            return 'unknown'
        except:
            return 'unknown'
    
    def _estimate_stopped_instance_cost(self, instance):
        """Estimate monthly cost for stopped instance (EBS volumes)"""
        total_cost = 0
        
        for mapping in instance.get('BlockDeviceMappings', []):
            if 'Ebs' in mapping:
                volume_size = mapping['Ebs'].get('VolumeSize', 8)  # Default 8 GB
                volume_type = mapping['Ebs'].get('VolumeType', 'gp2')
                total_cost += self._estimate_ebs_monthly_cost(volume_size, volume_type)
        
        return total_cost
    
    def _estimate_ebs_monthly_cost(self, size_gb, volume_type):
        """Estimate monthly cost for EBS volume"""
        # Rough pricing estimates
        pricing = {
            'gp2': 0.10,  # $0.10 per GB-month
            'gp3': 0.08,  # $0.08 per GB-month
            'io1': 0.125, # $0.125 per GB-month
            'io2': 0.125, # $0.125 per GB-month
            'st1': 0.045, # $0.045 per GB-month
            'sc1': 0.025  # $0.025 per GB-month
        }
        
        price_per_gb = pricing.get(volume_type, 0.10)
        return size_gb * price_per_gb
    
    def _estimate_instance_monthly_cost(self, instance_type):
        """Estimate monthly cost for EC2 instance"""
        # Rough pricing estimates for common instance types
        pricing = {
            't2.micro': 8.50,
            't2.small': 17.00,
            't2.medium': 34.00,
            't2.large': 68.00,
            't3.micro': 7.50,
            't3.small': 15.00,
            't3.medium': 30.00,
            't3.large': 60.00,
            'm5.large': 70.00,
            'm5.xlarge': 140.00,
            'm5.2xlarge': 280.00,
            'c5.large': 62.00,
            'c5.xlarge': 124.00,
            'c5.2xlarge': 248.00
        }
        
        # Default to t3.medium pricing if unknown
        return pricing.get(instance_type, 30.00) * 24 * 30  # Convert hourly to monthly
    
    def _get_smaller_instance_type(self, current_type):
        """Get recommended smaller instance type"""
        downsizing_map = {
            't2.large': 't2.medium',
            't2.medium': 't2.small',
            't2.small': 't2.micro',
            't3.large': 't3.medium',
            't3.medium': 't3.small',
            't3.small': 't3.micro',
            'm5.2xlarge': 'm5.xlarge',
            'm5.xlarge': 'm5.large',
            'm5.large': 't3.large',
            'c5.2xlarge': 'c5.xlarge',
            'c5.xlarge': 'c5.large',
            'c5.large': 't3.large'
        }
        
        return downsizing_map.get(current_type)
    
    def _estimate_rds_monthly_cost(self, db_class, engine, multi_az=False):
        """Estimate monthly cost for RDS instance"""
        # Rough pricing estimates
        base_pricing = {
            'db.t2.micro': 15.00,
            'db.t2.small': 30.00,
            'db.t2.medium': 60.00,
            'db.t3.micro': 13.00,
            'db.t3.small': 26.00,
            'db.t3.medium': 52.00,
            'db.m5.large': 90.00,
            'db.m5.xlarge': 180.00
        }
        
        monthly_cost = base_pricing.get(db_class, 50.00) * 24 * 30
        
        # Multi-AZ doubles the cost
        if multi_az:
            monthly_cost *= 2
        
        return monthly_cost
    
    def _get_instance_cpu_utilization(self, instance_id):
        """Get average CPU utilization for instance"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.now() - timedelta(days=7),
                EndTime=datetime.now(),
                Period=3600,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return sum(d['Average'] for d in response['Datapoints']) / len(response['Datapoints'])
            return None
        except:
            return None
    
    def _analyze_by_day_of_week(self, daily_costs):
        """Analyze costs by day of week"""
        day_totals = {}
        day_counts = {}
        
        for day_data in daily_costs:
            date = datetime.strptime(day_data['date'], '%Y-%m-%d')
            day_name = date.strftime('%A')
            
            if day_name not in day_totals:
                day_totals[day_name] = 0
                day_counts[day_name] = 0
            
            day_totals[day_name] += day_data['cost']
            day_counts[day_name] += 1
        
        # Calculate averages
        day_averages = {}
        for day, total in day_totals.items():
            day_averages[day] = total / day_counts[day] if day_counts[day] > 0 else 0
        
        return day_averages