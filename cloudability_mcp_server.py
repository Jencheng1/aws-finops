#!/usr/bin/env python3
"""
IBM Cloudability MCP Server Implementation

This server provides MCP tools for accessing IBM Cloudability data and integrating
with AWS Bedrock agents for cost optimization.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (not stdout, which would break STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("cloudability-mcp")

# Initialize FastMCP server
mcp = FastMCP("cloudability")

# Constants
CLOUDABILITY_API_BASE = os.environ.get("CLOUDABILITY_API_BASE", "https://api.cloudability.com/v3")
CLOUDABILITY_API_KEY = os.environ.get("CLOUDABILITY_API_KEY", "")
CLOUDABILITY_REGION = os.environ.get("CLOUDABILITY_REGION", "us")  # us, eu, au, me

# Determine the correct API endpoint based on region
if CLOUDABILITY_REGION == "eu":
    CLOUDABILITY_API_BASE = "https://api-eu.cloudability.com/v3"
elif CLOUDABILITY_REGION == "au":
    CLOUDABILITY_API_BASE = "https://api-au.cloudability.com/v3"
elif CLOUDABILITY_REGION == "me":
    CLOUDABILITY_API_BASE = "https://api-me.cloudability.com/v3"
else:
    CLOUDABILITY_API_BASE = "https://api.cloudability.com/v3"

# Helper functions
async def make_cloudability_request(
    endpoint: str, 
    method: str = "GET", 
    params: Dict = None, 
    data: Dict = None
) -> Dict:
    """Make an authenticated request to the Cloudability API.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body for POST requests
        
    Returns:
        API response as a dictionary
    """
    url = f"{CLOUDABILITY_API_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {CLOUDABILITY_API_KEY}"
    }
    
    logger.info(f"Making {method} request to {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method == "POST":
                response = await client.post(url, headers=headers, params=params, json=data, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        return {"error": f"HTTP error: {e.response.status_code}", "message": e.response.text}
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        return {"error": "Request error", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": "Unexpected error", "message": str(e)}

def format_cost_data(data: Dict) -> str:
    """Format cost data into a readable string.
    
    Args:
        data: Cost data from Cloudability API
        
    Returns:
        Formatted cost data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No cost data available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No cost data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost Data Summary:")
    
    # Handle different result formats
    if isinstance(result, list):
        for item in result:
            if "date" in item and "cost" in item:
                date = item["date"]
                cost = item["cost"]
                formatted_output.append(f"  {date}: ${cost:.2f}")
            else:
                # Handle other list item formats
                formatted_output.append(f"  {json.dumps(item)}")
    elif isinstance(result, dict):
        # Extract total cost if available
        if "totalCost" in result:
            formatted_output.append(f"  Total Cost: ${result['totalCost']:.2f}")
        
        # Extract service breakdown if available
        if "services" in result and isinstance(result["services"], list):
            formatted_output.append("\nCost by Service:")
            for service in result["services"]:
                name = service.get("name", "Unknown")
                cost = service.get("cost", 0)
                formatted_output.append(f"  {name}: ${cost:.2f}")
    
    return "\n".join(formatted_output)

def format_usage_data(data: Dict) -> str:
    """Format usage data into a readable string.
    
    Args:
        data: Usage data from Cloudability API
        
    Returns:
        Formatted usage data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No usage data available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No usage data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Usage Data Summary:")
    
    # Handle different result formats based on the actual API response structure
    if isinstance(result, list):
        for item in result:
            if "service" in item and "usage" in item:
                service = item["service"]
                usage = item["usage"]
                unit = item.get("unit", "units")
                formatted_output.append(f"  {service}: {usage} {unit}")
            else:
                # Handle other list item formats
                formatted_output.append(f"  {json.dumps(item)}")
    elif isinstance(result, dict):
        # Extract service usage if available
        if "services" in result and isinstance(result["services"], list):
            for service in result["services"]:
                name = service.get("name", "Unknown")
                usage = service.get("usage", 0)
                unit = service.get("unit", "units")
                formatted_output.append(f"  {name}: {usage} {unit}")
    
    return "\n".join(formatted_output)

def format_tagging_compliance(data: Dict) -> str:
    """Format tagging compliance data into a readable string.
    
    Args:
        data: Tagging compliance data from Cloudability API
        
    Returns:
        Formatted tagging compliance data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No tagging compliance data available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No tagging compliance data available."
    
    formatted_output = []
    formatted_output.append("Tagging Compliance Summary:")
    
    # Extract overall compliance score if available
    if "complianceScore" in result:
        score = result["complianceScore"]
        formatted_output.append(f"  Overall Compliance Score: {score:.2f}%")
    
    # Extract tag compliance if available
    if "tagCompliance" in result and isinstance(result["tagCompliance"], list):
        formatted_output.append("\nCompliance by Tag:")
        for tag in result["tagCompliance"]:
            name = tag.get("name", "Unknown")
            score = tag.get("complianceScore", 0)
            formatted_output.append(f"  {name}: {score:.2f}%")
    
    # Extract untagged resources if available
    if "untaggedResources" in result and isinstance(result["untaggedResources"], list):
        formatted_output.append("\nUntagged Resources:")
        for resource in result["untaggedResources"][:10]:  # Limit to 10 resources
            id = resource.get("id", "Unknown")
            type = resource.get("type", "Unknown")
            formatted_output.append(f"  {type}: {id}")
        
        total = len(result["untaggedResources"])
        if total > 10:
            formatted_output.append(f"  ... and {total - 10} more untagged resources")
    
    return "\n".join(formatted_output)

