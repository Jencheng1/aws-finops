#!/usr/bin/env python3
"""
AWS Cost Explorer MCP Server Implementation

This server provides MCP tools for accessing AWS Cost Explorer data and integrating
with AWS Bedrock agents for cost optimization.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

import boto3
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (not stdout, which would break STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("aws-cost-explorer-mcp")

# Initialize FastMCP server
mcp = FastMCP("aws-cost-explorer")

# Initialize AWS clients
try:
    ce_client = boto3.client('ce')
    savingsplans_client = boto3.client('savingsplans')
    compute_optimizer_client = boto3.client('compute-optimizer')
except Exception as e:
    logger.error(f"Error initializing AWS clients: {e}")
    print(f"Error initializing AWS clients: {e}", file=sys.stderr)

# Helper functions
def format_cost_usage_data(data: Dict) -> str:
    """Format cost and usage data into a readable string.
    
    Args:
        data: Cost and usage data from AWS Cost Explorer
        
    Returns:
        Formatted cost and usage data as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "ResultsByTime" not in data:
        return "No cost and usage data available or invalid response format."
    
    results = data["ResultsByTime"]
    
    if not results:
        return "No cost and usage data available for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost and Usage Data:")
    
    for result in results:
        time_period = result["TimePeriod"]
        start = time_period["Start"]
        end = time_period["End"]
        
        formatted_output.append(f"\nPeriod: {start} to {end}")
        
        if "Total" in result:
            for metric, value in result["Total"].items():
                amount = value.get("Amount", "0")
                unit = value.get("Unit", "")
                formatted_output.append(f"  {metric}: {amount} {unit}")
        
        if "Groups" in result and result["Groups"]:
            formatted_output.append("\n  Breakdown:")
            for group in result["Groups"]:
                keys = group["Keys"]
                metrics = group["Metrics"]
                
                key_str = ", ".join(keys)
                formatted_output.append(f"    {key_str}:")
                
                for metric, value in metrics.items():
                    amount = value.get("Amount", "0")
                    unit = value.get("Unit", "")
                    formatted_output.append(f"      {metric}: {amount} {unit}")
    
    return "\n".join(formatted_output)

