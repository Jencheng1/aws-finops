#!/usr/bin/env python3
"""
Test the fixed cost data retrieval
"""

import boto3
from datetime import datetime, timedelta

# Test the fixed cost retrieval logic
ce_client = boto3.client('ce')

# Get current month costs with DAILY granularity
now = datetime.now()
start_date = datetime(now.year, now.month, 1).date()
end_date = now.date() + timedelta(days=1)

print(f"Testing cost retrieval from {start_date} to {end_date}")
print("-" * 50)

# Use DAILY granularity and aggregate
response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date.strftime('%Y-%m-%d'),
        'End': end_date.strftime('%Y-%m-%d')
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
)

if response['ResultsByTime']:
    # Aggregate costs by service across all days
    service_costs = {}
    total_cost = 0.0
    
    for result in response['ResultsByTime']:
        date = result['TimePeriod']['Start']
        daily_total = 0
        
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            
            if service not in service_costs:
                service_costs[service] = 0.0
            service_costs[service] += cost
            daily_total += cost
        
        if daily_total > 0:
            print(f"{date}: ${daily_total:,.2f}")
        total_cost += daily_total
    
    print("-" * 50)
    print(f"\nMonth-to-Date Total: ${total_cost:,.2f}")
    print(f"Days in Month: {(end_date - start_date).days}")
    print(f"Daily Average: ${total_cost / max(1, (end_date - start_date).days):.2f}")
    print(f"Projected Monthly: ${(total_cost / max(1, (end_date - start_date).days)) * 30:.2f}")
    
    # Get top 5 services
    services = list(service_costs.items())
    services.sort(key=lambda x: x[1], reverse=True)
    top_services = services[:5]
    
    print("\nTop 5 Services by Cost:")
    for service, cost in top_services:
        pct = (cost / total_cost * 100) if total_cost > 0 else 0
        print(f"  • {service}: ${cost:.2f} ({pct:.1f}%)")
else:
    print("No cost data available")