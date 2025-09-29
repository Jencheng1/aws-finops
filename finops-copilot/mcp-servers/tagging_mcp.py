#!/usr/bin/env python3
"""
Tagging MCP Server

This MCP server provides access to AWS resource tagging information through the Model Context Protocol.
It exposes tagging compliance and cost allocation capabilities to AI agents and applications.
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

class TaggingMCPServer:
    """MCP Server for AWS Resource Tagging integration"""
    
    def __init__(self):
        """Initialize the Tagging MCP Server"""
        try:
            self.resource_groups_client = boto3.client('resourcegroupstaggingapi')
            self.ec2_client = boto3.client('ec2')
            self.s3_client = boto3.client('s3')
            self.rds_client = boto3.client('rds')
            self.cost_explorer_client = boto3.client('ce')
            logger.info("Tagging MCP Server initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing Tagging clients: {str(e)}")
            raise
    
    async def get_resources_by_tags(self, 
                                   tag_filters: List[Dict[str, Any]] = None,
                                   resource_type_filters: List[str] = None,
                                   include_compliance_details: bool = True) -> Dict[str, Any]:
        """
        Get AWS resources filtered by tags
        
        Args:
            tag_filters: List of tag filters to apply
            resource_type_filters: List of resource types to include
            include_compliance_details: Whether to include compliance analysis
        
        Returns:
            Dict containing filtered resources and their tags
        """
        try:
            params = {}
            
            if tag_filters:
                params['TagFilters'] = tag_filters
            if resource_type_filters:
                params['ResourceTypeFilters'] = resource_type_filters
            
            # Use paginator to handle large result sets
            paginator = self.resource_groups_client.get_paginator('get_resources')
            page_iterator = paginator.paginate(**params)
            
            all_resources = []
            resource_summary = {}
            
            for page in page_iterator:
                resources = page.get('ResourceTagMappingList', [])
                all_resources.extend(resources)
                
                # Build resource type summary
                for resource in resources:
                    resource_arn = resource.get('ResourceARN', '')
                    resource_type = self._extract_resource_type(resource_arn)
                    
                    if resource_type not in resource_summary:
                        resource_summary[resource_type] = {
                            'count': 0,
                            'tagged_count': 0,
                            'untagged_count': 0
                        }
                    
                    resource_summary[resource_type]['count'] += 1
                    
                    tags = resource.get('Tags', [])
                    if tags:
                        resource_summary[resource_type]['tagged_count'] += 1
                    else:
                        resource_summary[resource_type]['untagged_count'] += 1
            
            result = {
                'resources': all_resources,
                'total_count': len(all_resources),
                'resource_summary': resource_summary,
                'filters_applied': {
                    'tag_filters': tag_filters,
                    'resource_type_filters': resource_type_filters
                }
            }
            
            if include_compliance_details:
                result['compliance_analysis'] = await self._analyze_tagging_compliance(all_resources)
            
            return result
            
        except ClientError as e:
            logger.error(f"AWS API error in get_resources_by_tags: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_resources_by_tags: {str(e)}")
            raise
    
    def _extract_resource_type(self, resource_arn: str) -> str:
        """Extract resource type from ARN"""
        try:
            # ARN format: arn:aws:service:region:account:resource-type/resource-id
            parts = resource_arn.split(':')
            if len(parts) >= 6:
                service = parts[2]
                resource_part = parts[5]
                
                if '/' in resource_part:
                    resource_type = resource_part.split('/')[0]
                else:
                    resource_type = resource_part
                
                return f"{service}:{resource_type}"
            
            return "unknown"
        except Exception:
            return "unknown"
    
    async def _analyze_tagging_compliance(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tagging compliance for resources"""
        try:
            # Define required tags (these should be configurable)
            required_tags = ['Environment', 'Owner', 'Project', 'CostCenter']
            
            compliance_analysis = {
                'required_tags': required_tags,
                'overall_compliance': {},
                'by_resource_type': {},
                'missing_tags_summary': {},
                'recommendations': []
            }
            
            total_resources = len(resources)
            fully_compliant = 0
            partially_compliant = 0
            non_compliant = 0
            
            for resource in resources:
                resource_arn = resource.get('ResourceARN', '')
                resource_type = self._extract_resource_type(resource_arn)
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                
                # Check compliance
                missing_tags = [tag for tag in required_tags if tag not in tags]
                compliance_status = 'fully_compliant' if not missing_tags else 'partially_compliant' if len(missing_tags) < len(required_tags) else 'non_compliant'
                
                # Update counters
                if compliance_status == 'fully_compliant':
                    fully_compliant += 1
                elif compliance_status == 'partially_compliant':
                    partially_compliant += 1
                else:
                    non_compliant += 1
                
                # Update by resource type
                if resource_type not in compliance_analysis['by_resource_type']:
                    compliance_analysis['by_resource_type'][resource_type] = {
                        'total': 0,
                        'fully_compliant': 0,
                        'partially_compliant': 0,
                        'non_compliant': 0,
                        'common_missing_tags': {}
                    }
                
                type_stats = compliance_analysis['by_resource_type'][resource_type]
                type_stats['total'] += 1
                type_stats[compliance_status] += 1
                
                # Track missing tags
                for missing_tag in missing_tags:
                    if missing_tag not in type_stats['common_missing_tags']:
                        type_stats['common_missing_tags'][missing_tag] = 0
                    type_stats['common_missing_tags'][missing_tag] += 1
                    
                    if missing_tag not in compliance_analysis['missing_tags_summary']:
                        compliance_analysis['missing_tags_summary'][missing_tag] = 0
                    compliance_analysis['missing_tags_summary'][missing_tag] += 1
            
            # Calculate overall compliance
            compliance_analysis['overall_compliance'] = {
                'total_resources': total_resources,
                'fully_compliant': fully_compliant,
                'partially_compliant': partially_compliant,
                'non_compliant': non_compliant,
                'compliance_percentage': (fully_compliant / total_resources * 100) if total_resources > 0 else 0
            }
            
            # Generate recommendations
            if non_compliant > 0:
                compliance_analysis['recommendations'].append(f"Implement tagging for {non_compliant} non-compliant resources")
            
            if partially_compliant > 0:
                compliance_analysis['recommendations'].append(f"Complete tagging for {partially_compliant} partially compliant resources")
            
            # Identify most common missing tags
            if compliance_analysis['missing_tags_summary']:
                most_missing = max(compliance_analysis['missing_tags_summary'].items(), key=lambda x: x[1])
                compliance_analysis['recommendations'].append(f"Priority: Add '{most_missing[0]}' tag to {most_missing[1]} resources")
            
            return compliance_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing tagging compliance: {str(e)}")
            return {'error': str(e)}
    
    async def get_cost_allocation_tags(self, 
                                     start_date: str,
                                     end_date: str,
                                     tag_key: str) -> Dict[str, Any]:
        """
        Get cost allocation data by tag values
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            tag_key: Tag key to group costs by
        
        Returns:
            Dict containing cost allocation by tag values
        """
        try:
            # Get cost data grouped by tag
            response = self.cost_explorer_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'TAG',
                        'Key': tag_key
                    }
                ]
            )
            
            cost_by_tag = {}
            total_cost = 0
            untagged_cost = 0
            
            for result in response.get('ResultsByTime', []):
                period = result['TimePeriod']
                
                for group in result.get('Groups', []):
                    tag_value = group['Keys'][0] if group['Keys'] else 'Untagged'
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if tag_value not in cost_by_tag:
                        cost_by_tag[tag_value] = {
                            'total_cost': 0,
                            'periods': []
                        }
                    
                    cost_by_tag[tag_value]['total_cost'] += cost
                    cost_by_tag[tag_value]['periods'].append({
                        'period': period,
                        'cost': cost
                    })
                    
                    total_cost += cost
                    
                    if tag_value == 'Untagged' or tag_value == '':
                        untagged_cost += cost
            
            # Calculate percentages
            for tag_value in cost_by_tag:
                cost_by_tag[tag_value]['percentage'] = (cost_by_tag[tag_value]['total_cost'] / total_cost * 100) if total_cost > 0 else 0
            
            return {
                'tag_key': tag_key,
                'time_period': {
                    'start': start_date,
                    'end': end_date
                },
                'cost_by_tag': cost_by_tag,
                'summary': {
                    'total_cost': total_cost,
                    'untagged_cost': untagged_cost,
                    'untagged_percentage': (untagged_cost / total_cost * 100) if total_cost > 0 else 0,
                    'tagged_values_count': len([k for k in cost_by_tag.keys() if k not in ['Untagged', '']])
                }
            }
            
        except ClientError as e:
            logger.error(f"AWS API error in get_cost_allocation_tags: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_cost_allocation_tags: {str(e)}")
            raise
    
    async def get_tag_recommendations(self, 
                                    resource_type: str = None,
                                    environment: str = None) -> Dict[str, Any]:
        """
        Get tagging recommendations based on current state
        
        Args:
            resource_type: Optional resource type filter
            environment: Optional environment filter
        
        Returns:
            Dict containing tagging recommendations
        """
        try:
            # Get current resources and their tagging state
            filters = []
            if environment:
                filters.append({
                    'Key': 'Environment',
                    'Values': [environment]
                })
            
            resource_filters = []
            if resource_type:
                resource_filters.append(resource_type)
            
            resources_data = await self.get_resources_by_tags(
                tag_filters=filters,
                resource_type_filters=resource_filters,
                include_compliance_details=True
            )
            
            recommendations = {
                'immediate_actions': [],
                'strategic_improvements': [],
                'cost_optimization': [],
                'governance': []
            }
            
            compliance = resources_data.get('compliance_analysis', {})
            overall_compliance = compliance.get('overall_compliance', {})
            
            # Immediate actions
            non_compliant = overall_compliance.get('non_compliant', 0)
            if non_compliant > 0:
                recommendations['immediate_actions'].append({
                    'priority': 'high',
                    'action': f'Tag {non_compliant} non-compliant resources',
                    'impact': 'Enables cost allocation and governance',
                    'effort': 'medium'
                })
            
            # Strategic improvements
            compliance_percentage = overall_compliance.get('compliance_percentage', 0)
            if compliance_percentage < 90:
                recommendations['strategic_improvements'].append({
                    'priority': 'medium',
                    'action': 'Implement automated tagging policies',
                    'impact': 'Ensures consistent tagging for new resources',
                    'effort': 'high'
                })
            
            # Cost optimization
            missing_tags = compliance.get('missing_tags_summary', {})
            if 'CostCenter' in missing_tags:
                recommendations['cost_optimization'].append({
                    'priority': 'high',
                    'action': f'Add CostCenter tags to {missing_tags["CostCenter"]} resources',
                    'impact': 'Enables accurate cost allocation and chargeback',
                    'effort': 'low'
                })
            
            # Governance recommendations
            by_resource_type = compliance.get('by_resource_type', {})
            for resource_type, stats in by_resource_type.items():
                compliance_rate = (stats['fully_compliant'] / stats['total'] * 100) if stats['total'] > 0 else 0
                if compliance_rate < 80:
                    recommendations['governance'].append({
                        'priority': 'medium',
                        'action': f'Improve tagging compliance for {resource_type} resources',
                        'current_compliance': f"{compliance_rate:.1f}%",
                        'impact': 'Better resource management and cost visibility',
                        'effort': 'medium'
                    })
            
            return {
                'recommendations': recommendations,
                'current_state': {
                    'total_resources': overall_compliance.get('total_resources', 0),
                    'compliance_percentage': compliance_percentage,
                    'most_common_missing_tags': list(missing_tags.keys())[:3] if missing_tags else []
                },
                'filters_applied': {
                    'resource_type': resource_type,
                    'environment': environment
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_tag_recommendations: {str(e)}")
            raise
    
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
            
            if method == 'get_resources_by_tags':
                return await self.get_resources_by_tags(**params)
            elif method == 'get_cost_allocation_tags':
                return await self.get_cost_allocation_tags(**params)
            elif method == 'get_tag_recommendations':
                return await self.get_tag_recommendations(**params)
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
    server = TaggingMCPServer()
    
    try:
        # Test getting resources by tags
        resources_data = await server.get_resources_by_tags(
            resource_type_filters=['ec2:instance'],
            include_compliance_details=True
        )
        
        print("Tagging MCP Server Test Results:")
        print(f"Total resources found: {resources_data['total_count']}")
        
        if 'compliance_analysis' in resources_data:
            compliance = resources_data['compliance_analysis']['overall_compliance']
            print(f"Compliance rate: {compliance.get('compliance_percentage', 0):.1f}%")
        
        # Test tag recommendations
        recommendations = await server.get_tag_recommendations()
        print(f"Generated {len(recommendations['recommendations']['immediate_actions'])} immediate action recommendations")
        
        print("Tagging MCP Server test completed successfully")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