def format_savings_plans_recommendations(data: Dict) -> str:
    """Format Savings Plans recommendations into a readable string.
    
    Args:
        data: Savings Plans recommendations from AWS
        
    Returns:
        Formatted Savings Plans recommendations as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "SavingsPlansPurchaseRecommendationDetails" not in data:
        return "No Savings Plans recommendations available or invalid response format."
    
    recommendations = data["SavingsPlansPurchaseRecommendationDetails"]
    
    if not recommendations:
        return "No Savings Plans recommendations available."
    
    formatted_output = []
    formatted_output.append("Savings Plans Recommendations:")
    
    for rec in recommendations:
        term = rec.get("Term", "Unknown")
        payment_option = rec.get("PaymentOption", "Unknown")
        
        formatted_output.append(f"\nTerm: {term}")
        formatted_output.append(f"Payment Option: {payment_option}")
        
        if "SavingsPlansType" in rec:
            formatted_output.append(f"Type: {rec['SavingsPlansType']}")
        
        if "EstimatedSavingsAmount" in rec:
            amount = rec["EstimatedSavingsAmount"]
            formatted_output.append(f"Estimated Savings: ${amount}")
        
        if "EstimatedSavingsPercentage" in rec:
            percentage = rec["EstimatedSavingsPercentage"]
            formatted_output.append(f"Estimated Savings Percentage: {percentage}%")
        
        if "EstimatedMonthlySavingsAmount" in rec:
            amount = rec["EstimatedMonthlySavingsAmount"]
            formatted_output.append(f"Estimated Monthly Savings: ${amount}")
        
        if "EstimatedROI" in rec:
            roi = rec["EstimatedROI"]
            formatted_output.append(f"Estimated ROI: {roi}%")
        
        if "UpfrontCost" in rec:
            cost = rec["UpfrontCost"]
            formatted_output.append(f"Upfront Cost: ${cost}")
        
        if "RecurringCommitment" in rec:
            commitment = rec["RecurringCommitment"]
            formatted_output.append(f"Recurring Commitment: ${commitment}")
    
    return "\n".join(formatted_output)

def format_ri_recommendations(data: Dict) -> str:
    """Format Reserved Instance recommendations into a readable string.
    
    Args:
        data: Reserved Instance recommendations from AWS
        
    Returns:
        Formatted Reserved Instance recommendations as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "Recommendations" not in data:
        return "No Reserved Instance recommendations available or invalid response format."
    
    recommendations = data["Recommendations"]
    
    if not recommendations:
        return "No Reserved Instance recommendations available."
    
    formatted_output = []
    formatted_output.append("Reserved Instance Recommendations:")
    
    for rec in recommendations:
        account_id = rec.get("AccountId", "Unknown")
        instance_details = rec.get("InstanceDetails", {})
        current_instance = instance_details.get("CurrentInstance", {})
        recommended_instance = instance_details.get("RecommendedInstanceType", "Unknown")
        
        formatted_output.append(f"\nAccount: {account_id}")
        
        if current_instance:
            instance_type = current_instance.get("InstanceType", "Unknown")
            formatted_output.append(f"Current Instance Type: {instance_type}")
        
        formatted_output.append(f"Recommended Instance Type: {recommended_instance}")
        
        if "EstimatedMonthlySavings" in rec:
            savings = rec["EstimatedMonthlySavings"]
            currency = savings.get("Currency", "USD")
            amount = savings.get("Value", 0)
            formatted_output.append(f"Estimated Monthly Savings: {amount} {currency}")
        
        if "EstimatedSavingsPercentage" in rec:
            percentage = rec["EstimatedSavingsPercentage"]
            formatted_output.append(f"Estimated Savings Percentage: {percentage}%")
    
    return "\n".join(formatted_output)

def format_cost_anomalies(data: Dict) -> str:
    """Format cost anomalies into a readable string.
    
    Args:
        data: Cost anomalies from AWS
        
    Returns:
        Formatted cost anomalies as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "Anomalies" not in data:
        return "No cost anomalies available or invalid response format."
    
    anomalies = data["Anomalies"]
    
    if not anomalies:
        return "No cost anomalies detected for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost Anomalies:")
    
    for anomaly in anomalies:
        anomaly_id = anomaly.get("AnomalyId", "Unknown")
        anomaly_start_date = anomaly.get("AnomalyStartDate", "Unknown")
        anomaly_end_date = anomaly.get("AnomalyEndDate", "Unknown")
        
        formatted_output.append(f"\nAnomaly ID: {anomaly_id}")
        formatted_output.append(f"Period: {anomaly_start_date} to {anomaly_end_date}")
        
        if "RootCauses" in anomaly and anomaly["RootCauses"]:
            formatted_output.append("Root Causes:")
            for cause in anomaly["RootCauses"]:
                service = cause.get("Service", "Unknown")
                region = cause.get("Region", "Unknown")
                formatted_output.append(f"  Service: {service}, Region: {region}")
        
        if "Impact" in anomaly:
            impact = anomaly["Impact"]
            total_impact = impact.get("TotalImpact", 0)
            formatted_output.append(f"Total Impact: ${total_impact}")
        
        if "MonitorArn" in anomaly:
            monitor_arn = anomaly["MonitorArn"]
            formatted_output.append(f"Monitor ARN: {monitor_arn}")
    
    return "\n".join(formatted_output)

def format_cost_forecast(data: Dict) -> str:
    """Format cost forecast into a readable string.
    
    Args:
        data: Cost forecast from AWS
        
    Returns:
        Formatted cost forecast as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "ForecastResultsByTime" not in data:
        return "No cost forecast available or invalid response format."
    
    forecasts = data["ForecastResultsByTime"]
    
    if not forecasts:
        return "No cost forecast available for the specified period."
    
    formatted_output = []
    formatted_output.append("Cost Forecast:")
    
    for forecast in forecasts:
        time_period = forecast["TimePeriod"]
        start = time_period["Start"]
        end = time_period["End"]
        
        formatted_output.append(f"\nPeriod: {start} to {end}")
        
        if "MeanValue" in forecast:
            mean = forecast["MeanValue"]
            formatted_output.append(f"  Mean Forecast: ${mean}")
        
        if "PredictionIntervalLowerBound" in forecast:
            lower = forecast["PredictionIntervalLowerBound"]
            formatted_output.append(f"  Lower Bound: ${lower}")
        
        if "PredictionIntervalUpperBound" in forecast:
            upper = forecast["PredictionIntervalUpperBound"]
            formatted_output.append(f"  Upper Bound: ${upper}")
    
    return "\n".join(formatted_output)

