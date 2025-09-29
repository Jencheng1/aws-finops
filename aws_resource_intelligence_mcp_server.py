#!/usr/bin/env python3
"""
AWS Resource Intelligence MCP Server Implementation

This server provides MCP tools for analyzing AWS resources and identifying
optimization opportunities, including idle resources and rightsizing recommendations.
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
logger = logging.getLogger("aws-resource-intelligence-mcp")

# Initialize FastMCP server
mcp = FastMCP("aws-resource-intelligence")

# Initialize AWS clients
try:
    ec2_client = boto3.client('ec2')
    rds_client = boto3.client('rds')
    cloudwatch_client = boto3.client('cloudwatch')
    compute_optimizer_client = boto3.client('compute-optimizer')
    trusted_advisor_client = boto3.client('support')
    resource_groups_tagging_client = boto3.client('resourcegroupstaggingapi')
except Exception as e:
    logger.error(f"Error initializing AWS clients: {e}")
    print(f"Error initializing AWS clients: {e}", file=sys.stderr)

# Helper functions
def format_idle_ec2_instances(instances: List[Dict]) -> str:
    """Format idle EC2 instances into a readable string.
    
    Args:
        instances: List of idle EC2 instances
        
    Returns:
        Formatted idle EC2 instances as a string
    """
    if not instances:
        return "No idle EC2 instances found."
    
    formatted_output = []
    formatted_output.append("Idle EC2 Instances:")
    
    for instance in instances:
        instance_id = instance.get("InstanceId", "Unknown")
        instance_type = instance.get("InstanceType", "Unknown")
        state = instance.get("State", {}).get("Name", "Unknown")
        
        formatted_output.append(f"\nInstance ID: {instance_id}")
        formatted_output.append(f"  Instance Type: {instance_type}")
        formatted_output.append(f"  State: {state}")
        
        if "Tags" in instance:
            name_tag = next((tag["Value"] for tag in instance["Tags"] if tag["Key"] == "Name"), "Unnamed")
            formatted_output.append(f"  Name: {name_tag}")
        
        if "CpuUtilization" in instance:
            cpu = instance["CpuUtilization"]
            formatted_output.append(f"  CPU Utilization: {cpu}%")
        
        if "NetworkIn" in instance:
            net_in = instance["NetworkIn"]
            formatted_output.append(f"  Network In: {net_in} bytes/s")
        
        if "NetworkOut" in instance:
            net_out = instance["NetworkOut"]
            formatted_output.append(f"  Network Out: {net_out} bytes/s")
        
        if "EstimatedMonthlySavings" in instance:
            savings = instance["EstimatedMonthlySavings"]
            formatted_output.append(f"  Estimated Monthly Savings: ${savings:.2f}")
    
    return "\n".join(formatted_output)

def format_idle_ebs_volumes(volumes: List[Dict]) -> str:
    """Format idle EBS volumes into a readable string.
    
    Args:
        volumes: List of idle EBS volumes
        
    Returns:
        Formatted idle EBS volumes as a string
    """
    if not volumes:
        return "No idle EBS volumes found."
    
    formatted_output = []
    formatted_output.append("Idle EBS Volumes:")
    
    for volume in volumes:
        volume_id = volume.get("VolumeId", "Unknown")
        volume_type = volume.get("VolumeType", "Unknown")
        size = volume.get("Size", 0)
        state = volume.get("State", "Unknown")
        
        formatted_output.append(f"\nVolume ID: {volume_id}")
        formatted_output.append(f"  Volume Type: {volume_type}")
        formatted_output.append(f"  Size: {size} GB")
        formatted_output.append(f"  State: {state}")
        
        if "CreateTime" in volume:
            create_time = volume["CreateTime"].strftime("%Y-%m-%d %H:%M:%S")
            formatted_output.append(f"  Created: {create_time}")
        
        if "Tags" in volume:
            name_tag = next((tag["Value"] for tag in volume["Tags"] if tag["Key"] == "Name"), "Unnamed")
            formatted_output.append(f"  Name: {name_tag}")
        
        if "EstimatedMonthlySavings" in volume:
            savings = volume["EstimatedMonthlySavings"]
            formatted_output.append(f"  Estimated Monthly Savings: ${savings:.2f}")
    
    return "\n".join(formatted_output)

def format_idle_rds_instances(instances: List[Dict]) -> str:
    """Format idle RDS instances into a readable string.
    
    Args:
        instances: List of idle RDS instances
        
    Returns:
        Formatted idle RDS instances as a string
    """
    if not instances:
        return "No idle RDS instances found."
    
    formatted_output = []
    formatted_output.append("Idle RDS Instances:")
    
    for instance in instances:
        db_instance_id = instance.get("DBInstanceIdentifier", "Unknown")
        db_instance_class = instance.get("DBInstanceClass", "Unknown")
        engine = instance.get("Engine", "Unknown")
        status = instance.get("DBInstanceStatus", "Unknown")
        
        formatted_output.append(f"\nDB Instance ID: {db_instance_id}")
        formatted_output.append(f"  DB Instance Class: {db_instance_class}")
        formatted_output.append(f"  Engine: {engine}")
        formatted_output.append(f"  Status: {status}")
        
        if "CpuUtilization" in instance:
            cpu = instance["CpuUtilization"]
            formatted_output.append(f"  CPU Utilization: {cpu}%")
        
        if "DatabaseConnections" in instance:
            connections = instance["DatabaseConnections"]
            formatted_output.append(f"  Database Connections: {connections}")
        
        if "EstimatedMonthlySavings" in instance:
            savings = instance["EstimatedMonthlySavings"]
            formatted_output.append(f"  Estimated Monthly Savings: ${savings:.2f}")
    
    return "\n".join(formatted_output)

def format_rightsizing_recommendations(recommendations: List[Dict]) -> str:
    """Format rightsizing recommendations into a readable string.
    
    Args:
        recommendations: List of rightsizing recommendations
        
    Returns:
        Formatted rightsizing recommendations as a string
    """
    if not recommendations:
        return "No rightsizing recommendations found."
    
    formatted_output = []
    formatted_output.append("Rightsizing Recommendations:")
    
    for rec in recommendations:
        resource_id = rec.get("ResourceId", "Unknown")
        resource_type = rec.get("ResourceType", "Unknown")
        finding = rec.get("Finding", "Unknown")
        
        formatted_output.append(f"\nResource ID: {resource_id}")
        formatted_output.append(f"  Resource Type: {resource_type}")
        formatted_output.append(f"  Finding: {finding}")
        
        if "CurrentConfiguration" in rec:
            current = rec["CurrentConfiguration"]
            formatted_output.append(f"  Current Configuration: {current}")
        
        if "RecommendedConfiguration" in rec:
            recommended = rec["RecommendedConfiguration"]
            formatted_output.append(f"  Recommended Configuration: {recommended}")
        
        if "EstimatedMonthlySavings" in rec:
            savings = rec["EstimatedMonthlySavings"]
            currency = savings.get("Currency", "USD")
            amount = savings.get("Value", 0)
            formatted_output.append(f"  Estimated Monthly Savings: {amount} {currency}")
        
        if "SavingsOpportunityPercentage" in rec:
            percentage = rec["SavingsOpportunityPercentage"]
            formatted_output.append(f"  Savings Opportunity: {percentage}%")
    
    return "\n".join(formatted_output)

def format_trusted_advisor_recommendations(recommendations: List[Dict]) -> str:
    """Format Trusted Advisor recommendations into a readable string.
    
    Args:
        recommendations: List of Trusted Advisor recommendations
        
    Returns:
        Formatted Trusted Advisor recommendations as a string
    """
    if not recommendations:
        return "No Trusted Advisor recommendations found."
    
    formatted_output = []
    formatted_output.append("Trusted Advisor Cost Optimization Recommendations:")
    
    for rec in recommendations:
        check_id = rec.get("id", "Unknown")
        name = rec.get("name", "Unknown")
        status = rec.get("status", "Unknown")
        
        formatted_output.append(f"\nCheck: {name}")
        formatted_output.append(f"  Status: {status}")
        
        if "resourcesSummary" in rec:
            summary = rec["resourcesSummary"]
            resources_flagged = summary.get("resourcesFlagged", 0)
            resources_processed = summary.get("resourcesProcessed", 0)
            resources_suppressed = summary.get("resourcesSuppressed", 0)
            
            formatted_output.append(f"  Resources Flagged: {resources_flagged}")
            formatted_output.append(f"  Resources Processed: {resources_processed}")
            formatted_output.append(f"  Resources Suppressed: {resources_suppressed}")
        
        if "flaggedResources" in rec:
            flagged = rec["flaggedResources"]
            if flagged:
                formatted_output.append("  Flagged Resources:")
                for resource in flagged[:5]:  # Limit to 5 resources
                    resource_id = resource.get("resourceId", "Unknown")
                    region = resource.get("region", "Unknown")
                    formatted_output.append(f"    Resource ID: {resource_id}, Region: {region}")
                
                if len(flagged) > 5:
                    formatted_output.append(f"    ... and {len(flagged) - 5} more resources")
        
        if "estimatedMonthlySavings" in rec:
            savings = rec["estimatedMonthlySavings"]
            formatted_output.append(f"  Estimated Monthly Savings: ${savings:.2f}")
    
    return "\n".join(formatted_output)

def format_untagged_resources(resources: List[Dict]) -> str:
    """Format untagged resources into a readable string.
    
    Args:
        resources: List of untagged resources
        
    Returns:
        Formatted untagged resources as a string
    """
    if not resources:
        return "No untagged resources found."
    
    formatted_output = []
    formatted_output.append("Untagged Resources:")
    
    for resource in resources:
        resource_arn = resource.get("ResourceARN", "Unknown")
        resource_type = resource.get("ResourceType", "Unknown")
        
        formatted_output.append(f"\nResource ARN: {resource_arn}")
        formatted_output.append(f"  Resource Type: {resource_type}")
    
    return "\n".join(formatted_output)

# MCP Tools
@mcp.tool()
async def get_idle_ec2_instances(days: int = 14, cpu_threshold: float = 10.0) -> str:
    """Get idle EC2 instances based on CloudWatch metrics.
    
    Args:
        days: Number of days to look back
        cpu_threshold: CPU utilization threshold (%) below which an instance is considered idle
    
    Returns:
        Formatted idle EC2 instances as a string
    """
    try:
        # Get all running EC2 instances
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )
        
        instances = []
        for reservation in response.get("Reservations", []):
            instances.extend(reservation.get("Instances", []))
        
        if not instances:
            return "No running EC2 instances found."
        
        # Check CloudWatch metrics for each instance
        idle_instances = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        for instance in instances:
            instance_id = instance["InstanceId"]
            
            # Get CPU utilization
            cpu_response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            # Get network traffic
            net_in_response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkIn',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            net_out_response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkOut',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            # Calculate average metrics
            cpu_datapoints = cpu_response.get("Datapoints", [])
            net_in_datapoints = net_in_response.get("Datapoints", [])
            net_out_datapoints = net_out_response.get("Datapoints", [])
            
            avg_cpu = sum(dp["Average"] for dp in cpu_datapoints) / len(cpu_datapoints) if cpu_datapoints else 0
            avg_net_in = sum(dp["Average"] for dp in net_in_datapoints) / len(net_in_datapoints) if net_in_datapoints else 0
            avg_net_out = sum(dp["Average"] for dp in net_out_datapoints) / len(net_out_datapoints) if net_out_datapoints else 0
            
            # Check if instance is idle
            if avg_cpu < cpu_threshold:
                # Add metrics to instance data
                instance["CpuUtilization"] = avg_cpu
                instance["NetworkIn"] = avg_net_in
                instance["NetworkOut"] = avg_net_out
                
                # Estimate monthly savings
                instance_type = instance["InstanceType"]
                # This is a simplified calculation; in a real implementation, you would use pricing API
                estimated_savings = 0.0
                if instance_type.startswith("t3."):
                    estimated_savings = 30.0  # $30/month
                elif instance_type.startswith("m5."):
                    estimated_savings = 70.0  # $70/month
                elif instance_type.startswith("c5."):
                    estimated_savings = 85.0  # $85/month
                else:
                    estimated_savings = 50.0  # Default
                
                instance["EstimatedMonthlySavings"] = estimated_savings
                
                idle_instances.append(instance)
        
        return format_idle_ec2_instances(idle_instances)
    except Exception as e:
        logger.error(f"Error getting idle EC2 instances: {e}")
        return f"Error getting idle EC2 instances: {str(e)}"

@mcp.tool()
async def get_idle_ebs_volumes() -> str:
    """Get idle EBS volumes that are not attached to any instance.
    
    Returns:
        Formatted idle EBS volumes as a string
    """
    try:
        # Get all available (unattached) EBS volumes
        response = ec2_client.describe_volumes(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ]
        )
        
        volumes = response.get("Volumes", [])
        
        if not volumes:
            return "No idle EBS volumes found."
        
        # Add estimated monthly savings
        for volume in volumes:
            volume_type = volume["VolumeType"]
            size = volume["Size"]
            
            # This is a simplified calculation; in a real implementation, you would use pricing API
            estimated_savings = 0.0
            if volume_type == "gp2":
                estimated_savings = size * 0.10  # $0.10 per GB per month
            elif volume_type == "io1":
                estimated_savings = size * 0.125  # $0.125 per GB per month
            elif volume_type == "st1":
                estimated_savings = size * 0.045  # $0.045 per GB per month
            elif volume_type == "sc1":
                estimated_savings = size * 0.025  # $0.025 per GB per month
            else:
                estimated_savings = size * 0.08  # Default
            
            volume["EstimatedMonthlySavings"] = estimated_savings
        
        return format_idle_ebs_volumes(volumes)
    except Exception as e:
        logger.error(f"Error getting idle EBS volumes: {e}")
        return f"Error getting idle EBS volumes: {str(e)}"

@mcp.tool()
async def get_idle_rds_instances(days: int = 14, cpu_threshold: float = 10.0, connection_threshold: int = 5) -> str:
    """Get idle RDS instances based on CloudWatch metrics.
    
    Args:
        days: Number of days to look back
        cpu_threshold: CPU utilization threshold (%) below which an instance is considered idle
        connection_threshold: Database connection threshold below which an instance is considered idle
    
    Returns:
        Formatted idle RDS instances as a string
    """
    try:
        # Get all RDS instances
        response = rds_client.describe_db_instances()
        
        instances = response.get("DBInstances", [])
        
        if not instances:
            return "No RDS instances found."
        
        # Check CloudWatch metrics for each instance
        idle_instances = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        for instance in instances:
            db_instance_id = instance["DBInstanceIdentifier"]
            
            # Get CPU utilization
            cpu_response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            # Get database connections
            conn_response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )
            
            # Calculate average metrics
            cpu_datapoints = cpu_response.get("Datapoints", [])
            conn_datapoints = conn_response.get("Datapoints", [])
            
            avg_cpu = sum(dp["Average"] for dp in cpu_datapoints) / len(cpu_datapoints) if cpu_datapoints else 0
            avg_conn = sum(dp["Average"] for dp in conn_datapoints) / len(conn_datapoints) if conn_datapoints else 0
            
            # Check if instance is idle
            if avg_cpu < cpu_threshold and avg_conn < connection_threshold:
                # Add metrics to instance data
                instance["CpuUtilization"] = avg_cpu
                instance["DatabaseConnections"] = avg_conn
                
                # Estimate monthly savings
                db_instance_class = instance["DBInstanceClass"]
                # This is a simplified calculation; in a real implementation, you would use pricing API
                estimated_savings = 0.0
                if db_instance_class.startswith("db.t3."):
                    estimated_savings = 50.0  # $50/month
                elif db_instance_class.startswith("db.m5."):
                    estimated_savings = 150.0  # $150/month
                elif db_instance_class.startswith("db.r5."):
                    estimated_savings = 200.0  # $200/month
                else:
                    estimated_savings = 100.0  # Default
                
                instance["EstimatedMonthlySavings"] = estimated_savings
                
                idle_instances.append(instance)
        
        return format_idle_rds_instances(idle_instances)
    except Exception as e:
        logger.error(f"Error getting idle RDS instances: {e}")
        return f"Error getting idle RDS instances: {str(e)}"

@mcp.tool()
async def get_rightsizing_recommendations() -> str:
    """Get rightsizing recommendations for EC2 instances.
    
    Returns:
        Formatted rightsizing recommendations as a string
    """
    try:
        # Get EC2 instance recommendations
        response = compute_optimizer_client.get_ec2_instance_recommendations()
        
        recommendations = response.get("instanceRecommendations", [])
        
        if not recommendations:
            return "No rightsizing recommendations found."
        
        # Format recommendations
        formatted_recommendations = []
        for rec in recommendations:
            resource_id = rec["instanceArn"].split("/")[-1]
            
            formatted_rec = {
                "ResourceId": resource_id,
                "ResourceType": "EC2 Instance",
                "Finding": rec["finding"],
                "CurrentConfiguration": rec["currentInstanceType"],
                "RecommendedConfiguration": rec["recommendationOptions"][0]["instanceType"] if rec["recommendationOptions"] else "No recommendation"
            }
            
            # Add savings information if available
            if rec["recommendationOptions"] and "estimatedMonthlySavings" in rec["recommendationOptions"][0]:
                formatted_rec["EstimatedMonthlySavings"] = rec["recommendationOptions"][0]["estimatedMonthlySavings"]
            
            if rec["recommendationOptions"] and "savingsOpportunity" in rec["recommendationOptions"][0]:
                formatted_rec["SavingsOpportunityPercentage"] = rec["recommendationOptions"][0]["savingsOpportunity"]["savingsOpportunityPercentage"]
            
            formatted_recommendations.append(formatted_rec)
        
        return format_rightsizing_recommendations(formatted_recommendations)
    except Exception as e:
        logger.error(f"Error getting rightsizing recommendations: {e}")
        return f"Error getting rightsizing recommendations: {str(e)}"

@mcp.tool()
async def get_trusted_advisor_recommendations() -> str:
    """Get cost optimization recommendations from AWS Trusted Advisor.
    
    Returns:
        Formatted Trusted Advisor recommendations as a string
    """
    try:
        # Get Trusted Advisor checks
        response = trusted_advisor_client.describe_trusted_advisor_checks(language="en")
        
        checks = response.get("checks", [])
        
        # Filter for cost optimization checks
        cost_checks = [check for check in checks if check["category"] == "cost_optimizing"]
        
        if not cost_checks:
            return "No cost optimization checks found in Trusted Advisor."
        
        # Get check results
        check_results = []
        for check in cost_checks:
            check_id = check["id"]
            
            result_response = trusted_advisor_client.describe_trusted_advisor_check_result(
                checkId=check_id,
                language="en"
            )
            
            result = result_response.get("result", {})
            result["id"] = check_id
            result["name"] = check["name"]
            
            check_results.append(result)
        
        return format_trusted_advisor_recommendations(check_results)
    except Exception as e:
        logger.error(f"Error getting Trusted Advisor recommendations: {e}")
        return f"Error getting Trusted Advisor recommendations: {str(e)}"

@mcp.tool()
async def get_untagged_resources() -> str:
    """Get resources that are not properly tagged.
    
    Returns:
        Formatted untagged resources as a string
    """
    try:
        # Get resources without tags
        response = resource_groups_tagging_client.get_resources(
            ResourcesPerPage=100,
            TagFilters=[
                {
                    'Key': 'Environment',
                    'Values': []
                }
            ]
        )
        
        resources = response.get("ResourceTagMappingList", [])
        
        return format_untagged_resources(resources)
    except Exception as e:
        logger.error(f"Error getting untagged resources: {e}")
        return f"Error getting untagged resources: {str(e)}"

@mcp.tool()
async def get_resource_count_by_type() -> str:
    """Get count of AWS resources by type.
    
    Returns:
        Formatted resource count by type as a string
    """
    try:
        # Get all resources
        response = resource_groups_tagging_client.get_resources(ResourcesPerPage=100)
        
        resources = response.get("ResourceTagMappingList", [])
        
        if not resources:
            return "No resources found."
        
        # Count resources by type
        resource_counts = {}
        for resource in resources:
            resource_arn = resource["ResourceARN"]
            resource_type = resource_arn.split(":")[2]
            
            if resource_type in resource_counts:
                resource_counts[resource_type] += 1
            else:
                resource_counts[resource_type] = 1
        
        # Format output
        formatted_output = []
        formatted_output.append("Resource Count by Type:")
        
        for resource_type, count in sorted(resource_counts.items(), key=lambda x: x[1], reverse=True):
            formatted_output.append(f"  {resource_type}: {count}")
        
        return "\n".join(formatted_output)
    except Exception as e:
        logger.error(f"Error getting resource count by type: {e}")
        return f"Error getting resource count by type: {str(e)}"

@mcp.tool()
async def get_resource_count_by_region() -> str:
    """Get count of AWS resources by region.
    
    Returns:
        Formatted resource count by region as a string
    """
    try:
        # Get all resources
        response = resource_groups_tagging_client.get_resources(ResourcesPerPage=100)
        
        resources = response.get("ResourceTagMappingList", [])
        
        if not resources:
            return "No resources found."
        
        # Count resources by region
        region_counts = {}
        for resource in resources:
            resource_arn = resource["ResourceARN"]
            parts = resource_arn.split(":")
            
            if len(parts) >= 4:
                region = parts[3]
                
                if region in region_counts:
                    region_counts[region] += 1
                else:
                    region_counts[region] = 1
        
        # Format output
        formatted_output = []
        formatted_output.append("Resource Count by Region:")
        
        for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True):
            formatted_output.append(f"  {region}: {count}")
        
        return "\n".join(formatted_output)
    except Exception as e:
        logger.error(f"Error getting resource count by region: {e}")
        return f"Error getting resource count by region: {str(e)}"

@mcp.tool()
async def get_resource_count_by_tag(tag_key: str) -> str:
    """Get count of AWS resources by tag value.
    
    Args:
        tag_key: The tag key to group by (e.g., "Environment", "Project")
    
    Returns:
        Formatted resource count by tag value as a string
    """
    try:
        # Get all resources with the specified tag
        response = resource_groups_tagging_client.get_resources(
            ResourcesPerPage=100,
            TagFilters=[
                {
                    'Key': tag_key
                }
            ]
        )
        
        resources = response.get("ResourceTagMappingList", [])
        
        if not resources:
            return f"No resources found with tag key '{tag_key}'."
        
        # Count resources by tag value
        tag_value_counts = {}
        for resource in resources:
            tags = resource.get("Tags", [])
            
            for tag in tags:
                if tag["Key"] == tag_key:
                    tag_value = tag["Value"]
                    
                    if tag_value in tag_value_counts:
                        tag_value_counts[tag_value] += 1
                    else:
                        tag_value_counts[tag_value] = 1
        
        # Format output
        formatted_output = []
        formatted_output.append(f"Resource Count by '{tag_key}' Tag Value:")
        
        for tag_value, count in sorted(tag_value_counts.items(), key=lambda x: x[1], reverse=True):
            formatted_output.append(f"  {tag_value}: {count}")
        
        return "\n".join(formatted_output)
    except Exception as e:
        logger.error(f"Error getting resource count by tag: {e}")
        return f"Error getting resource count by tag: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    logger.info("Starting AWS Resource Intelligence MCP server")
    mcp.run(transport='stdio')
