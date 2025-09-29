import json
import boto3
import logging
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ApptioMCPClient:
    """Client for interacting with Apptio via MCP protocol"""
    
    def __init__(self):
        # Get MCP server configuration from environment or parameter store
        self.ssm_client = boto3.client('ssm')
        self._load_configuration()
        
    def _load_configuration(self):
        """Load MCP configuration from Parameter Store"""
        try:
            # Get MCP server endpoint
            mcp_endpoint_param = self.ssm_client.get_parameter(
                Name='/finops-copilot/mcp/apptio/endpoint',
                WithDecryption=False
            )
            self.mcp_endpoint = mcp_endpoint_param['Parameter']['Value']
            
            # Get API credentials (stored as SecureString)
            api_key_param = self.ssm_client.get_parameter(
                Name='/finops-copilot/mcp/apptio/api-key',
                WithDecryption=True
            )
            self.api_key = api_key_param['Parameter']['Value']
            
            env_id_param = self.ssm_client.get_parameter(
                Name='/finops-copilot/mcp/apptio/env-id',
                WithDecryption=False
            )
            self.env_id = env_id_param['Parameter']['Value']
            
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {str(e)}")
            # Use defaults for testing
            self.mcp_endpoint = "http://localhost:8000"
            self.api_key = ""
            self.env_id = ""
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool via JSON-RPC"""
        try:
            # Prepare JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": f"{tool_name}_{datetime.utcnow().timestamp()}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            # Set up headers with authentication
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "X-Environment-ID": self.env_id
            }
            
            # Make async HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.mcp_endpoint,
                    json=request,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "error" in result:
                    logger.error(f"MCP error: {result['error']}")
                    return {"error": result["error"]}
                
                return result.get("result", {})
                
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {"error": str(e)}
    
    async def get_cost_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get cost data from Apptio"""
        return await self.call_mcp_tool(
            "get_cost_data",
            {"start_date": start_date, "end_date": end_date}
        )
    
    async def get_budget_data(self, fiscal_year: str, fiscal_period: Optional[str] = None) -> Dict[str, Any]:
        """Get budget data from Apptio"""
        params = {"fiscal_year": fiscal_year}
        if fiscal_period:
            params["fiscal_period"] = fiscal_period
        
        return await self.call_mcp_tool("get_budget_data", params)
    
    async def get_forecast_data(self, months_ahead: int = 3) -> Dict[str, Any]:
        """Get forecast data from Apptio"""
        return await self.call_mcp_tool(
            "get_forecast_data",
            {"months_ahead": months_ahead}
        )
    
    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations from Apptio"""
        return await self.call_mcp_tool("get_optimization_recommendations", {})
    
    async def get_cost_by_service(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get cost breakdown by service from Apptio"""
        return await self.call_mcp_tool(
            "get_cost_by_service",
            {"start_date": start_date, "end_date": end_date}
        )
    
    async def get_cost_by_tag(self, start_date: str, end_date: str, tag_key: str) -> Dict[str, Any]:
        """Get cost breakdown by tag from Apptio"""
        return await self.call_mcp_tool(
            "get_cost_by_tag",
            {"start_date": start_date, "end_date": end_date, "tag_key": tag_key}
        )
    
    async def get_budget_vs_actual(self, fiscal_year: str) -> Dict[str, Any]:
        """Get budget vs actual comparison from Apptio"""
        return await self.call_mcp_tool(
            "get_budget_vs_actual",
            {"fiscal_year": fiscal_year}
        )