def format_dimension_values(data: Dict) -> str:
    """Format dimension values into a readable string.
    
    Args:
        data: Dimension values from AWS
        
    Returns:
        Formatted dimension values as a string
    """
    if "error" in data:
        return f"Error: {data['error']} - {data.get('message', '')}"
    
    if "DimensionValues" not in data:
        return "No dimension values available or invalid response format."
    
    values = data["DimensionValues"]
    
    if not values:
        return "No dimension values available for the specified dimension."
    
    formatted_output = []
    formatted_output.append("Dimension Values:")
    
    for value in values:
        if "Value" in value:
            formatted_output.append(f"  {value['Value']}")
        elif "Attributes" in value:
            attributes = value["Attributes"]
            formatted_output.append(f"  {json.dumps(attributes)}")
    
    return "\n".join(formatted_output)

# MCP Tools
@mcp.tool()
async def get_cost_usage(start_date: str, end_date: str, granularity: str = "DAILY", group_by: str = None) -> str:
    """Get cost and usage data from AWS Cost Explorer.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Data granularity (DAILY, MONTHLY)
        group_by: Optional dimension to group by (e.g., SERVICE, LINKED_ACCOUNT)
    
    Returns:
        Formatted cost and usage data as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    # Validate granularity
    if granularity not in ["DAILY", "MONTHLY"]:
        return "Error: Invalid granularity. Please use 'DAILY' or 'MONTHLY'."
    
    # Prepare request parameters
    params = {
        "TimePeriod": {
            "Start": start_date,
            "End": end_date
        },
        "Granularity": granularity,
        "Metrics": ["UnblendedCost", "UsageQuantity"]
    }
    
    # Add group by if specified
    if group_by:
        params["GroupBy"] = [{"Type": "DIMENSION", "Key": group_by}]
    
    try:
        # Make API request
        response = ce_client.get_cost_and_usage(**params)
        return format_cost_usage_data(response)
    except Exception as e:
        logger.error(f"Error getting cost and usage data: {e}")
        return {"error": "Error getting cost and usage data", "message": str(e)}

@mcp.tool()
async def get_savings_plans_recommendations(lookback_period: str = "SIXTY_DAYS", payment_option: str = "NO_UPFRONT") -> str:
    """Get Savings Plans recommendations from AWS.
    
    Args:
        lookback_period: Period to analyze for recommendations (SEVEN_DAYS, THIRTY_DAYS, SIXTY_DAYS)
        payment_option: Payment option (NO_UPFRONT, PARTIAL_UPFRONT, ALL_UPFRONT)
    
    Returns:
        Formatted Savings Plans recommendations as a string
    """
    # Validate lookback period
    if lookback_period not in ["SEVEN_DAYS", "THIRTY_DAYS", "SIXTY_DAYS"]:
        return "Error: Invalid lookback period. Please use 'SEVEN_DAYS', 'THIRTY_DAYS', or 'SIXTY_DAYS'."
    
    # Validate payment option
    if payment_option not in ["NO_UPFRONT", "PARTIAL_UPFRONT", "ALL_UPFRONT"]:
        return "Error: Invalid payment option. Please use 'NO_UPFRONT', 'PARTIAL_UPFRONT', or 'ALL_UPFRONT'."
    
    try:
        # Make API request
        response = savingsplans_client.get_savings_plans_purchase_recommendation(
            LookbackPeriodInDays=lookback_period,
            TermInYears="ONE_YEAR",
            PaymentOption=payment_option,
            SavingsPlansType="COMPUTE_SP"
        )
        return format_savings_plans_recommendations(response)
    except Exception as e:
        logger.error(f"Error getting Savings Plans recommendations: {e}")
        return {"error": "Error getting Savings Plans recommendations", "message": str(e)}

@mcp.tool()
async def get_ri_recommendations() -> str:
    """Get Reserved Instance recommendations from AWS.
    
    Returns:
        Formatted Reserved Instance recommendations as a string
    """
    try:
        # Make API request
        response = compute_optimizer_client.get_ec2_instance_recommendations()
        return format_ri_recommendations(response)
    except Exception as e:
        logger.error(f"Error getting Reserved Instance recommendations: {e}")
        return {"error": "Error getting Reserved Instance recommendations", "message": str(e)}

@mcp.tool()
async def get_cost_anomalies(start_date: str = None, end_date: str = None) -> str:
    """Get detected cost anomalies from AWS.
    
    Args:
        start_date: Optional start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: Optional end date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Formatted cost anomalies as a string
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
    
    try:
        # Make API request
        response = ce_client.get_anomalies(
            DateInterval={
                "StartDate": start_date,
                "EndDate": end_date
            }
        )
        return format_cost_anomalies(response)
    except Exception as e:
        logger.error(f"Error getting cost anomalies: {e}")
        return {"error": "Error getting cost anomalies", "message": str(e)}