def format_anomalies(data: Dict) -> str:
    """Format anomaly data into a readable string.
    
    Args:
        data: Anomaly data from Cloudability API
        
    Returns:
        Formatted anomaly data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No anomaly data available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No anomalies detected for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost Anomalies:")
    
    # Handle different result formats
    if isinstance(result, list):
        for anomaly in result:
            service = anomaly.get("service", "Unknown")
            expected = anomaly.get("expectedCost", 0)
            actual = anomaly.get("actualCost", 0)
            diff = actual - expected
            percent = (diff / expected) * 100 if expected > 0 else 0
            
            formatted_output.append(f"  Service: {service}")
            formatted_output.append(f"    Expected Cost: ${expected:.2f}")
            formatted_output.append(f"    Actual Cost: ${actual:.2f}")
            formatted_output.append(f"    Difference: ${diff:.2f} ({percent:.2f}%)")
            
            if "reason" in anomaly:
                formatted_output.append(f"    Reason: {anomaly['reason']}")
            
            formatted_output.append("")
    
    return "\n".join(formatted_output)

# MCP Tools
@mcp.tool()
async def get_cost_data(start_date: str, end_date: str, granularity: str = "daily") -> str:
    """Get cost data from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Data granularity (daily, monthly)
    
    Returns:
        Formatted cost data as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Validate granularity
    if granularity not in ["daily", "monthly"]:
        return "Error: Invalid granularity. Please use 'daily' or 'monthly'."
    
    # Make API request
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": granularity
    }
    
    response = await make_cloudability_request("costs", params=params)
    return format_cost_data(response)

@mcp.tool()
async def get_usage_data(start_date: str, end_date: str, service: str = None) -> str:
    """Get usage data from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        service: Optional AWS service filter
    
    Returns:
        Formatted usage data as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Make API request
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    
    if service:
        params["service"] = service
    
    response = await make_cloudability_request("usage", params=params)
    return format_usage_data(response)

@mcp.tool()
async def get_tagging_compliance() -> str:
    """Get tagging compliance information from IBM Cloudability.
    
    Returns:
        Formatted tagging compliance data as a string
    """
    response = await make_cloudability_request("tagging/compliance")
    return format_tagging_compliance(response)

@mcp.tool()
async def get_anomalies(start_date: str = None, end_date: str = None) -> str:
    """Get detected cost anomalies from IBM Cloudability.
    
    Args:
        start_date: Optional start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: Optional end date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Formatted anomaly data as a string
    """
    # Set default dates if not provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Make API request
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    
    response = await make_cloudability_request("anomalies", params=params)
    return format_anomalies(response)

@mcp.tool()
async def get_cost_by_service(start_date: str, end_date: str) -> str:
    """Get cost breakdown by service from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted cost by service data as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Make API request
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "groupBy": "service"
    }
    
    response = await make_cloudability_request("costs/breakdown", params=params)
    
    if "error" in response:
        return f"Error: {response['error']} - {response.get('message', '')}"
    
    if "result" not in response or not response["result"]:
        return "No cost data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost by Service:")
    
    result = response["result"]
    
    if isinstance(result, list):
        for item in result:
            service = item.get("service", "Unknown")
            cost = item.get("cost", 0)
            formatted_output.append(f"  {service}: ${cost:.2f}")
    elif isinstance(result, dict) and "services" in result:
        for service in result["services"]:
            name = service.get("name", "Unknown")
            cost = service.get("cost", 0)
            formatted_output.append(f"  {name}: ${cost:.2f}")
    
    return "\n".join(formatted_output)

