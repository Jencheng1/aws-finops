import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TaggingComplianceAnalyzer:
    def __init__(self):
        self.resource_groups_tagging = boto3.client('resourcegroupstaggingapi')
        self.ec2_client = boto3.client('ec2')
        self.rds_client = boto3.client('rds')
        self.s3_client = boto3.client('s3')
        self.ce_client = boto3.client('ce')
        
        # Define required tags for compliance
        self.required_tags = {
            'Environment': ['Production', 'Staging', 'Development', 'Test'],
            'Owner': None,  # Any value accepted
            'Project': None,  # Any value accepted
            'CostCenter': None,  # Any value accepted
            'Application': None  # Any value accepted
        }
        
    def get_all_resources(self, resource_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get all resources with their tags"""
        try:
            if not resource_types:
                resource_types = [
                    'ec2:instance',
                    's3:bucket',
                    'rds:db',
                    'lambda:function',
                    'elasticloadbalancing:loadbalancer'
                ]
            
            all_resources = []
            paginator = self.resource_groups_tagging.get_paginator('get_resources')
            
            for resource_type in resource_types:
                try:
                    page_iterator = paginator.paginate(
                        ResourceTypeFilters=[resource_type]
                    )
                    
                    for page in page_iterator:
                        for resource in page['ResourceTagMappingList']:
                            tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                            
                            all_resources.append({
                                'resource_arn': resource['ResourceARN'],
                                'resource_type': resource_type,
                                'tags': tags
                            })
                except Exception as e:
                    logger.warning(f"Error getting resources for type {resource_type}: {str(e)}")
                    
            return all_resources
            
        except Exception as e:
            logger.error(f"Error getting resources: {str(e)}")
            return []
    
    def analyze_tag_compliance(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tag compliance for resources"""
        try:
            compliance_summary = {
                'total_resources': len(resources),
                'compliant_resources': 0,
                'non_compliant_resources': 0,
                'partially_compliant_resources': 0,
                'compliance_by_tag': defaultdict(lambda: {'present': 0, 'missing': 0}),
                'compliance_by_resource_type': defaultdict(lambda: {'total': 0, 'compliant': 0}),
                'missing_tags_detail': []
            }
            
            for resource in resources:
                resource_type = resource['resource_type']
                resource_tags = resource.get('tags', {})
                missing_tags = []
                invalid_tags = []
                
                # Check each required tag
                for required_tag, allowed_values in self.required_tags.items():
                    if required_tag not in resource_tags:
                        missing_tags.append(required_tag)
                        compliance_summary['compliance_by_tag'][required_tag]['missing'] += 1
                    else:
                        compliance_summary['compliance_by_tag'][required_tag]['present'] += 1
                        
                        # Check if tag value is valid (if allowed values are specified)
                        if allowed_values and resource_tags[required_tag] not in allowed_values:
                            invalid_tags.append({
                                'tag': required_tag,
                                'value': resource_tags[required_tag],
                                'allowed_values': allowed_values
                            })
                
                # Update compliance counts
                compliance_summary['compliance_by_resource_type'][resource_type]['total'] += 1
                
                if not missing_tags and not invalid_tags:
                    compliance_summary['compliant_resources'] += 1
                    compliance_summary['compliance_by_resource_type'][resource_type]['compliant'] += 1
                elif len(missing_tags) == len(self.required_tags):
                    compliance_summary['non_compliant_resources'] += 1
                else:
                    compliance_summary['partially_compliant_resources'] += 1
                
                # Add to missing tags detail
                if missing_tags or invalid_tags:
                    compliance_summary['missing_tags_detail'].append({
                        'resource_arn': resource['resource_arn'],
                        'resource_type': resource_type,
                        'missing_tags': missing_tags,
                        'invalid_tags': invalid_tags,
                        'existing_tags': resource_tags
                    })
            
            # Calculate compliance percentage
            compliance_summary['compliance_percentage'] = (
                compliance_summary['compliant_resources'] / compliance_summary['total_resources'] * 100
                if compliance_summary['total_resources'] > 0 else 0
            )
            
            return compliance_summary
            
        except Exception as e:
            logger.error(f"Error analyzing tag compliance: {str(e)}")
            return {}
    
    def get_untagged_resource_costs(self, days: int = 30) -> Dict[str, Any]:
        """Get costs for resources without required tags"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            costs_by_missing_tag = {}
            
            # Get cost data grouped by tags
            for required_tag in self.required_tags:
                try:
                    response = self.ce_client.get_cost_and_usage(
                        TimePeriod={
                            'Start': start_date.strftime('%Y-%m-%d'),
                            'End': end_date.strftime('%Y-%m-%d')
                        },
                        Granularity='MONTHLY',
                        Metrics=['UnblendedCost'],
                        GroupBy=[
                            {
                                'Type': 'TAG',
                                'Key': required_tag
                            }
                        ]
                    )
                    
                    untagged_cost = 0
                    tagged_cost = 0
                    
                    for result in response['ResultsByTime']:
                        for group in result['Groups']:
                            # Cost Explorer returns empty key for untagged resources
                            if not group['Keys'][0] or group['Keys'][0] == f'{required_tag}$':
                                untagged_cost += float(group['Metrics']['UnblendedCost']['Amount'])
                            else:
                                tagged_cost += float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    costs_by_missing_tag[required_tag] = {
                        'untagged_cost': untagged_cost,
                        'tagged_cost': tagged_cost,
                        'total_cost': untagged_cost + tagged_cost,
                        'untagged_percentage': (untagged_cost / (untagged_cost + tagged_cost) * 100) if (untagged_cost + tagged_cost) > 0 else 0
                    }
                    
                except Exception as e:
                    logger.warning(f"Error getting cost data for tag {required_tag}: {str(e)}")
                    costs_by_missing_tag[required_tag] = {'error': str(e)}
            
            # Calculate total untagged costs
            total_untagged_cost = sum(
                data.get('untagged_cost', 0) 
                for data in costs_by_missing_tag.values() 
                if 'error' not in data
            )
            
            return {
                'costs_by_missing_tag': costs_by_missing_tag,
                'total_untagged_cost': total_untagged_cost,
                'analysis_period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting untagged resource costs: {str(e)}")
            return {}
    
    def get_tag_value_distribution(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze distribution of tag values"""
        try:
            tag_distribution = defaultdict(lambda: defaultdict(int))
            
            for resource in resources:
                for tag_key, tag_value in resource.get('tags', {}).items():
                    if tag_key in self.required_tags:
                        tag_distribution[tag_key][tag_value] += 1
            
            # Convert to regular dict and calculate percentages
            distribution_summary = {}
            for tag_key, values in tag_distribution.items():
                total_count = sum(values.values())
                distribution_summary[tag_key] = {
                    'values': dict(values),
                    'unique_values': len(values),
                    'total_tagged': total_count,
                    'top_values': sorted(values.items(), key=lambda x: x[1], reverse=True)[:5]
                }
            
            return distribution_summary
            
        except Exception as e:
            logger.error(f"Error analyzing tag distribution: {str(e)}")
            return {}
    
    def identify_tagging_opportunities(self, compliance_summary: Dict[str, Any], 
                                     cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify tagging improvement opportunities"""
        opportunities = []
        
        # High-cost untagged resources
        if cost_data.get('total_untagged_cost', 0) > 100:
            opportunities.append({
                'type': 'high_cost_untagged',
                'monthly_cost': cost_data['total_untagged_cost'],
                'recommendation': f"Resources costing ${cost_data['total_untagged_cost']:.2f}/month lack required tags",
                'priority': 'high',
                'impact': 'cost_allocation'
            })
        
        # Low compliance rate
        compliance_percentage = compliance_summary.get('compliance_percentage', 0)
        if compliance_percentage < 80:
            opportunities.append({
                'type': 'low_compliance_rate',
                'compliance_percentage': compliance_percentage,
                'non_compliant_count': compliance_summary.get('non_compliant_resources', 0),
                'recommendation': f"Only {compliance_percentage:.1f}% of resources are fully compliant with tagging policy",
                'priority': 'high' if compliance_percentage < 50 else 'medium',
                'impact': 'governance'
            })
        
        # Missing critical tags
        for tag, data in compliance_summary.get('compliance_by_tag', {}).items():
            missing_percentage = (data['missing'] / (data['present'] + data['missing']) * 100) if (data['present'] + data['missing']) > 0 else 0
            
            if missing_percentage > 20:
                # Check cost impact
                tag_cost_data = cost_data.get('costs_by_missing_tag', {}).get(tag, {})
                untagged_cost = tag_cost_data.get('untagged_cost', 0)
                
                opportunities.append({
                    'type': 'missing_required_tag',
                    'tag': tag,
                    'missing_percentage': missing_percentage,
                    'resources_missing': data['missing'],
                    'monthly_untagged_cost': untagged_cost,
                    'recommendation': f"{missing_percentage:.1f}% of resources missing '{tag}' tag",
                    'priority': 'high' if tag in ['Environment', 'Owner'] else 'medium',
                    'impact': 'cost_allocation_and_governance'
                })
        
        # Resource type specific opportunities
        for resource_type, data in compliance_summary.get('compliance_by_resource_type', {}).items():
            if data['total'] > 0:
                compliance_rate = (data['compliant'] / data['total'] * 100)
                if compliance_rate < 70:
                    opportunities.append({
                        'type': 'resource_type_compliance',
                        'resource_type': resource_type,
                        'compliance_rate': compliance_rate,
                        'non_compliant_count': data['total'] - data['compliant'],
                        'recommendation': f"{resource_type} resources have only {compliance_rate:.1f}% tagging compliance",
                        'priority': 'medium',
                        'impact': 'governance'
                    })
        
        return opportunities
    
    def generate_tagging_report(self, resources: List[Dict[str, Any]], 
                              days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive tagging compliance report"""
        try:
            # Analyze compliance
            compliance_summary = self.analyze_tag_compliance(resources)
            
            # Get cost data
            cost_data = self.get_untagged_resource_costs(days)
            
            # Get tag distribution
            tag_distribution = self.get_tag_value_distribution(resources)
            
            # Identify opportunities
            opportunities = self.identify_tagging_opportunities(compliance_summary, cost_data)
            
            # Generate tag remediation plan
            remediation_plan = []
            for detail in compliance_summary.get('missing_tags_detail', [])[:20]:  # Top 20
                remediation_plan.append({
                    'resource': detail['resource_arn'],
                    'action': 'add_tags',
                    'tags_to_add': detail['missing_tags'],
                    'priority': 'high' if len(detail['missing_tags']) >= 3 else 'medium'
                })
            
            return {
                'compliance_summary': compliance_summary,
                'cost_analysis': cost_data,
                'tag_distribution': tag_distribution,
                'opportunities': opportunities,
                'remediation_plan': remediation_plan
            }
            
        except Exception as e:
            logger.error(f"Error generating tagging report: {str(e)}")
            return {}

def lambda_handler(event, context):
    """AWS Lambda handler for tagging compliance analysis"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize the analyzer
        analyzer = TaggingComplianceAnalyzer()
        
        # Extract parameters from the event
        action = event.get('action', 'analyze_all')
        resource_types = event.get('resource_types', None)
        days = event.get('days', 30)
        
        # Get all resources
        resources = analyzer.get_all_resources(resource_types)
        
        if action == 'check_compliance':
            compliance_summary = analyzer.analyze_tag_compliance(resources)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'compliance_summary': compliance_summary,
                    'resource_count': len(resources)
                })
            }
            
        elif action == 'analyze_costs':
            cost_data = analyzer.get_untagged_resource_costs(days)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'cost_analysis': cost_data,
                    'analysis_period_days': days
                })
            }
            
        elif action == 'get_distribution':
            tag_distribution = analyzer.get_tag_value_distribution(resources)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'tag_distribution': tag_distribution,
                    'resource_count': len(resources)
                })
            }
            
        elif action == 'analyze_all':
            # Generate comprehensive report
            report = analyzer.generate_tagging_report(resources, days)
            
            # Calculate summary metrics
            compliance_summary = report.get('compliance_summary', {})
            cost_analysis = report.get('cost_analysis', {})
            opportunities = report.get('opportunities', [])
            
            # Count high priority items
            high_priority_count = sum(1 for opp in opportunities if opp.get('priority') == 'high')
            
            # Calculate potential savings (from better cost allocation)
            total_untagged_cost = cost_analysis.get('total_untagged_cost', 0)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': action,
                    'summary': {
                        'total_resources': compliance_summary.get('total_resources', 0),
                        'compliance_percentage': compliance_summary.get('compliance_percentage', 0),
                        'non_compliant_resources': compliance_summary.get('non_compliant_resources', 0),
                        'monthly_untagged_cost': total_untagged_cost,
                        'high_priority_recommendations': high_priority_count,
                        'total_recommendations': len(opportunities)
                    },
                    'compliance_summary': compliance_summary,
                    'cost_analysis': cost_analysis,
                    'tag_distribution': report.get('tag_distribution', {}),
                    'recommendations': opportunities,
                    'remediation_plan': report.get('remediation_plan', []),
                    'analysis_period_days': days
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'supported_actions': ['check_compliance', 'analyze_costs', 'get_distribution', 'analyze_all']
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