@mcp.tool()
async def get_cost_forecast(start_date: str = None, end_date: str = None) -> str:
    """Get cost forecast from AWS.
    
    Args:
        start_date: Optional start date in YYYY-MM-DD format (defaults to tomorrow)
        end_date: Optional end date in YYYY-MM-DD format (defaults to 3 months from tomorrow)
    
    Returns:
        Formatted cost forecast as a string
    """
    # Set default dates if not provided
    if not start_date:
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    try:
        # Make API request
        response = ce_client.get_cost_forecast(
            TimePeriod={
                "Start": start_date,
                "End": end_date
            },
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY"
        )
        return format_cost_forecast(response)
    except Exception as e:
        logger.error(f"Error getting cost forecast: {e}")
        return {"error": "Error getting cost forecast", "message": str(e)}

@mcp.tool()
async def get_dimension_values(dimension: str) -> str:
    """Get dimension values from AWS Cost Explorer.
    
    Args:
        dimension: Dimension to get values for (e.g., SERVICE, LINKED_ACCOUNT)
    
    Returns:
        Formatted dimension values as a string
    """
    # Validate dimension
    valid_dimensions = [
        "AZ", "INSTANCE_TYPE", "LINKED_ACCOUNT", "OPERATION", "PURCHASE_TYPE",
        "REGION", "SERVICE", "USAGE_TYPE", "PLATFORM", "TENANCY", "RECORD_TYPE",
        "LEGAL_ENTITY_NAME", "INVOICING_ENTITY", "DEPLOYMENT_OPTION", "DATABASE_ENGINE",
        "CACHE_ENGINE", "INSTANCE_TYPE_FAMILY", "BILLING_ENTITY", "RESERVATION_ID",
        "SAVINGS_PLANS_TYPE", "SAVINGS_PLAN_ARN", "OPERATING_SYSTEM"
    ]
    
    if dimension not in valid_dimensions:
        return f"Error: Invalid dimension. Please use one of: {', '.join(valid_dimensions)}"
    
    try:
        # Make API request
        response = ce_client.get_dimension_values(
            TimePeriod={
                "Start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "End": datetime.now().strftime("%Y-%m-%d")
            },
            Dimension=dimension
        )
        return format_dimension_values(response)
    except Exception as e:
        logger.error(f"Error getting dimension values: {e}")
        return {"error": "Error getting dimension values", "message": str(e)}

