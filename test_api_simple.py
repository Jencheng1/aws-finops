#!/usr/bin/env python3
"""
Simple API test to verify core functionality
"""

import boto3
import sys
from datetime import datetime, timedelta
from budget_prediction_agent import BudgetPredictionAgent

def test_apis():
    """Test core APIs"""
    print("=== Testing Core AWS APIs ===")
    
    tests_passed = 0
    tests_total = 5
    
    # Test 1: Cost Explorer
    try:
        ce = boto3.client('ce')
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        total = sum(float(r['Total']['UnblendedCost']['Amount']) for r in response['ResultsByTime'])
        print(f"✓ Cost Explorer API: Last 7 days = ${total:.2f}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Cost Explorer API failed: {e}")
    
    # Test 2: EC2
    try:
        ec2 = boto3.client('ec2')
        instances = ec2.describe_instances()
        count = sum(len(r['Instances']) for r in instances['Reservations'])
        print(f"✓ EC2 API: Found {count} instances")
        tests_passed += 1
    except Exception as e:
        print(f"✗ EC2 API failed: {e}")
    
    # Test 3: ML Prediction
    try:
        agent = BudgetPredictionAgent()
        df = agent.fetch_historical_costs(months=1)
        agent.train_prediction_models(df)  # Train models first
        pred = agent.predict_budget(days_ahead=7)
        total = pred['summary']['total_predicted_cost']
        print(f"✓ ML Prediction: 7-day forecast = ${total:.2f}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ ML Prediction failed: {e}")
    
    # Test 4: DynamoDB
    try:
        db = boto3.resource('dynamodb')
        table = db.Table('FinOpsFeedback')
        table.table_status
        print("✓ DynamoDB: Feedback table accessible")
        tests_passed += 1
    except Exception as e:
        print(f"✗ DynamoDB failed: {e}")
    
    # Test 5: Trusted Advisor
    try:
        agent = BudgetPredictionAgent()
        ta_data = agent.get_trusted_advisor_cost_data()
        savings = ta_data['total_monthly_savings']
        print(f"✓ Trusted Advisor: ${savings:.2f} monthly savings potential")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Trusted Advisor failed: {e}")
    
    print(f"\n=== API Test Results: {tests_passed}/{tests_total} passed ===")
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_apis()
    sys.exit(0 if success else 1)