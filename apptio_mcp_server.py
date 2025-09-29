#!/usr/bin/env python3
"""
Apptio MCP Server Implementation

This server provides MCP tools for accessing Apptio data and integrating
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
logger = logging.getLogger("apptio-mcp")

# Initialize FastMCP server
mcp = FastMCP("apptio")

# Constants
APPTIO_API_BASE = os.environ.get("APPTIO_API_BASE", "https://api.apptio.com")
APPTIO_API_KEY = os.environ.get("APPTIO_API_KEY", "")
APPTIO_ENV_ID = os.environ.get("APPTIO_ENV_ID", "")

# Helper functions
async def make_apptio_request(
    endpoint: str, 
    method: str = "GET", 
    params: Dict = None, 
    data: Dict = None
) -> Dict:
    """Make an authenticated request to the Apptio API.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body for POST requests
        
    Returns:
        API response as a dictionary
    """
    url = f"{APPTIO_API_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apptio-opentoken": APPTIO_API_KEY,
        "apptio-environmentid": APPTIO_ENV_ID
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
        data: Cost data from Apptio API
        
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

def format_budget_data(data: Dict) -> str:
    """Format budget data into a readable string.
    
    Args:
        data: Budget data from Apptio API
        
    Returns:
        Formatted budget data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No budget data available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No budget data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Budget Data Summary:")
    
    # Handle different result formats
    if isinstance(result, list):
        for budget in result:
            name = budget.get("name", "Unknown")
            amount = budget.get("amount", 0)
            spent = budget.get("spent", 0)
            remaining = budget.get("remaining", 0)
            percent_used = (spent / amount) * 100 if amount > 0 else 0
            
            formatted_output.append(f"\nBudget: {name}")
            formatted_output.append(f"  Amount: ${amount:.2f}")
            formatted_output.append(f"  Spent: ${spent:.2f}")
            formatted_output.append(f"  Remaining: ${remaining:.2f}")
            formatted_output.append(f"  Percent Used: {percent_used:.2f}%")
    elif isinstance(result, dict):
        # Extract budget details
        name = result.get("name", "Unknown")
        amount = result.get("amount", 0)
        spent = result.get("spent", 0)
        remaining = result.get("remaining", 0)
        percent_used = (spent / amount) * 100 if amount > 0 else 0
        
        formatted_output.append(f"\nBudget: {name}")
        formatted_output.append(f"  Amount: ${amount:.2f}")
        formatted_output.append(f"  Spent: ${spent:.2f}")
        formatted_output.append(f"  Remaining: ${remaining:.2f}")
        formatted_output.append(f"  Percent Used: {percent_used:.2f}%")
    
    return "\n".join(formatted_output)

def format_forecast_data(data: Dict) -> str:
    """Format forecast data into a readable string.
    
    Args:
        data: Forecast data from Apptio API
        
    Returns:
        Formatted forecast data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No forecast data available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No forecast data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Forecast Data Summary:")
    
    # Handle different result formats
    if isinstance(result, list):
        for forecast in result:
            period = forecast.get("period", "Unknown")
            amount = forecast.get("amount", 0)
            lower_bound = forecast.get("lowerBound", 0)
            upper_bound = forecast.get("upperBound", 0)
            
            formatted_output.append(f"\nPeriod: {period}")
            formatted_output.append(f"  Forecast Amount: ${amount:.2f}")
            formatted_output.append(f"  Range: ${lower_bound:.2f} - ${upper_bound:.2f}")
    elif isinstance(result, dict):
        # Extract forecast details
        period = result.get("period", "Unknown")
        amount = result.get("amount", 0)
        lower_bound = result.get("lowerBound", 0)
        upper_bound = result.get("upperBound", 0)
        
        formatted_output.append(f"\nPeriod: {period}")
        formatted_output.append(f"  Forecast Amount: ${amount:.2f}")
        formatted_output.append(f"  Range: ${lower_bound:.2f} - ${upper_bound:.2f}")
    
    return "\n".join(formatted_output)

def format_optimization_recommendations(data: Dict) -> str:
    """Format optimization recommendations into a readable string.
    
    Args:
        data: Optimization recommendations from Apptio API
        
    Returns:
        Formatted optimization recommendations as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "result" not in data:
        return "No optimization recommendations available or invalid response format."
    
    result = data["result"]
    
    if not result:
        return "No optimization recommendations available."
    
    formatted_output = []
    formatted_output.append("Optimization Recommendations:")
    
    # Handle different result formats
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