@mcp.tool()
async def get_cost_by_account(start_date: str, end_date: str) -> str:
    """Get cost breakdown by account from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted cost by account data as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Make API request
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "groupBy": "account"
    }
    
    response = await make_cloudability_request("costs/breakdown", params=params)
    
    if "error" in response:
        return f"Error: {response['error']} - {response.get('message', '')}"
    
    if "result" not in response or not response["result"]:
        return "No cost data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost by Account:")
    
    result = response["result"]
    
    if isinstance(result, list):
        for item in result:
            account = item.get("account", "Unknown")
            cost = item.get("cost", 0)
            formatted_output.append(f"  {account}: ${cost:.2f}")
    elif isinstance(result, dict) and "accounts" in result:
        for account in result["accounts"]:
            name = account.get("name", "Unknown")
            cost = account.get("cost", 0)
            formatted_output.append(f"  {name}: ${cost:.2f}")
    
    return "\n".join(formatted_output)

@mcp.tool()
async def get_cost_by_tag(start_date: str, end_date: str, tag_key: str) -> str:
    """Get cost breakdown by a specific tag from IBM Cloudability.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        tag_key: The tag key to group by (e.g., "Environment", "Project")
    
    Returns:
        Formatted cost by tag data as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Make API request
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "groupBy": f"tag:{tag_key}"
    }
    
    response = await make_cloudability_request("costs/breakdown", params=params)
    
    if "error" in response:
        return f"Error: {response['error']} - {response.get('message', '')}"
    
    if "result" not in response or not response["result"]:
        return f"No cost data available for tag '{tag_key}' in the specified period."
    
    formatted_output = []
    formatted_output.append(f"Cost by Tag '{tag_key}':")
    
    result = response["result"]
    
    if isinstance(result, list):
        for item in result:
            tag_value = item.get("tagValue", "Untagged")
            cost = item.get("cost", 0)
            formatted_output.append(f"  {tag_value}: ${cost:.2f}")
    elif isinstance(result, dict) and "tags" in result:
        for tag in result["tags"]:
            value = tag.get("value", "Untagged")
            cost = tag.get("cost", 0)
            formatted_output.append(f"  {value}: ${cost:.2f}")
    
    return "\n".join(formatted_output)

@mcp.tool()
async def get_cost_forecast(months_ahead: int = 3) -> str:
    """Get cost forecast from IBM Cloudability.
    
    Args:
        months_ahead: Number of months to forecast (1-12)
    
    Returns:
        Formatted cost forecast data as a string
    """
    # Validate months_ahead
    if not 1 <= months_ahead <= 12:
        return "Error: months_ahead must be between 1 and 12."
    
    # Make API request
    params = {
        "months": months_ahead
    }
    
    response = await make_cloudability_request("costs/forecast", params=params)
    
    if "error" in response:
        return f"Error: {response['error']} - {response.get('message', '')}"
    
    if "result" not in response or not response["result"]:
        return "No forecast data available."
    
    formatted_output = []
    formatted_output.append("Cost Forecast:")
    
    result = response["result"]
    
    if isinstance(result, list):
        for item in result:
            date = item.get("date", "Unknown")
            forecast = item.get("forecast", 0)
            lower_bound = item.get("lowerBound", 0)
            upper_bound = item.get("upperBound", 0)
            
            formatted_output.append(f"  {date}:")
            formatted_output.append(f"    Forecast: ${forecast:.2f}")
            formatted_output.append(f"    Range: ${lower_bound:.2f} - ${upper_bound:.2f}")
    elif isinstance(result, dict) and "forecasts" in result:
        for forecast in result["forecasts"]:
            date = forecast.get("date", "Unknown")
            amount = forecast.get("amount", 0)
            lower_bound = forecast.get("lowerBound", 0)
            upper_bound = forecast.get("upperBound", 0)
            
            formatted_output.append(f"  {date}:")
            formatted_output.append(f"    Forecast: ${amount:.2f}")
            formatted_output.append(f"    Range: ${lower_bound:.2f} - ${upper_bound:.2f}")
    
    return "\n".join(formatted_output)

@mcp.tool()
async def get_optimization_recommendations() -> str:
    """Get cost optimization recommendations from IBM Cloudability.
    
    Returns:
        Formatted optimization recommendations as a string
    """
    response = await make_cloudability_request("recommendations/optimization")
    
    if "error" in response:
        return f"Error: {response['error']} - {response.get('message', '')}"
    
    if "result" not in response or not response["result"]:
        return "No optimization recommendations available."
    
    formatted_output = []
    formatted_output.append("Cost Optimization Recommendations:")
    
    result = response["result"]
    
    if isinstance(result, list):
        for i, rec in enumerate(result, 1):
            title = rec.get("title", "Unknown")
            savings = rec.get("savings", 0)
            impact = rec.get("impact", "Medium")
            
            formatted_output.append(f"\n{i}. {title}")
            formatted_output.append(f"   Potential Savings: ${savings:.2f}")
            formatted_output.append(f"   Impact: {impact}")
            
            if "description" in rec:
                formatted_output.append(f"   Description: {rec['description']}")
            
            if "steps" in rec and isinstance(rec["steps"], list):
                formatted_output.append("   Implementation Steps:")
                for step in rec["steps"]:
                    formatted_output.append(f"   - {step}")
    
    return "\n".join(formatted_output)

if __name__ == "__main__":
    # Check if API key is set
    if not CLOUDABILITY_API_KEY:
        logger.error("CLOUDABILITY_API_KEY environment variable is not set")
        print("Error: CLOUDABILITY_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    
    # Initialize and run the server
    logger.info("Starting Cloudability MCP server")
    mcp.run(transport='stdio')
