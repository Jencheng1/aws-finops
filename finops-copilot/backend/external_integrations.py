#!/usr/bin/env python3
"""
External FinOps Tools Integration Module

This module provides integration with external FinOps and cloud cost management tools
including CloudHealth, Cloudability, Spot.io, and other third-party APIs.
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APICredentials:
    """Data class for storing API credentials"""
    api_key: str
    api_secret: Optional[str] = None
    base_url: str = ""
    auth_type: str = "api_key"  # api_key, bearer_token, basic_auth

class ExternalFinOpsIntegrator:
    """Main class for integrating with external FinOps tools"""
    
    def __init__(self):
        """Initialize the external integrations"""
        self.session = None
        self.credentials = {}
        self._load_credentials()
    
    def _load_credentials(self):
        """Load API credentials from environment variables"""
        self.credentials = {
            'cloudhealth': APICredentials(
                api_key=os.getenv('CLOUDHEALTH_API_KEY', ''),
                base_url='https://chapi.cloudhealthtech.com/v1',
                auth_type='api_key'
            ),
            'cloudability': APICredentials(
                api_key=os.getenv('CLOUDABILITY_API_KEY', ''),
                base_url='https://api.cloudability.com/v3',
                auth_type='bearer_token'
            ),
            'spot': APICredentials(
                api_key=os.getenv('SPOT_API_TOKEN', ''),
                base_url='https://api.spotinst.io',
                auth_type='bearer_token'
            ),
            'apito': APICredentials(
                api_key=os.getenv('APITO_API_KEY', ''),
                api_secret=os.getenv('APITO_API_SECRET', ''),
                base_url=os.getenv('APITO_BASE_URL', 'https://api.apito.com'),
                auth_type='api_key'
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_auth_headers(self, service: str) -> Dict[str, str]:
        """Get authentication headers for a specific service"""
        creds = self.credentials.get(service)
        if not creds or not creds.api_key:
            return {}
        
        if creds.auth_type == 'api_key':
            return {'Authorization': f'Bearer {creds.api_key}'}
        elif creds.auth_type == 'bearer_token':
            return {'Authorization': f'Bearer {creds.api_key}'}
        elif creds.auth_type == 'basic_auth':
            import base64
            auth_string = base64.b64encode(f"{creds.api_key}:{creds.api_secret}".encode()).decode()
            return {'Authorization': f'Basic {auth_string}'}
        
        return {}
    
    async def _make_request(self, 
                           service: str, 
                           endpoint: str, 
                           method: str = 'GET',
                           params: Dict[str, Any] = None,
                           data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an authenticated request to an external service"""
        try:
            creds = self.credentials.get(service)
            if not creds:
                raise ValueError(f"No credentials configured for service: {service}")
            
            url = f"{creds.base_url}/{endpoint.lstrip('/')}"
            headers = self._get_auth_headers(service)
            headers['Content-Type'] = 'application/json'
            
            logger.info(f"Making {method} request to {service}: {endpoint}")
            
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data if data else None
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise Exception(f"Authentication failed for {service}")
                elif response.status == 403:
                    raise Exception(f"Access forbidden for {service}")
                elif response.status == 429:
                    raise Exception(f"Rate limit exceeded for {service}")
                else:
                    error_text = await response.text()
                    raise Exception(f"API error for {service}: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error making request to {service}: {str(e)}")
            return {'error': str(e), 'service': service}

