# FinOps Copilot User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [Cost Analysis](#cost-analysis)
5. [Optimization Recommendations](#optimization-recommendations)
6. [Tagging Compliance](#tagging-compliance)
7. [Cost Forecasting](#cost-forecasting)
8. [Executive Reports](#executive-reports)
9. [Settings and Configuration](#settings-and-configuration)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

## Introduction

FinOps Copilot is an AI-powered AWS cost optimization solution that helps you identify cost-saving opportunities, improve resource utilization, and enhance tagging compliance across your AWS environment. This user guide will help you navigate the system and make the most of its features.

## Getting Started

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, or Edge)
- AWS account with appropriate permissions
- Network access to the FinOps Copilot dashboard URL

### Accessing the Dashboard

1. Open your web browser and navigate to the FinOps Copilot dashboard URL provided by your administrator.
2. Log in using your credentials (username and password or SSO).
3. If this is your first time logging in, you may be prompted to complete a setup wizard.

### Initial Setup

If you're setting up FinOps Copilot for the first time, you'll need to:

1. Connect your AWS accounts:
   - Navigate to Settings > AWS Accounts
   - Click "Add AWS Account"
   - Follow the instructions to create an IAM role with the necessary permissions
   - Enter the AWS account ID and role name

2. Configure data collection:
   - Navigate to Settings > Data Collection
   - Select the data sources you want to enable (Cost Explorer, CloudWatch, etc.)
   - Set the data refresh frequency

3. Set up user access:
   - Navigate to Settings > User Management
   - Add users and assign appropriate roles
   - Configure SSO if needed

## Dashboard Overview

The FinOps Copilot dashboard is organized into several sections:

![Dashboard Overview](/home/ubuntu/finops-copilot-presentation/images/streamlit_dashboard.png)

### Navigation Menu

The left sidebar contains the main navigation menu with the following sections:

- **Overview**: High-level summary of costs and recommendations
- **Cost Analysis**: Detailed cost breakdowns and trends
- **Recommendations**: Cost optimization recommendations
- **Tagging Compliance**: Resource tagging analysis
- **Forecasting**: Cost forecasts and budget tracking
- **Reports**: Generate and download reports
- **Settings**: System configuration

### Overview Page

The Overview page provides a high-level summary of your AWS costs and optimization opportunities:

- **Cost Summary**: Current month costs, month-over-month change, and year-over-year comparison
- **Top Services**: Bar chart showing costs by AWS service
- **Cost Trend**: Line chart showing cost trends over time
- **Savings Opportunities**: Summary of potential cost savings
- **Recent Recommendations**: Latest cost optimization recommendations

## Cost Analysis

The Cost Analysis section provides detailed insights into your AWS costs:

### Cost Explorer

The Cost Explorer allows you to analyze your AWS costs with various dimensions and filters:

1. **Time Range**: Select the time period for analysis (e.g., last 7 days, last 30 days, custom range)
2. **Granularity**: Choose the data granularity (hourly, daily, monthly)
3. **Group By**: Select how to group the data (service, account, region, etc.)
4. **Filters**: Apply filters to focus on specific services, accounts, or tags

### Cost Breakdown

The Cost Breakdown view shows your costs organized by different dimensions:

- **By Service**: Costs broken down by AWS service
- **By Account**: Costs broken down by AWS account
- **By Region**: Costs broken down by AWS region
- **By Tag**: Costs broken down by resource tags

### Cost Anomalies

The Cost Anomalies view highlights unusual spending patterns:

- **Recent Anomalies**: List of detected cost anomalies
- **Anomaly Details**: Drill-down into specific anomalies
- **Anomaly Settings**: Configure anomaly detection thresholds

## Optimization Recommendations

The Recommendations section provides actionable cost-saving opportunities:

### Recommendation Types

FinOps Copilot provides several types of recommendations:

- **Right-sizing**: Recommendations for resizing over-provisioned resources
- **Reserved Instances**: Opportunities to purchase Reserved Instances
- **Savings Plans**: Opportunities to purchase Savings Plans
- **Idle Resources**: Identification of unused or underutilized resources
- **Storage Optimization**: Recommendations for optimizing storage costs

### Recommendation Details

Each recommendation includes:

- **Title**: Brief description of the recommendation
- **Service**: The AWS service affected
- **Estimated Savings**: Potential monthly cost savings
- **Impact**: The impact level (High, Medium, Low)
- **Effort**: The implementation effort required (High, Medium, Low)
- **Description**: Detailed explanation of the recommendation
- **Implementation Steps**: Step-by-step instructions for implementing the recommendation

### Filtering and Sorting

You can filter and sort recommendations by:

- **Service**: Filter by AWS service
- **Savings**: Sort by estimated savings
- **Impact**: Filter by impact level
- **Effort**: Filter by implementation effort
- **Status**: Filter by implementation status

### Implementation Tracking

You can track the implementation status of recommendations:

1. Select a recommendation
2. Click "Start Implementation"
3. Update the status as you progress through the implementation steps
4. Mark the recommendation as "Implemented" when complete

## Tagging Compliance

The Tagging Compliance section helps you improve resource tagging for better cost allocation:

### Compliance Dashboard

The Compliance Dashboard shows your overall tagging compliance:

- **Compliance Score**: Percentage of resources with required tags
- **Compliance Trend**: Chart showing compliance score over time
- **Tag Coverage**: Percentage of resources with each required tag
- **Untagged Resources**: List of resources missing required tags

### Tag Management

The Tag Management view allows you to:

- **Define Required Tags**: Specify which tags are required for resources
- **Create Tag Policies**: Define rules for tag values
- **Export Tag Reports**: Generate reports of tagging compliance

### Tagging Recommendations

The system provides recommendations for improving tagging:

- **Missing Tags**: Resources missing required tags
- **Inconsistent Tags**: Resources with inconsistent tag values
- **Tag Automation**: Opportunities to automate tagging

## Cost Forecasting

The Forecasting section provides predictions of future AWS costs:

### Cost Forecast

The Cost Forecast view shows:

- **Monthly Forecast**: Predicted costs for upcoming months
- **Forecast Accuracy**: Historical accuracy of previous forecasts
- **Forecast Factors**: Factors influencing the forecast

### Budget Tracking

The Budget Tracking view allows you to:

- **Create Budgets**: Set budget targets for different dimensions
- **Track Budget**: Monitor actual spending against budgets
- **Budget Alerts**: Configure alerts for budget overruns

### What-If Analysis

The What-If Analysis tool allows you to:

- **Simulate Changes**: Model the cost impact of infrastructure changes
- **Compare Scenarios**: Compare different cost optimization scenarios
- **Optimize Budgets**: Identify the most effective ways to meet budget targets

## Executive Reports

The Reports section allows you to generate and download reports:

### Report Types

Available report types include:

- **Executive Summary**: High-level overview for executives
- **Cost Analysis**: Detailed cost analysis report
- **Optimization Opportunities**: Summary of cost-saving opportunities
- **Tagging Compliance**: Report on tagging compliance
- **Custom Reports**: Create custom reports with selected metrics

### Report Generation

To generate a report:

1. Select the report type
2. Configure report parameters (time range, filters, etc.)
3. Click "Generate Report"
4. Download the report in PDF, Excel, or CSV format

### Scheduled Reports

You can schedule reports to be generated automatically:

1. Configure the report parameters
2. Set the schedule (daily, weekly, monthly)
3. Specify email recipients
4. Enable or disable the schedule

## Settings and Configuration

The Settings section allows you to configure the system:

### AWS Accounts

Manage your connected AWS accounts:

- **Add Account**: Connect a new AWS account
- **Edit Account**: Modify AWS account settings
- **Remove Account**: Disconnect an AWS account

### Data Collection

Configure data collection settings:

- **Data Sources**: Enable or disable data sources
- **Refresh Frequency**: Set how often data is refreshed
- **Historical Data**: Configure historical data retention

### User Management

Manage user access to the system:

- **Add User**: Create a new user account
- **Edit User**: Modify user settings
- **Remove User**: Delete a user account
- **Roles**: Configure user roles and permissions

### Notifications

Configure notification settings:

- **Email Notifications**: Set up email notifications
- **Slack Integration**: Configure Slack notifications
- **Alert Thresholds**: Set thresholds for cost alerts

### API Access

Manage API access to the system:

- **API Keys**: Generate and manage API keys
- **API Documentation**: Access API documentation
- **API Limits**: View and configure API rate limits

## Troubleshooting

### Common Issues

#### Dashboard Not Loading

- Check your internet connection
- Clear your browser cache and cookies
- Try using a different browser
- Contact support if the issue persists

#### Data Not Updating

- Check the data refresh status in Settings > Data Collection
- Verify AWS account permissions
- Check for any error messages in the notification center
- Wait for the next scheduled data refresh

#### Recommendations Not Appearing

- Ensure you have connected your AWS accounts
- Check that data collection is enabled
- Wait for the system to analyze your data (may take 24-48 hours for new accounts)
- Verify that you have resources that could benefit from optimization

#### Export Not Working

- Check your browser's download settings
- Try a different export format
- Reduce the amount of data being exported
- Contact support if the issue persists

### Getting Help

If you encounter issues not covered in this guide:

- Click the "Help" button in the dashboard
- Check the knowledge base for solutions
- Contact support via email or chat
- Schedule a consultation with a FinOps specialist

## FAQ

### General Questions

**Q: How often is the data updated?**
A: By default, cost data is updated daily, and resource metrics are updated hourly. You can adjust these settings in the Data Collection configuration.

**Q: How far back does historical data go?**
A: The system retains up to 13 months of historical data for cost analysis and 3 months for detailed resource metrics.

**Q: Can I export data to other systems?**
A: Yes, you can export data via the UI or use the API to integrate with other systems.

### Cost Analysis

**Q: Why do the costs in FinOps Copilot differ from my AWS bill?**
A: There might be slight differences due to timing of data collection or the inclusion/exclusion of certain cost types. You can configure these settings in the Data Collection configuration.

**Q: Can I see costs for specific projects or teams?**
A: Yes, if you use tags to identify projects or teams, you can group costs by these tags in the Cost Breakdown view.

### Recommendations

**Q: How are savings estimates calculated?**
A: Savings estimates are calculated based on current costs, usage patterns, and AWS pricing models. The calculation methodology varies by recommendation type.

**Q: How long does it take to see the benefits of implementing recommendations?**
A: The time to realize savings varies by recommendation type. Some changes (like deleting idle resources) show immediate savings, while others (like Reserved Instance purchases) may take longer to show their full benefit.

**Q: Can the system automatically implement recommendations?**
A: Currently, the system provides implementation instructions but does not automatically implement changes. This is to ensure you have full control over your AWS environment.

### Security

**Q: What permissions does FinOps Copilot need?**
A: The system requires read-only access to cost and usage data, as well as resource metadata. It does not need write access to your AWS environment.

**Q: Is my data secure?**
A: Yes, all data is encrypted in transit and at rest. The system follows AWS security best practices and undergoes regular security assessments.

**Q: Who can see my cost data?**
A: Only users with appropriate permissions can access your cost data. You can configure user roles and permissions in the User Management settings.
