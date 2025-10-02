#!/usr/bin/env python3
"""
Demonstrate new FinOps features with real AWS data
"""

from tag_compliance_agent import TagComplianceAgent
from finops_report_generator import FinOpsReportGenerator
import boto3
from datetime import datetime, timedelta

print('🔍 Demonstrating New Features with Real AWS Data\n')

# 1. Tag Compliance Check
print('=== TAG COMPLIANCE CHECK ===')
agent = TagComplianceAgent()
response, data = agent.perform_compliance_scan()
print(f'Compliance Rate: {data.get("compliance_rate", 0):.1f}%')
print(f'Total Resources: {data.get("total_resources", 0)}')
print(f'Non-compliant: {data.get("non_compliant_count", 0)}')

if 'missing_tags_summary' in data:
    print('\nMissing Tags:')
    for tag, count in data['missing_tags_summary'].items():
        if count > 0:
            print(f'  - {tag}: {count} resources')

# 2. Report Generation Sample
print('\n=== REPORT GENERATION ===')
clients = {
    'ce': boto3.client('ce'),
    'ec2': boto3.client('ec2'),
    'rds': boto3.client('rds'),
    's3': boto3.client('s3'),
    'lambda': boto3.client('lambda'),
    'cloudwatch': boto3.client('cloudwatch'),
    'organizations': boto3.client('organizations'),
    'sts': boto3.client('sts')
}

report_gen = FinOpsReportGenerator(clients)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

# Get cost analysis
costs = report_gen._analyze_costs(start_date, end_date)
print(f'7-Day Cost Analysis:')
print(f'  Total Cost: ${costs.get("total_cost", 0):,.2f}')
print(f'  Daily Average: ${costs.get("average_daily_cost", 0):,.2f}')
print(f'  Services with Costs: {len(costs.get("service_costs", {}))}')

# Get optimization recommendations
print('\n=== OPTIMIZATION RECOMMENDATIONS ===')
recommendations = report_gen._generate_optimization_recommendations()
print(f'Total Recommendations: {len(recommendations.get("recommendations", []))}')
print(f'Annual Savings Potential: ${recommendations.get("total_annual_savings", 0):,.2f}')

if recommendations['recommendations']:
    print('\nTop Recommendations:')
    for i, rec in enumerate(recommendations['recommendations'][:3], 1):
        print(f'{i}. {rec["recommendation"]}')
        print(f'   Monthly Savings: ${rec.get("monthly_savings", 0):,.2f}')

print('\n✅ All features working with real AWS data!')