class CloudHealthIntegration:
    """Integration with CloudHealth API"""
    
    def __init__(self, integrator: ExternalFinOpsIntegrator):
        self.integrator = integrator
        self.service = 'cloudhealth'
    
    async def get_cost_data(self, 
                           start_date: str, 
                           end_date: str,
                           interval: str = 'monthly') -> Dict[str, Any]:
        """Get cost data from CloudHealth"""
        try:
            params = {
                'interval': interval,
                'from': start_date,
                'to': end_date
            }
            
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='reports',
                params=params
            )
            
            if 'error' in response:
                return response
            
            # Process CloudHealth response
            processed_data = {
                'source': 'CloudHealth',
                'time_period': {'start': start_date, 'end': end_date},
                'interval': interval,
                'cost_data': response.get('data', []),
                'total_cost': sum(item.get('cost', 0) for item in response.get('data', [])),
                'currency': 'USD'
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting CloudHealth cost data: {str(e)}")
            return {'error': str(e), 'source': 'CloudHealth'}
    
    async def get_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations from CloudHealth"""
        try:
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='recommendations'
            )
            
            if 'error' in response:
                return response
            
            # Process recommendations
            recommendations = []
            for rec in response.get('recommendations', []):
                recommendations.append({
                    'title': rec.get('title', 'CloudHealth Recommendation'),
                    'description': rec.get('description', ''),
                    'potential_savings': rec.get('savings', 0),
                    'priority': rec.get('priority', 'medium'),
                    'category': rec.get('category', 'cost_optimization'),
                    'source': 'CloudHealth'
                })
            
            return {
                'source': 'CloudHealth',
                'recommendations': recommendations,
                'total_recommendations': len(recommendations),
                'total_potential_savings': sum(r['potential_savings'] for r in recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error getting CloudHealth recommendations: {str(e)}")
            return {'error': str(e), 'source': 'CloudHealth'}

class CloudabilityIntegration:
    """Integration with Cloudability API"""
    
    def __init__(self, integrator: ExternalFinOpsIntegrator):
        self.integrator = integrator
        self.service = 'cloudability'
    
    async def get_cost_reports(self, 
                              start_date: str, 
                              end_date: str,
                              dimensions: List[str] = None) -> Dict[str, Any]:
        """Get cost reports from Cloudability"""
        try:
            if dimensions is None:
                dimensions = ['service', 'account']
            
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'dimensions': ','.join(dimensions),
                'metrics': 'unblended_cost'
            }
            
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='reporting/cost',
                params=params
            )
            
            if 'error' in response:
                return response
            
            # Process Cloudability response
            processed_data = {
                'source': 'Cloudability',
                'time_period': {'start': start_date, 'end': end_date},
                'dimensions': dimensions,
                'cost_data': response.get('results', []),
                'metadata': response.get('metadata', {}),
                'total_cost': response.get('metadata', {}).get('total_cost', 0)
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting Cloudability cost reports: {str(e)}")
            return {'error': str(e), 'source': 'Cloudability'}
    
    async def get_rightsizing_recommendations(self) -> Dict[str, Any]:
        """Get rightsizing recommendations from Cloudability"""
        try:
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='rightsizing/recommendations'
            )
            
            if 'error' in response:
                return response
            
            # Process rightsizing recommendations
            recommendations = []
            for rec in response.get('recommendations', []):
                recommendations.append({
                    'resource_id': rec.get('resource_id', ''),
                    'resource_type': rec.get('resource_type', ''),
                    'current_type': rec.get('current_instance_type', ''),
                    'recommended_type': rec.get('recommended_instance_type', ''),
                    'potential_savings': rec.get('monthly_savings', 0),
                    'confidence': rec.get('confidence', 'medium'),
                    'source': 'Cloudability'
                })
            
            return {
                'source': 'Cloudability',
                'recommendations': recommendations,
                'total_recommendations': len(recommendations),
                'total_potential_savings': sum(r['potential_savings'] for r in recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error getting Cloudability rightsizing: {str(e)}")
            return {'error': str(e), 'source': 'Cloudability'}

class SpotIntegration:
    """Integration with Spot.io API"""
    
    def __init__(self, integrator: ExternalFinOpsIntegrator):
        self.integrator = integrator
        self.service = 'spot'
    
    async def get_elastigroup_costs(self, 
                                   start_date: str, 
                                   end_date: str) -> Dict[str, Any]:
        """Get Elastigroup cost data from Spot.io"""
        try:
            params = {
                'fromDate': start_date,
                'toDate': end_date,
                'granularity': 'day'
            }
            
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='aws/ec2/costs',
                params=params
            )
            
            if 'error' in response:
                return response
            
            # Process Spot.io response
            cost_items = response.get('response', {}).get('items', [])
            total_cost = sum(item.get('cost', 0) for item in cost_items)
            
            processed_data = {
                'source': 'Spot.io',
                'time_period': {'start': start_date, 'end': end_date},
                'cost_data': cost_items,
                'total_cost': total_cost,
                'savings_summary': response.get('response', {}).get('savings', {})
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting Spot.io cost data: {str(e)}")
            return {'error': str(e), 'source': 'Spot.io'}
    
    async def get_optimization_suggestions(self) -> Dict[str, Any]:
        """Get optimization suggestions from Spot.io"""
        try:
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='aws/ec2/suggestions'
            )
            
            if 'error' in response:
                return response
            
            # Process optimization suggestions
            suggestions = []
            for suggestion in response.get('response', {}).get('items', []):
                suggestions.append({
                    'resource_id': suggestion.get('resourceId', ''),
                    'suggestion_type': suggestion.get('type', ''),
                    'description': suggestion.get('description', ''),
                    'potential_savings': suggestion.get('potentialSavings', 0),
                    'confidence': suggestion.get('confidence', 'medium'),
                    'source': 'Spot.io'
                })
            
            return {
                'source': 'Spot.io',
                'suggestions': suggestions,
                'total_suggestions': len(suggestions),
                'total_potential_savings': sum(s['potential_savings'] for s in suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error getting Spot.io suggestions: {str(e)}")
            return {'error': str(e), 'source': 'Spot.io'}

class ApitoIntegration:
    """Integration with Apito API (custom/generic FinOps tool)"""
    
    def __init__(self, integrator: ExternalFinOpsIntegrator):
        self.integrator = integrator
        self.service = 'apito'
    
    async def get_cost_analysis(self, 
                               account_id: str,
                               start_date: str, 
                               end_date: str) -> Dict[str, Any]:
        """Get cost analysis from Apito"""
        try:
            data = {
                'account_id': account_id,
                'start_date': start_date,
                'end_date': end_date,
                'include_recommendations': True
            }
            
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='cost-analysis',
                method='POST',
                data=data
            )
            
            if 'error' in response:
                return response
            
            # Process Apito response
            processed_data = {
                'source': 'Apito',
                'account_id': account_id,
                'time_period': {'start': start_date, 'end': end_date},
                'cost_breakdown': response.get('cost_breakdown', {}),
                'trends': response.get('trends', []),
                'recommendations': response.get('recommendations', []),
                'total_cost': response.get('total_cost', 0)
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting Apito cost analysis: {str(e)}")
            return {'error': str(e), 'source': 'Apito'}
    
    async def submit_optimization_request(self, 
                                        optimization_type: str,
                                        resource_details: Dict[str, Any]) -> Dict[str, Any]:
        """Submit optimization request to Apito"""
        try:
            data = {
                'optimization_type': optimization_type,
                'resource_details': resource_details,
                'priority': 'high'
            }
            
            response = await self.integrator._make_request(
                service=self.service,
                endpoint='optimization-requests',
                method='POST',
                data=data
            )
            
            if 'error' in response:
                return response
            
            return {
                'source': 'Apito',
                'request_id': response.get('request_id', ''),
                'status': response.get('status', 'submitted'),
                'estimated_completion': response.get('estimated_completion', ''),
                'optimization_type': optimization_type
            }
            
        except Exception as e:
            logger.error(f"Error submitting Apito optimization request: {str(e)}")
            return {'error': str(e), 'source': 'Apito'}

class FinOpsAggregator:
    """Aggregates data from multiple FinOps tools"""
    
    def __init__(self):
        self.integrator = ExternalFinOpsIntegrator()
        self.cloudhealth = CloudHealthIntegration(self.integrator)
        self.cloudability = CloudabilityIntegration(self.integrator)
        self.spot = SpotIntegration(self.integrator)
        self.apito = ApitoIntegration(self.integrator)
    
    async def get_comprehensive_analysis(self, 
                                       start_date: str, 
                                       end_date: str,
                                       account_id: str = None) -> Dict[str, Any]:
        """Get comprehensive cost analysis from all available tools"""
        async with self.integrator:
            results = {
                'time_period': {'start': start_date, 'end': end_date},
                'sources': [],
                'cost_data': {},
                'recommendations': [],
                'total_cost': 0,
                'total_potential_savings': 0,
                'errors': []
            }
            
            # Collect data from all sources
            tasks = []
            
            # CloudHealth
            if self.integrator.credentials['cloudhealth'].api_key:
                tasks.append(('cloudhealth_cost', self.cloudhealth.get_cost_data(start_date, end_date)))
                tasks.append(('cloudhealth_recs', self.cloudhealth.get_recommendations()))
            
            # Cloudability
            if self.integrator.credentials['cloudability'].api_key:
                tasks.append(('cloudability_cost', self.cloudability.get_cost_reports(start_date, end_date)))
                tasks.append(('cloudability_recs', self.cloudability.get_rightsizing_recommendations()))
            
            # Spot.io
            if self.integrator.credentials['spot'].api_key:
                tasks.append(('spot_cost', self.spot.get_elastigroup_costs(start_date, end_date)))
                tasks.append(('spot_suggestions', self.spot.get_optimization_suggestions()))
            
            # Apito
            if self.integrator.credentials['apito'].api_key and account_id:
                tasks.append(('apito_analysis', self.apito.get_cost_analysis(account_id, start_date, end_date)))
            
            # Execute all tasks concurrently
            if tasks:
                task_results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
                
                for i, (task_name, result) in enumerate(zip([task[0] for task in tasks], task_results)):
                    if isinstance(result, Exception):
                        results['errors'].append({'task': task_name, 'error': str(result)})
                        continue
                    
                    if 'error' in result:
                        results['errors'].append({'task': task_name, 'error': result['error']})
                        continue
                    
                    # Process successful results
                    source = result.get('source', task_name)
                    if source not in results['sources']:
                        results['sources'].append(source)
                    
                    results['cost_data'][task_name] = result
                    
                    # Aggregate costs
                    if 'total_cost' in result:
                        results['total_cost'] += result['total_cost']
                    
                    # Aggregate recommendations
                    if 'recommendations' in result:
                        results['recommendations'].extend(result['recommendations'])
                    elif 'suggestions' in result:
                        results['recommendations'].extend(result['suggestions'])
                    
                    # Aggregate potential savings
                    if 'total_potential_savings' in result:
                        results['total_potential_savings'] += result['total_potential_savings']
            
            # Sort recommendations by potential savings
            results['recommendations'].sort(
                key=lambda x: x.get('potential_savings', 0), 
                reverse=True
            )
            
            return results

# Example usage and testing
async def main():
    """Main function for testing external integrations"""
    aggregator = FinOpsAggregator()
    
    # Test comprehensive analysis
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    try:
        analysis = await aggregator.get_comprehensive_analysis(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            account_id='123456789'
        )
        
        print("External FinOps Integration Test Results:")
        print(f"Sources integrated: {len(analysis['sources'])}")
        print(f"Total recommendations: {len(analysis['recommendations'])}")
        print(f"Total potential savings: ${analysis['total_potential_savings']:.2f}")
        
        if analysis['errors']:
            print(f"Errors encountered: {len(analysis['errors'])}")
            for error in analysis['errors']:
                print(f"  - {error['task']}: {error['error']}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