@mcp.tool()
async def get_cost_by_service(start_date: str, end_date: str) -> str:
    """Get cost breakdown by service from AWS Cost Explorer.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted cost by service data as a string
    """
    return await get_cost_usage(start_date, end_date, "MONTHLY", "SERVICE")

@mcp.tool()
async def get_cost_by_account(start_date: str, end_date: str) -> str:
    """Get cost breakdown by account from AWS Cost Explorer.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted cost by account data as a string
    """
    return await get_cost_usage(start_date, end_date, "MONTHLY", "LINKED_ACCOUNT")

@mcp.tool()
async def get_cost_by_region(start_date: str, end_date: str) -> str:
    """Get cost breakdown by region from AWS Cost Explorer.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted cost by region data as a string
    """
    return await get_cost_usage(start_date, end_date, "MONTHLY", "REGION")

@mcp.tool()
async def get_savings_plans_utilization(start_date: str, end_date: str) -> str:
    """Get Savings Plans utilization from AWS.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted Savings Plans utilization as a string
    """
    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD format."
    
    try:
        # Make API request
        response = ce_client.get_savings_plans_utilization(
            TimePeriod={
                "Start": start_date,
                "End": end_date
            }
        )
        
        if "error" in response:
            return f"Error: {response['error']} - {response.get('message', '')}"
        
        if "SavingsPlansUtilizationsByTime" not in response:
            return "No Savings Plans utilization data available or invalid response format."
        
        utilizations = response["SavingsPlansUtilizationsByTime"]
        
        if not utilizations:
            return "No Savings Plans utilization data available for the specified period."
        
        formatted_output = []
        formatted_output.append("Savings Plans Utilization:")
        
        for utilization in utilizations:
            time_period = utilization["TimePeriod"]
            start = time_period["Start"]
            end = time_period["End"]
            
            formatted_output.append(f"\nPeriod: {start} to {end}")
            
            if "Total" in utilization:
                total = utilization["Total"]
                
                if "Utilization" in total:
                    util = total["Utilization"]
                    formatted_output.append(f"  Utilization: {util}%")
                
                if "SavingsPlansCount" in total:
                    count = total["SavingsPlansCount"]
                    formatted_output.append(f"  Savings Plans Count: {count}")
                
                if "AmortizedCommitment" in total:
                    commitment = total["AmortizedCommitment"]
                    amount = commitment.get("Amount", "0")
                    unit = commitment.get("Unit", "")
                    formatted_output.append(f"  Amortized Commitment: {amount} {unit}")
                
                if "UsedCommitment" in total:
                    used = total["UsedCommitment"]
                    amount = used.get("Amount", "0")
                    unit = used.get("Unit", "")
                    formatted_output.append(f"  Used Commitment: {amount} {unit}")
                
                if "UnusedCommitment" in total:
                    unused = total["UnusedCommitment"]
                    amount = unused.get("Amount", "0")
                    unit = unused.get("Unit", "")
                    formatted_output.append(f"  Unused Commitment: {amount} {unit}")
        
        return "\n".join(formatted_output)
    except Exception as e:
        logger.error(f"Error getting Savings Plans utilization: {e}")
        return {"error": "Error getting Savings Plans utilization", "message": str(e)}

if __name__ == "__main__":
    # Initialize and run the server
    logger.info("Starting AWS Cost Explorer MCP server")
    mcp.run(transport='stdio')
