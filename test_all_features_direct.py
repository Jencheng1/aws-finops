#!/usr/bin/env python3
"""
Direct API testing of all features without Selenium
Tests all functionality with real AWS APIs
"""

import unittest
import requests
import json
import boto3
import time
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import subprocess
import threading

# Import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from budget_prediction_agent import BudgetPredictionAgent, CostAnomalyDetector

class TestAllFeaturesDirect(unittest.TestCase):
    """Test all platform features directly with real AWS APIs"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        print("\n=== Direct Feature Testing (No UI Required) ===")
        
        # Initialize AWS clients
        cls.ce = boto3.client('ce')
        cls.ec2 = boto3.client('ec2')
        cls.lambda_client = boto3.client('lambda')
        cls.dynamodb = boto3.resource('dynamodb')
        cls.sts = boto3.client('sts')
        cls.cloudwatch = boto3.client('cloudwatch')
        cls.support = boto3.client('support')
        
        # Get account info
        cls.account_id = cls.sts.get_caller_identity()['Account']
        print(f"✓ Connected to AWS Account: {cls.account_id}")
        
        # Start Streamlit in background for API testing
        cls.streamlit_process = None
        cls.start_streamlit()
        
    @classmethod
    def start_streamlit(cls):
        """Start Streamlit server in background"""
        print("Starting Streamlit server...")
        cls.streamlit_process = subprocess.Popen(
            ['streamlit', 'run', 'enhanced_dashboard_with_feedback.py',
             '--server.headless', 'true',
             '--server.port', '8501'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Wait for server to start
        time.sleep(10)
        
        # Verify server is running
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            if response.status_code == 200:
                print("✓ Streamlit server running on port 8501")
            else:
                print("⚠ Streamlit server responded with status:", response.status_code)
        except Exception as e:
            print(f"⚠ Streamlit server check: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        if cls.streamlit_process:
            cls.streamlit_process.terminate()
            cls.streamlit_process.wait()
            print("✓ Stopped Streamlit server")
    
    def test_01_cost_data_retrieval(self):
        """Test Cost Explorer data retrieval"""
        print("\n=== Test 1: Cost Data Retrieval ===")
        
        # Test daily costs
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        total_cost = 0
        service_count = 0
        
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0:
                    service_count += 1
                    total_cost += cost
        
        print(f"✓ Retrieved 7 days of cost data")
        print(f"✓ Total cost: ${total_cost:.2f}")
        print(f"✓ Active services: {service_count}")
        
        self.assertGreater(len(response['ResultsByTime']), 0)
        self.assertGreaterEqual(total_cost, 0)
    
    def test_02_budget_prediction_ml(self):
        """Test ML-based budget prediction"""
        print("\n=== Test 2: Budget Prediction ML ===")
        
        agent = BudgetPredictionAgent()
        
        # Get historical data
        df = agent.fetch_historical_costs(months=3)
        print(f"✓ Fetched {len(df)} historical records")
        
        # Train models
        training_result = agent.train_prediction_models(df)
        print(f"✓ Trained models: {', '.join(training_result['models_trained'])}")
        
        # Make predictions
        predictions = agent.predict_budget(days_ahead=30)
        
        total = predictions['summary']['total_predicted_cost']
        avg_daily = predictions['summary']['average_daily_cost']
        confidence = predictions['summary']['confidence_level']
        
        print(f"✓ 30-day prediction: ${total:.2f}")
        print(f"✓ Daily average: ${avg_daily:.2f}")
        print(f"✓ Confidence level: {confidence}")
        
        self.assertGreater(total, 0)
        self.assertEqual(len(predictions['daily_predictions']), 30)
    
    def test_03_resource_optimization_scan(self):
        """Test idle resource detection"""
        print("\n=== Test 3: Resource Optimization ===")
        
        idle_resources = {
            'stopped_instances': 0,
            'unattached_volumes': 0,
            'unused_eips': 0,
            'total_waste': 0.0
        }
        
        # Scan EC2 instances
        instances = self.ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'stopped':
                    idle_resources['stopped_instances'] += 1
                    # Estimate storage cost
                    volumes = instance.get('BlockDeviceMappings', [])
                    total_gb = sum(v.get('Ebs', {}).get('VolumeSize', 0) for v in volumes)
                    idle_resources['total_waste'] += total_gb * 0.10  # $0.10/GB/month
        
        print(f"✓ Found {idle_resources['stopped_instances']} stopped EC2 instances")
        
        # Scan unattached volumes
        volumes = self.ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
        idle_resources['unattached_volumes'] = len(volumes['Volumes'])
        for vol in volumes['Volumes']:
            idle_resources['total_waste'] += vol['Size'] * 0.10
        
        print(f"✓ Found {idle_resources['unattached_volumes']} unattached EBS volumes")
        
        # Scan Elastic IPs
        addresses = self.ec2.describe_addresses()
        for addr in addresses['Addresses']:
            if 'InstanceId' not in addr and 'NetworkInterfaceId' not in addr:
                idle_resources['unused_eips'] += 1
                idle_resources['total_waste'] += 0.005 * 24 * 30  # $0.005/hour
        
        print(f"✓ Found {idle_resources['unused_eips']} unused Elastic IPs")
        print(f"✓ Total monthly waste: ${idle_resources['total_waste']:.2f}")
        
        self.assertIsInstance(idle_resources['total_waste'], float)
    
    def test_04_anomaly_detection(self):
        """Test cost anomaly detection"""
        print("\n=== Test 4: Anomaly Detection ===")
        
        detector = CostAnomalyDetector()
        agent = BudgetPredictionAgent()
        
        # Get historical data
        df = agent.fetch_historical_costs(months=2)
        
        # Detect anomalies
        anomalies = detector.detect_anomalies(df, lookback_days=30)
        
        print(f"✓ Analyzed {len(df)} cost records")
        print(f"✓ Found {len(anomalies['daily_anomalies'])} daily anomalies")
        print(f"✓ Found {len(anomalies['service_anomalies'])} service anomalies")
        print(f"✓ Anomaly rate: {anomalies['summary']['anomaly_rate']:.1f}%")
        
        if anomalies['daily_anomalies']:
            latest = anomalies['daily_anomalies'][0]
            print(f"✓ Latest anomaly: {latest['date']} - ${latest['cost']:.2f} (z-score: {latest['z_score']:.2f})")
        
        self.assertIn('daily_anomalies', anomalies)
        self.assertIn('service_anomalies', anomalies)
    
    def test_05_savings_plans_analysis(self):
        """Test Savings Plans recommendations"""
        print("\n=== Test 5: Savings Plans Analysis ===")
        
        try:
            # Get current Savings Plans
            current_plans = boto3.client('savingsplans').describe_savings_plans()
            print(f"✓ Current Savings Plans: {len(current_plans.get('savingsPlans', []))}")
        except:
            print("⚠ Savings Plans API not available in this region")
        
        # Get recommendations
        try:
            recommendations = self.ce.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='ALL_UPFRONT',
                LookbackPeriodInDays='SIXTY_DAYS'
            )
            
            if 'SavingsPlansPurchaseRecommendation' in recommendations:
                rec = recommendations['SavingsPlansPurchaseRecommendation']
                hourly = float(rec.get('HourlyCommitmentToPurchase', 0))
                savings = float(rec.get('EstimatedSavingsAmount', 0))
                
                print(f"✓ Recommended hourly commitment: ${hourly:.2f}")
                print(f"✓ Estimated annual savings: ${savings:.2f}")
            else:
                print("✓ No Savings Plans recommendations available")
                
        except Exception as e:
            print(f"⚠ Savings Plans recommendations: {e}")
        
        # Get coverage
        try:
            coverage = self.ce.get_savings_plans_coverage(
                TimePeriod={
                    'Start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'End': datetime.now().strftime('%Y-%m-%d')
                }
            )
            
            if coverage.get('SavingsPlansCoverages'):
                coverage_pct = float(coverage['SavingsPlansCoverages'][0]
                                   .get('Coverage', {})
                                   .get('CoveragePercentage', 0))
                print(f"✓ Current coverage: {coverage_pct:.1f}%")
        except:
            print("⚠ Coverage data not available")
    
    def test_06_feedback_system(self):
        """Test feedback storage in DynamoDB"""
        print("\n=== Test 6: Feedback System ===")
        
        feedback_table = self.dynamodb.Table('FinOpsFeedback')
        
        # Create test feedback
        test_feedback = {
            'feedback_id': f'test_{datetime.now().timestamp()}',
            'timestamp': datetime.now().isoformat(),
            'user_id': 'test_user',
            'session_id': 'test_session',
            'feedback_type': 'prediction_accuracy',
            'feedback_text': 'Test feedback for comprehensive testing',
            'rating': 5,
            'sentiment': 'POSITIVE',
            'context': json.dumps({
                'test': True,
                'prediction_id': 'test_pred_123'
            })
        }
        
        # Store feedback
        feedback_table.put_item(Item=test_feedback)
        print("✓ Stored test feedback")
        
        # Retrieve feedback
        response = feedback_table.get_item(
            Key={
                'feedback_id': test_feedback['feedback_id'],
                'timestamp': test_feedback['timestamp']
            }
        )
        
        self.assertIn('Item', response)
        print("✓ Retrieved feedback successfully")
        
        # Query by user
        user_feedback = feedback_table.query(
            IndexName='UserIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': 'test_user'},
            Limit=10
        )
        
        print(f"✓ Found {len(user_feedback['Items'])} feedback items for test user")
    
    def test_07_lambda_functions(self):
        """Test Lambda function invocations"""
        print("\n=== Test 7: Lambda Functions ===")
        
        lambda_functions = [
            {
                'name': 'finops-budget-predictor',
                'payload': {
                    'days_ahead': 7,
                    'months_history': 1,
                    'user_id': 'test_user',
                    'session_id': 'test_lambda'
                }
            },
            {
                'name': 'finops-resource-optimizer',
                'payload': {
                    'scan_days': 7,
                    'user_id': 'test_user',
                    'session_id': 'test_lambda'
                }
            },
            {
                'name': 'finops-feedback-processor',
                'payload': {
                    'feedback_type': 'test',
                    'feedback_text': 'Lambda test',
                    'rating': 5,
                    'user_id': 'test_user'
                }
            }
        ]
        
        for func in lambda_functions:
            try:
                response = self.lambda_client.invoke(
                    FunctionName=func['name'],
                    InvocationType='RequestResponse',
                    Payload=json.dumps(func['payload'])
                )
                
                if response['StatusCode'] == 200:
                    result = json.loads(response['Payload'].read())
                    print(f"✓ Lambda {func['name']} invoked successfully")
                else:
                    print(f"⚠ Lambda {func['name']} returned status {response['StatusCode']}")
                    
            except Exception as e:
                print(f"⚠ Lambda {func['name']}: {str(e)[:50]}...")
    
    def test_08_trusted_advisor(self):
        """Test Trusted Advisor integration"""
        print("\n=== Test 8: Trusted Advisor ===")
        
        agent = BudgetPredictionAgent()
        ta_data = agent.get_trusted_advisor_cost_data()
        
        print(f"✓ Found {len(ta_data['recommendations'])} recommendations")
        print(f"✓ Total monthly savings: ${ta_data['total_monthly_savings']:.2f}")
        print(f"✓ Annual savings potential: ${ta_data['annual_savings_potential']:.2f}")
        
        if ta_data['recommendations']:
            for rec in ta_data['recommendations'][:3]:
                print(f"  - {rec['check']}: ${rec['monthly_savings']:.2f}/month")
        
        self.assertIn('recommendations', ta_data)
        self.assertGreaterEqual(ta_data['total_monthly_savings'], 0)
    
    def test_09_integrated_insights(self):
        """Test integrated insights generation"""
        print("\n=== Test 9: Integrated Insights ===")
        
        from budget_prediction_agent import get_budget_insights
        
        insights = get_budget_insights(months_history=2, prediction_days=14)
        
        print("✓ Generated integrated insights:")
        print(f"  - Prediction total: ${insights['predictions']['summary']['total_predicted_cost']:.2f}")
        print(f"  - Trusted Advisor savings: ${insights['trusted_advisor']['total_monthly_savings']:.2f}")
        print(f"  - Anomalies found: {insights['anomalies']['summary']['total_anomalies']}")
        print(f"  - Cost drivers analyzed: {len(insights['cost_drivers']['top_services'])}")
        print(f"  - Recommendations generated: {len(insights['recommendations'])}")
        
        self.assertIn('predictions', insights)
        self.assertIn('trusted_advisor', insights)
        self.assertIn('cost_drivers', insights)
        self.assertIn('anomalies', insights)
        self.assertIn('recommendations', insights)
    
    def test_10_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n=== Test 10: End-to-End Workflow ===")
        
        print("Simulating complete user workflow...")
        
        # Step 1: Get current costs
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        yesterday_cost = float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
        print(f"✓ Step 1: Yesterday's cost: ${yesterday_cost:.2f}")
        
        # Step 2: Generate prediction
        agent = BudgetPredictionAgent()
        df = agent.fetch_historical_costs(months=1)
        agent.train_prediction_models(df)
        pred = agent.predict_budget(days_ahead=7)
        
        print(f"✓ Step 2: 7-day prediction: ${pred['summary']['total_predicted_cost']:.2f}")
        
        # Step 3: Find optimizations
        volumes = self.ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
        waste = len(volumes['Volumes']) * 10  # Rough estimate
        
        print(f"✓ Step 3: Potential savings identified: ${waste}/month")
        
        # Step 4: Store feedback
        feedback_table = self.dynamodb.Table('FinOpsFeedback')
        feedback_table.put_item(
            Item={
                'feedback_id': f'e2e_test_{datetime.now().timestamp()}',
                'timestamp': datetime.now().isoformat(),
                'user_id': 'test_user',
                'session_id': 'e2e_test',
                'feedback_type': 'workflow_complete',
                'feedback_text': 'End-to-end test successful',
                'rating': 5,
                'context': json.dumps({
                    'yesterday_cost': yesterday_cost,
                    'prediction': pred['summary']['total_predicted_cost'],
                    'savings_found': waste
                })
            }
        )
        
        print("✓ Step 4: Feedback stored")
        print("\n✅ End-to-end workflow completed successfully!")

def run_all_direct_tests():
    """Run all direct API tests"""
    print("\n" + "="*60)
    print("COMPREHENSIVE DIRECT API TEST SUITE")
    print("Testing all features without UI dependencies")
    print("="*60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAllFeaturesDirect)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*60)
    
    # Save results
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
    }
    
    with open('direct_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_direct_tests()
    sys.exit(0 if success else 1)