#!/usr/bin/env python3
"""
Cost Explorer MCP Server

This MCP server provides access to AWS Cost Explorer data through the Model Context Protocol.
It exposes cost analysis capabilities to AI agents and applications.
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

class CostExplorerMCPServer:
    """MCP Server for AWS Cost Explorer integration"""
    
    def __init__(self):
        """Initialize the Cost Explorer MCP Server"""
        try:
            self.cost_explorer_client = boto3.client('ce')
            self.organizations_client = boto3.client('organizations')
            logger.info("Cost Explorer MCP Server initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing Cost Explorer client: {str(e)}")
            raise
    
    async def get_cost_and_usage(self, 
                                start_date: str, 
                                end_date: str, 
                                granularity: str = 'MONTHLY',
                                metrics: List[str] = None,
                                group_by: List[Dict[str, str]] = None,
                                filter_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get cost and usage data from AWS Cost Explorer
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY, MONTHLY, or HOURLY
            metrics: List of metrics to retrieve (BlendedCost, UnblendedCost, etc.)
            group_by: List of grouping dimensions
            filter_config: Filter configuration for the query
        
        Returns:
            Dict containing cost and usage data
        """
        try:
            if metrics is None:
                metrics = ['BlendedCost']
            
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': granularity,
                'Metrics': metrics
            }
            
            if group_by:
                params['GroupBy'] = group_by
            
            if filter_config:
                params['Filter'] = filter_config
            
            logger.info(f"Querying Cost Explorer with params: {params}")
            response = self.cost_explorer_client.get_cost_and_usage(**params)
            
            # Process and structure the response
            processed_data = {
                'time_period': {
                    'start': start_date,
                    'end': end_date
                },
                'granularity': granularity,
                'results': [],
                'total_cost': 0,
                'currency': 'USD'
            }
            
            for result in response.get('ResultsByTime', []):
                period_data = {
                    'time_period': result['TimePeriod'],
                    'estimated': result.get('Estimated', False),
                    'groups': []
                }
                
                # Process groups (services, accounts, etc.)
                for group in result.get('Groups', []):
                    group_data = {
                        'keys': group['Keys'],
                        'metrics': {}
                    }
                    
                    for metric_name, metric_data in group['Metrics'].items():
                        amount = float(metric_data.get('Amount', 0))
                        group_data['metrics'][metric_name] = {
                            'amount': amount,
                            'unit': metric_data.get('Unit', 'USD')
                        }
                        
                        if metric_name == 'BlendedCost':
                            processed_data['total_cost'] += amount
                    
                    period_data['groups'].append(group_data)
                
                # Process total metrics if no grouping
                if 'Total' in result:
                    period_data['total'] = {}
                    for metric_name, metric_data in result['Total'].items():
                        amount = float(metric_data.get('Amount', 0))
                        period_data['total'][metric_name] = {
                            'amount': amount,
                            'unit': metric_data.get('Unit', 'USD')
                        }
                        
                        if metric_name == 'BlendedCost':
                            processed_data['total_cost'] += amount
                
                processed_data['results'].append(period_data)
            
            return processed_data
            
        except ClientError as e:
            logger.error(f"AWS API error in get_cost_and_usage: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_cost_and_usage: {str(e)}")
            raise
    
    async def get_dimension_values(self, 
                                  dimension: str, 
                                  start_date: str, 
                                  end_date: str,
                                  search_string: str = None) -> Dict[str, Any]:
        """
        Get dimension values for filtering and grouping
        
        Args:
            dimension: Dimension name (SERVICE, LINKED_ACCOUNT, etc.)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            search_string: Optional search string to filter results
        
        Returns:
            Dict containing dimension values
        """
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Dimension': dimension
            }
            
            if search_string:
                params['SearchString'] = search_string
            
            response = self.cost_explorer_client.get_dimension_values(**params)
            
            return {
                'dimension': dimension,
                'time_period': {
                    'start': start_date,
                    'end': end_date
                },
                'values': [
                    {
                        'value': item['Value'],
                        'attributes': item.get('Attributes', {})
                    }
                    for item in response.get('DimensionValues', [])
                ],
                'total_size': response.get('TotalSize', 0),
                'return_size': response.get('ReturnSize', 0)
            }
            
        except ClientError as e:
            logger.error(f"AWS API error in get_dimension_values: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_dimension_values: {str(e)}")
            raise
    
    async def get_rightsizing_recommendations(self, 
                                            service: str = 'EC2-Instance',
                                            page_size: int = 100) -> Dict[str, Any]:
        """
        Get rightsizing recommendations from AWS Cost Explorer
        
        Args:
            service: Service to get recommendations for
            page_size: Number of recommendations per page
        
        Returns:
            Dict containing rightsizing recommendations
        """
        try:
            params = {
                'Service': service,
                'PageSize': page_size
            }
            
            response = self.cost_explorer_client.get_rightsizing_recommendation(**params)
            
            recommendations = []
            for rec in response.get('RightsizingRecommendations', []):
                recommendation_data = {
                    'account_id': rec.get('AccountId'),
                    'current_instance': rec.get('CurrentInstance', {}),
                    'rightsizing_type': rec.get('RightsizingType'),
                    'modify_recommendation': rec.get('ModifyRecommendationDetail', {}),
                    'terminate_recommendation': rec.get('TerminateRecommendationDetail', {}),
                    'finding_reason_codes': rec.get('FindingReasonCodes', [])
                }
                recommendations.append(recommendation_data)
            
            return {
                'service': service,
                'recommendations': recommendations,
                'metadata': response.get('Metadata', {}),
                'next_page_token': response.get('NextPageToken'),
                'configuration': response.get('Configuration', {})
            }
            
        except ClientError as e:
            logger.error(f"AWS API error in get_rightsizing_recommendations: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_rightsizing_recommendations: {str(e)}")
            raise
    
    async def get_savings_plans_utilization(self, 
                                          start_date: str, 
                                          end_date: str,
                                          granularity: str = 'MONTHLY') -> Dict[str, Any]:
        """
        Get Savings Plans utilization data
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY or MONTHLY
        
        Returns:
            Dict containing Savings Plans utilization data
        """
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': granularity
            }
            
            response = self.cost_explorer_client.get_savings_plans_utilization(**params)
            
            utilization_data = []
            for result in response.get('SavingsPlansUtilizationsByTime', []):
                period_data = {
                    'time_period': result['TimePeriod'],
                    'total': result.get('Total', {}),
                    'savings_plans_details': result.get('SavingsPlansDetails', [])
                }
                utilization_data.append(period_data)
            
            return {
                'time_period': {
                    'start': start_date,
                    'end': end_date
                },
                'granularity': granularity,
                'utilization_data': utilization_data,
                'total': response.get('Total', {})
            }
            
        except ClientError as e:
            logger.error(f"AWS API error in get_savings_plans_utilization: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_savings_plans_utilization: {str(e)}")
            raise
    
    async def get_cost_categories(self) -> Dict[str, Any]:
        """
        Get available cost categories
        
        Returns:
            Dict containing cost categories information
        """
        try:
            response = self.cost_explorer_client.list_cost_category_definitions()
            
            categories = []
            for category in response.get('CostCategoryReferences', []):
                categories.append({
                    'cost_category_arn': category.get('CostCategoryArn'),
                    'name': category.get('Name'),
                    'effective_start': category.get('EffectiveStart'),
                    'effective_end': category.get('EffectiveEnd'),
                    'number_of_rules': category.get('NumberOfRules')
                })
            
            return {
                'cost_categories': categories,
                'next_token': response.get('NextToken')
            }
            
        except ClientError as e:
            logger.error(f"AWS API error in get_cost_categories: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in get_cost_categories: {str(e)}")
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
            
            if method == 'get_cost_and_usage':
                return await self.get_cost_and_usage(**params)
            elif method == 'get_dimension_values':
                return await self.get_dimension_values(**params)
            elif method == 'get_rightsizing_recommendations':
                return await self.get_rightsizing_recommendations(**params)
            elif method == 'get_savings_plans_utilization':
                return await self.get_savings_plans_utilization(**params)
            elif method == 'get_cost_categories':
                return await self.get_cost_categories()
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            logger.error(f"Error processing MCP request: {str(e)}")
            return {
                'error': str(e),
                'method': request.get('method'),
                'params': request.get('params')
            }

