#!/usr/bin/env python3
"""
Check what date range has actual cost data
"""

import boto3
from datetime import datetime, timedelta

ce_client = boto3.client('ce')

# Check last 90 days
end_date = datetime.now().date()
start_date = end_date - timedelta(days=90)

print(f"Checking cost data from {start_date} to {end_date}")
print("-" * 50)

response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date.strftime('%Y-%m-%d'),
        'End': end_date.strftime('%Y-%m-%d')
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost']
)

# Find dates with actual costs
dates_with_costs = []
total_cost = 0.0

for result in response['ResultsByTime']:
    date = result['TimePeriod']['Start']
    cost = float(result['Metrics']['UnblendedCost']['Amount'])
    
    if cost > 0:
        dates_with_costs.append((date, cost))
        total_cost += cost

if dates_with_costs:
    print(f"Found {len(dates_with_costs)} days with costs")
    print(f"Date range: {dates_with_costs[0][0]} to {dates_with_costs[-1][0]}")
    print(f"Total cost in period: ${total_cost:,.2f}")
    
    # Show last 5 days with costs
    print("\nLast 5 days with costs:")
    for date, cost in dates_with_costs[-5:]:
        print(f"  {date}: ${cost:,.2f}")
else:
    print("No cost data found in the last 90 days")
    
# Check if this is a test/demo account
print("\nAccount Status:")
print(f"Account ID: {boto3.client('sts').get_caller_identity()['Account']}")
print("Note: This might be a test account with no real usage")