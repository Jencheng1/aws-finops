#!/usr/bin/env python3
"""
Test Budget Prediction functionality
"""

import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Testing Budget Prediction Components...")
print("=" * 50)

# Test 1: Get historical data
print("\n1. Testing historical data retrieval:")
ce_client = boto3.client('ce')

end_date = datetime.now().date()
start_date = end_date - timedelta(days=90)

try:
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )
    
    historical_costs = []
    for result in response['ResultsByTime']:
        historical_costs.append({
            'Date': pd.to_datetime(result['TimePeriod']['Start']),
            'Cost': float(result['Metrics']['UnblendedCost']['Amount'])
        })
    
    df_historical = pd.DataFrame(historical_costs)
    print(f"✅ Retrieved {len(df_historical)} days of historical data")
    
    # Filter out zero-cost days for better predictions
    df_with_costs = df_historical[df_historical['Cost'] > 0]
    if len(df_with_costs) == 0:
        print("   Note: No days with actual costs found (test/demo account)")
    else:
        print(f"   Days with costs: {len(df_with_costs)}")
        print(f"   Total cost in period: ${df_historical['Cost'].sum():,.2f}")
    
    # Test 2: Linear prediction
    print("\n2. Testing Linear prediction:")
    if len(df_historical) > 0:
        df_historical['Days'] = (df_historical['Date'] - df_historical['Date'].min()).dt.days
        costs = df_historical['Cost'].values
        days = df_historical['Days'].values
        
        # Linear regression
        z = np.polyfit(days, costs, 1)
        p = np.poly1d(z)
        
        # Predict next 30 days
        predictions = []
        for i in range(1, 31):
            predicted_cost = p(days[-1] + i)
            predictions.append(max(0, predicted_cost))
        
        print(f"✅ Linear prediction generated")
        print(f"   Current 30-day total: ${sum(costs[-30:]):,.2f}")
        print(f"   Predicted next 30 days: ${sum(predictions):,.2f}")
    
    # Test 3: Service-level predictions
    print("\n3. Testing service-level predictions:")
    service_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': (end_date - timedelta(days=30)).strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )
    
    service_costs = {}
    for result in service_response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            if service not in service_costs:
                service_costs[service] = []
            service_costs[service].append(cost)
    
    print(f"✅ Found {len(service_costs)} services with cost data")
    
    # Show top 3 services
    if service_costs:
        service_totals = [(s, sum(costs)) for s, costs in service_costs.items()]
        service_totals.sort(key=lambda x: x[1], reverse=True)
        
        print("\n   Top 3 services by cost:")
        for service, total in service_totals[:3]:
            print(f"   - {service}: ${total:,.2f}")
    
    # Test 4: Budget alert simulation
    print("\n4. Testing budget alert logic:")
    current_month_cost = sum(costs[-30:]) if len(costs) >= 30 else 0
    budget_threshold = current_month_cost * 1.1  # 10% over current
    predicted_month_cost = sum(predictions[:30]) if 'predictions' in locals() else 0
    
    if predicted_month_cost > budget_threshold:
        print(f"⚠️  Budget alert triggered!")
        print(f"   Predicted: ${predicted_month_cost:,.2f}")
        print(f"   Threshold: ${budget_threshold:,.2f}")
    else:
        print(f"✅ Within budget")
        print(f"   Predicted: ${predicted_month_cost:,.2f}")
        print(f"   Threshold: ${budget_threshold:,.2f}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 50)
print("Budget Prediction testing complete!")
print("\nThe Budget Prediction tab should provide:")
print("1. Multiple forecast types (Linear, Exponential, ML-Based)")
print("2. Configurable prediction period (7-90 days)")
print("3. Service-level predictions")
print("4. Budget alerts and recommendations")
print("5. Visual forecast charts")