# MCP Tools
@mcp.tool()
async def get_cost_data(start_date: str, end_date: str) -> str:
    """Get cost data from Apptio.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted cost data as a string
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
    
    response = await make_apptio_request("costs", params=params)
    return format_cost_data(response)

@mcp.tool()
async def get_budget_data(fiscal_year: str, fiscal_period: str = None) -> str:
    """Get budget data from Apptio.
    
    Args:
        fiscal_year: Fiscal year
        fiscal_period: Optional fiscal period
    
    Returns:
        Formatted budget data as a string
    """
    # Make API request
    params = {
        "fiscalYear": fiscal_year
    }
    
    if fiscal_period:
        params["fiscalPeriod"] = fiscal_period
    
    response = await make_apptio_request("budgets", params=params)
    return format_budget_data(response)

@mcp.tool()
async def get_forecast_data(months_ahead: int = 3) -> str:
    """Get forecast data from Apptio.
    
    Args:
        months_ahead: Number of months to forecast (1-12)
    
    Returns:
        Formatted forecast data as a string
    """
    # Validate months_ahead
    if not 1 <= months_ahead <= 12:
        return "Error: months_ahead must be between 1 and 12."
    
    # Make API request
    params = {
        "months": months_ahead
    }
    
    response = await make_apptio_request("forecasts", params=params)
    return format_forecast_data(response)

@mcp.tool()
async def get_optimization_recommendations() -> str:
    """Get cost optimization recommendations from Apptio.
    
    Returns:
        Formatted optimization recommendations as a string
    """
    response = await make_apptio_request("recommendations/optimization")
    return format_optimization_recommendations(response)

@mcp.tool()
async def get_cost_by_service(start_date: str, end_date: str) -> str:
    """Get cost breakdown by service from Apptio.
    
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
    
    response = await make_apptio_request("costs/breakdown", params=params)
    
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
    """Get cost breakdown by account from Apptio.
    
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
    
    response = await make_apptio_request("costs/breakdown", params=params)
    
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
    """Get cost breakdown by a specific tag from Apptio.
    
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
    
    response = await make_apptio_request("costs/breakdown", params=params)
    
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
async def get_budget_vs_actual(fiscal_year: str) -> str:
    """Get budget vs. actual comparison from Apptio.
    
    Args:
        fiscal_year: Fiscal year
    
    Returns:
        Formatted budget vs. actual data as a string
    """
    # Make API request
    params = {
        "fiscalYear": fiscal_year
    }
    
    response = await make_apptio_request("budgets/comparison", params=params)
    
    if "error" in response:
        return f"Error: {response['error']} - {response.get('message', '')}"
    
    if "result" not in response or not response["result"]:
        return "No budget comparison data available for the specified fiscal year."
    
    formatted_output = []
    formatted_output.append(f"Budget vs. Actual for Fiscal Year {fiscal_year}:")
    
    result = response["result"]
    
    if isinstance(result, list):
        for item in result:
            period = item.get("period", "Unknown")
            budget = item.get("budget", 0)
            actual = item.get("actual", 0)
            variance = actual - budget
            variance_percent = (variance / budget) * 100 if budget > 0 else 0
            
            formatted_output.append(f"\nPeriod: {period}")
            formatted_output.append(f"  Budget: ${budget:.2f}")
            formatted_output.append(f"  Actual: ${actual:.2f}")
            formatted_output.append(f"  Variance: ${variance:.2f} ({variance_percent:.2f}%)")
    elif isinstance(result, dict):
        # Extract overall comparison
        budget = result.get("budget", 0)
        actual = result.get("actual", 0)
        variance = actual - budget
        variance_percent = (variance / budget) * 100 if budget > 0 else 0
        
        formatted_output.append(f"\nOverall:")
        formatted_output.append(f"  Budget: ${budget:.2f}")
        formatted_output.append(f"  Actual: ${actual:.2f}")
        formatted_output.append(f"  Variance: ${variance:.2f} ({variance_percent:.2f}%)")
        
        # Extract period breakdown if available
        if "periods" in result and isinstance(result["periods"], list):
            formatted_output.append("\nBy Period:")
            for period in result["periods"]:
                name = period.get("name", "Unknown")
                budget = period.get("budget", 0)
                actual = period.get("actual", 0)
                variance = actual - budget
                variance_percent = (variance / budget) * 100 if budget > 0 else 0
                
                formatted_output.append(f"\n  {name}:")
                formatted_output.append(f"    Budget: ${budget:.2f}")
                formatted_output.append(f"    Actual: ${actual:.2f}")
                formatted_output.append(f"    Variance: ${variance:.2f} ({variance_percent:.2f}%)")
    
    return "\n".join(formatted_output)

if __name__ == "__main__":
    # Check if API key and environment ID are set
    if not APPTIO_API_KEY:
        logger.error("APPTIO_API_KEY environment variable is not set")
        print("Error: APPTIO_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    
    if not APPTIO_ENV_ID:
        logger.error("APPTIO_ENV_ID environment variable is not set")
        print("Error: APPTIO_ENV_ID environment variable is not set", file=sys.stderr)
        sys.exit(1)
    
    # Initialize and run the server
    logger.info("Starting Apptio MCP server")
    mcp.run(transport='stdio')