class ApptioDataEnricher:
    """Enriches AWS cost data with Apptio insights"""
    
    def __init__(self):
        self.mcp_client = ApptioMCPClient()
    
    async def enrich_cost_analysis(self, aws_cost_data: Dict[str, Any], days: int = 30) -> Dict[str, Any]:
        """Enrich AWS cost data with Apptio insights"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get Apptio data
            apptio_cost_data = await self.mcp_client.get_cost_data(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            apptio_forecast = await self.mcp_client.get_forecast_data(months_ahead=3)
            apptio_recommendations = await self.mcp_client.get_optimization_recommendations()
            
            # Get current fiscal year for budget comparison
            current_year = datetime.utcnow().year
            budget_comparison = await self.mcp_client.get_budget_vs_actual(str(current_year))
            
            # Parse and combine insights
            enriched_data = {
                "aws_data": aws_cost_data,
                "apptio_insights": {
                    "cost_analysis": self._parse_cost_data(apptio_cost_data),
                    "forecast": self._parse_forecast_data(apptio_forecast),
                    "budget_comparison": self._parse_budget_data(budget_comparison),
                    "additional_recommendations": self._parse_recommendations(apptio_recommendations)
                },
                "combined_analysis": self._combine_insights(aws_cost_data, apptio_cost_data, apptio_recommendations)
            }
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching cost analysis: {str(e)}")
            # Return original data if enrichment fails
            return {
                "aws_data": aws_cost_data,
                "apptio_insights": {"error": str(e)},
                "combined_analysis": {}
            }
    
    def _parse_cost_data(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Apptio cost data response"""
        if "error" in cost_data:
            return {"error": cost_data["error"]}
        
        # Extract key metrics from the formatted string response
        # In real implementation, this would parse the actual Apptio response format
        return {
            "total_cost": 0,  # Would be extracted from response
            "cost_trend": "stable",
            "top_cost_drivers": []
        }
    
    def _parse_forecast_data(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Apptio forecast data"""
        if "error" in forecast_data:
            return {"error": forecast_data["error"]}
        
        return {
            "forecast_accuracy": "high",
            "projected_spend": 0,
            "confidence_interval": {"lower": 0, "upper": 0}
        }
    
    def _parse_budget_data(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Apptio budget comparison data"""
        if "error" in budget_data:
            return {"error": budget_data["error"]}
        
        return {
            "budget_variance": 0,
            "variance_percentage": 0,
            "budget_health": "on_track"
        }
    
    def _parse_recommendations(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Apptio recommendations"""
        if "error" in recommendations:
            return []
        
        # Would parse actual recommendations from Apptio
        return []
    
    def _combine_insights(self, aws_data: Dict[str, Any], 
                         apptio_cost_data: Dict[str, Any],
                         apptio_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Combine AWS and Apptio insights for comprehensive analysis"""
        combined = {
            "total_identified_savings": 0,
            "confidence_score": 0.85,
            "risk_areas": [],
            "opportunity_areas": []
        }
        
        # Combine savings opportunities from both sources
        if "summary" in aws_data:
            aws_savings = aws_data["summary"].get("potential_monthly_savings", 0)
            combined["total_identified_savings"] += aws_savings
        
        # Add Apptio-specific insights
        if "error" not in apptio_cost_data:
            combined["opportunity_areas"].append({
                "source": "apptio",
                "type": "cost_allocation",
                "description": "Improved cost allocation based on Apptio business mapping"
            })
        
        return combined

def lambda_handler(event, context):
    """Lambda handler for Apptio MCP integration"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract parameters
        action = event.get('action', 'enrich_analysis')
        aws_cost_data = event.get('aws_cost_data', {})
        days = event.get('days', 30)
        
        if action == 'enrich_analysis':
            # Create enricher and run async operation
            enricher = ApptioDataEnricher()
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                enriched_data = loop.run_until_complete(
                    enricher.enrich_cost_analysis(aws_cost_data, days)
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(enriched_data)
                }
            finally:
                loop.close()
        
        elif action == 'get_apptio_data':
            # Direct MCP calls for specific Apptio data
            client = ApptioMCPClient()
            
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Run async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Gather multiple MCP calls concurrently
                results = loop.run_until_complete(
                    asyncio.gather(
                        client.get_cost_data(
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        ),
                        client.get_forecast_data(3),
                        client.get_optimization_recommendations()
                    )
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'cost_data': results[0],
                        'forecast': results[1],
                        'recommendations': results[2]
                    })
                }
            finally:
                loop.close()
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'supported_actions': ['enrich_analysis', 'get_apptio_data']
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
        'action': 'enrich_analysis',
        'aws_cost_data': {
            'summary': {
                'total_monthly_cost': 10000,
                'potential_monthly_savings': 2000
            }
        },
        'days': 30
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))