# MCP Server Protocol Implementation
class MCPProtocolHandler:
    """Handles MCP protocol communication"""
    
    def __init__(self):
        self.cost_explorer_server = CostExplorerMCPServer()
    
    async def handle_request(self, request_data: str) -> str:
        """Handle incoming MCP request"""
        try:
            request = json.loads(request_data)
            response = await self.cost_explorer_server.process_mcp_request(request)
            
            return json.dumps({
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': response
            })
            
        except json.JSONDecodeError as e:
            return json.dumps({
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': -32700,
                    'message': 'Parse error',
                    'data': str(e)
                }
            })
        except Exception as e:
            return json.dumps({
                'jsonrpc': '2.0',
                'id': request.get('id') if 'request' in locals() else None,
                'error': {
                    'code': -32603,
                    'message': 'Internal error',
                    'data': str(e)
                }
            })

# Example usage and testing
async def main():
    """Main function for testing the MCP server"""
    server = CostExplorerMCPServer()
    
    # Test cost and usage query
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    try:
        cost_data = await server.get_cost_and_usage(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            granularity='DAILY',
            group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        print("Cost Explorer MCP Server Test Results:")
        print(f"Total cost: ${cost_data['total_cost']:.2f}")
        print(f"Number of results: {len(cost_data['results'])}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
