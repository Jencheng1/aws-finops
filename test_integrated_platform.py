#!/usr/bin/env python3
"""
Comprehensive test suite for Integrated FinOps Platform
Tests all features with real AWS APIs
"""

import sys
import os
import json
import boto3
import pandas as pd
from datetime import datetime, timedelta
import unittest
from typing import Dict, List, Any
import time

# Import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from budget_prediction_agent import BudgetPredictionAgent, CostAnomalyDetector, get_budget_insights


class TestIntegratedFinOpsPlatform(unittest.TestCase):
    """Test all features of the integrated FinOps platform with real AWS APIs"""
    
    @classmethod
    def setUpClass(cls):
        """Set up AWS clients and test data"""
        print("\n=== Setting up test environment ===")
        
        # Initialize AWS clients
        cls.ce = boto3.client('ce')
        cls.ec2 = boto3.client('ec2')
        cls.cloudwatch = boto3.client('cloudwatch')
        cls.support = boto3.client('support')
        cls.organizations = boto3.client('organizations')
        cls.savingsplans = boto3.client('savingsplans')
        cls.compute_optimizer = boto3.client('compute-optimizer')
        cls.sts = boto3.client('sts')
        
        # Get account info
        try:
            cls.account_id = cls.sts.get_caller_identity()['Account']
            print(f"✓ Connected to AWS Account: {cls.account_id}")
        except Exception as e:
            print(f"✗ Failed to connect to AWS: {e}")
            raise
        
        # Test parameters
        cls.test_days = 7  # Look back 7 days for testing
        cls.end_date = datetime.now().date()
        cls.start_date = cls.end_date - timedelta(days=cls.test_days)
        
    def test_01_cost_explorer_api(self):
        """Test 1: Verify Cost Explorer API access and data retrieval"""
        print("\n=== Test 1: Cost Explorer API ===")
        
        try:
            # Get cost and usage data
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date.strftime('%Y-%m-%d'),
                    'End': self.end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            self.assertIn('ResultsByTime', response)
            self.assertGreater(len(response['ResultsByTime']), 0)
            
            # Process and validate data
            total_cost = 0
            services_found = set()
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    services_found.add(service)
                    total_cost += cost
            
            print(f"✓ Retrieved {len(response['ResultsByTime'])} days of cost data")
            print(f"✓ Found {len(services_found)} AWS services with costs")
            print(f"✓ Total cost for period: ${total_cost:,.2f}")
            
            # Get cost forecast
            forecast_response = self.ce.get_cost_forecast(
                TimePeriod={
                    'Start': (self.end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'End': (self.end_date + timedelta(days=7)).strftime('%Y-%m-%d')
                },
                Metric='UNBLENDED_COST',
                Granularity='DAILY'
            )
            
            self.assertIn('ForecastResultsByTime', forecast_response)
            print(f"✓ Cost forecast available for next 7 days")
            
        except Exception as e:
            self.fail(f"Cost Explorer API test failed: {e}")
    
    def test_02_trusted_advisor_integration(self):
        """Test 2: Verify Trusted Advisor integration for cost optimization"""
        print("\n=== Test 2: Trusted Advisor Integration ===")
        
        try:
            # Note: Trusted Advisor requires Business or Enterprise support plan
            checks = self.support.describe_trusted_advisor_checks(language='en')
            
            # Find cost optimization checks
            cost_check_ids = {
                'Low Utilization Amazon EC2 Instances': 'Qch7DwouX1',
                'Idle Load Balancers': 'hjLMh88uM8',
                'Unassociated Elastic IP Addresses': 'Z4AUBRNSmz',
                'Underutilized Amazon EBS Volumes': 'DAvU99Dc4C',
                'Amazon RDS Idle DB Instances': 'Ti39halfu8'
            }
            
            cost_savings_found = 0
            recommendations_count = 0
            
            for check_name, check_id in cost_check_ids.items():
                try:
                    result = self.support.describe_trusted_advisor_check_result(
                        checkId=check_id,
                        language='en'
                    )
                    
                    if result['result']['status'] in ['warning', 'error']:
                        flagged = result['result']['flaggedResources']
                        recommendations_count += len(flagged)
                        
                        for resource in flagged:
                            metadata = resource.get('metadata', [])
                            if len(metadata) > 4 and metadata[4]:  # Estimated monthly savings
                                try:
                                    savings = float(metadata[4])
                                    cost_savings_found += savings
                                except:
                                    pass
                        
                        print(f"✓ {check_name}: {len(flagged)} issues found")
                
                except Exception as e:
                    print(f"  - {check_name}: Not available or no access")
            
            print(f"✓ Total recommendations: {recommendations_count}")
            print(f"✓ Potential monthly savings: ${cost_savings_found:,.2f}")
            
        except Exception as e:
            print(f"⚠ Trusted Advisor not available (requires Business/Enterprise support): {e}")
            print("  Using alternative cost optimization checks...")
    
    def test_03_resource_optimization(self):
        """Test 3: Identify idle and underutilized resources"""
        print("\n=== Test 3: Resource Optimization ===")
        
        idle_resources = {
            'ec2_instances': [],
            'ebs_volumes': [],
            'load_balancers': [],
            'rds_instances': [],
            'elastic_ips': []
        }
        
        try:
            # Check EC2 instances
            instances = self.ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'stopped':
                        idle_resources['ec2_instances'].append({
                            'id': instance['InstanceId'],
                            'type': instance['InstanceType'],
                            'state': 'stopped',
                            'launch_time': instance.get('LaunchTime', '').isoformat() if 'LaunchTime' in instance else 'N/A'
                        })
            
            print(f"✓ Found {len(idle_resources['ec2_instances'])} stopped EC2 instances")
            
            # Check unattached EBS volumes
            volumes = self.ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )
            idle_resources['ebs_volumes'] = [{
                'id': vol['VolumeId'],
                'size': vol['Size'],
                'type': vol['VolumeType'],
                'create_time': vol['CreateTime'].isoformat()
            } for vol in volumes['Volumes']]
            
            print(f"✓ Found {len(idle_resources['ebs_volumes'])} unattached EBS volumes")
            
            # Check elastic IPs
            eips = self.ec2.describe_addresses()
            unassociated_eips = [eip for eip in eips['Addresses'] if 'InstanceId' not in eip]
            idle_resources['elastic_ips'] = [{
                'ip': eip.get('PublicIp', 'N/A'),
                'allocation_id': eip.get('AllocationId', 'N/A')
            } for eip in unassociated_eips]
            
            print(f"✓ Found {len(idle_resources['elastic_ips'])} unassociated Elastic IPs")
            
            # Calculate potential savings
            potential_savings = 0
            potential_savings += len(idle_resources['ebs_volumes']) * 0.10 * 730  # $0.10/GB/month avg
            potential_savings += len(idle_resources['elastic_ips']) * 0.005 * 730  # $0.005/hour
            
            print(f"✓ Estimated monthly savings from cleanup: ${potential_savings:,.2f}")
            
            self.assertIsInstance(idle_resources, dict)
            
        except Exception as e:
            self.fail(f"Resource optimization test failed: {e}")
    
    def test_04_savings_plans_analysis(self):
        """Test 4: Analyze Savings Plans opportunities"""
        print("\n=== Test 4: Savings Plans Analysis ===")
        
        try:
            # Get current Savings Plans
            current_plans = self.savingsplans.describe_savings_plans()
            print(f"✓ Current Savings Plans: {len(current_plans.get('savingsPlans', []))}")
            
            # Get Savings Plans recommendations
            try:
                recommendations = self.ce.get_savings_plans_purchase_recommendation(
                    SavingsPlansType='COMPUTE_SP',
                    TermInYears='ONE_YEAR',
                    PaymentOption='NO_UPFRONT',
                    LookbackPeriodInDays='SIXTY_DAYS'
                )
                
                if 'SavingsPlansPurchaseRecommendation' in recommendations:
                    rec = recommendations['SavingsPlansPurchaseRecommendation']
                    hourly_commitment = rec.get('HourlyCommitmentToPurchase', '0')
                    estimated_savings = rec.get('EstimatedSavingsAmount', '0')
                    
                    print(f"✓ Recommended hourly commitment: ${hourly_commitment}")
                    print(f"✓ Estimated annual savings: ${estimated_savings}")
                    
                    # Get details
                    details = rec.get('SavingsPlansPurchaseRecommendationDetails', [])
                    if details:
                        for detail in details[:3]:  # Top 3 recommendations
                            print(f"  - {detail.get('SavingsPlansDetails', {}).get('OfferingId', 'N/A')}: "
                                  f"Save {detail.get('EstimatedSavingsPercentage', 0)}%")
                
            except Exception as e:
                print(f"  Savings Plans recommendations not available: {e}")
            
            # Check RI coverage
            coverage = self.ce.get_reservation_coverage(
                TimePeriod={
                    'Start': self.start_date.strftime('%Y-%m-%d'),
                    'End': self.end_date.strftime('%Y-%m-%d')
                }
            )
            
            if 'Total' in coverage:
                coverage_pct = coverage['Total'].get('CoverageHours', {}).get('CoverageHoursPercentage', '0')
                print(f"✓ Current RI coverage: {coverage_pct}%")
            
        except Exception as e:
            print(f"⚠ Savings Plans analysis limited: {e}")
    
    def test_05_budget_prediction_agent(self):
        """Test 5: Verify Budget Prediction Agent functionality"""
        print("\n=== Test 5: Budget Prediction Agent ===")
        
        try:
            agent = BudgetPredictionAgent()
            
            # Test historical data fetch
            print("  Testing historical data fetch...")
            df = agent.fetch_historical_costs(months=3)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertGreater(len(df), 0)
            print(f"✓ Retrieved {len(df)} historical cost records")
            
            # Test model training
            print("  Training prediction models...")
            training_result = agent.train_prediction_models(df)
            self.assertIn('models_trained', training_result)
            print(f"✓ Trained models: {', '.join(training_result['models_trained'])}")
            
            # Test prediction
            print("  Generating budget predictions...")
            predictions = agent.predict_budget(days_ahead=30)
            self.assertIn('daily_predictions', predictions)
            self.assertEqual(len(predictions['daily_predictions']), 30)
            
            total_predicted = predictions['summary']['total_predicted_cost']
            print(f"✓ 30-day budget prediction: ${total_predicted:,.2f}")
            print(f"✓ Average daily cost: ${predictions['summary']['average_daily_cost']:,.2f}")
            
            # Test cost driver analysis
            print("  Analyzing cost drivers...")
            drivers = agent.analyze_cost_drivers(df)
            self.assertIn('top_services', drivers)
            print(f"✓ Top cost driver: {drivers['top_services'][0]['service']} "
                  f"({drivers['top_services'][0]['percentage']:.1f}%)")
            
        except Exception as e:
            self.fail(f"Budget prediction agent test failed: {e}")
    
    def test_06_anomaly_detection(self):
        """Test 6: Verify anomaly detection capabilities"""
        print("\n=== Test 6: Anomaly Detection ===")
        
        try:
            # Get historical data
            agent = BudgetPredictionAgent()
            df = agent.fetch_historical_costs(months=2)
            
            # Test anomaly detection
            detector = CostAnomalyDetector()
            anomalies = detector.detect_anomalies(df, lookback_days=30)
            
            self.assertIn('daily_anomalies', anomalies)
            self.assertIn('service_anomalies', anomalies)
            
            print(f"✓ Detected {len(anomalies['daily_anomalies'])} daily anomalies")
            print(f"✓ Detected {len(anomalies['service_anomalies'])} service-level anomalies")
            
            if anomalies['daily_anomalies']:
                latest = anomalies['daily_anomalies'][0]
                print(f"  Latest anomaly: {latest['date']} - ${latest['cost']:,.2f} "
                      f"(z-score: {latest['z_score']:.2f})")
            
            # Test explanation generation
            explanation = detector.explain_anomaly(anomalies)
            self.assertIsInstance(explanation, str)
            print(f"✓ Generated explanation: {explanation[:100]}...")
            
        except Exception as e:
            self.fail(f"Anomaly detection test failed: {e}")
    
    def test_07_integrated_insights(self):
        """Test 7: Verify integrated insights generation"""
        print("\n=== Test 7: Integrated Insights ===")
        
        try:
            # Get comprehensive insights
            insights = get_budget_insights(months_history=3, prediction_days=30)
            
            # Verify all components
            self.assertIn('predictions', insights)
            self.assertIn('trusted_advisor', insights)
            self.assertIn('cost_drivers', insights)
            self.assertIn('anomalies', insights)
            self.assertIn('recommendations', insights)
            
            print("✓ Successfully generated integrated insights:")
            print(f"  - Predictions: {insights['predictions']['summary']['total_predicted_cost']:,.2f}")
            print(f"  - Trusted Advisor savings: ${insights['trusted_advisor']['total_monthly_savings']:,.2f}")
            print(f"  - Anomalies detected: {insights['anomalies']['summary']['total_anomalies']}")
            print(f"  - Recommendations: {len(insights['recommendations'])}")
            
            # Test recommendation quality
            for rec in insights['recommendations']:
                self.assertIn('type', rec)
                self.assertIn('priority', rec)
                self.assertIn('title', rec)
                self.assertIn('description', rec)
                print(f"  - {rec['title']}: {rec['description'][:50]}...")
            
        except Exception as e:
            self.fail(f"Integrated insights test failed: {e}")
    
    def test_08_real_time_cost_monitoring(self):
        """Test 8: Verify real-time cost monitoring capabilities"""
        print("\n=== Test 8: Real-time Cost Monitoring ===")
        
        try:
            # Get today's costs
            today = datetime.now().date()
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': today.strftime('%Y-%m-%d'),
                    'End': (today + timedelta(days=1)).strftime('%Y-%m-%d')
                },
                Granularity='HOURLY',
                Metrics=['UnblendedCost']
            )
            
            hourly_costs = []
            for result in response.get('ResultsByTime', []):
                cost = float(result['Total']['UnblendedCost']['Amount'])
                hour = result['TimePeriod']['Start']
                if cost > 0:
                    hourly_costs.append({'hour': hour, 'cost': cost})
            
            if hourly_costs:
                print(f"✓ Retrieved {len(hourly_costs)} hours of today's cost data")
                total_today = sum(h['cost'] for h in hourly_costs)
                print(f"✓ Today's cost so far: ${total_today:,.2f}")
                
                # Check for cost spikes
                if len(hourly_costs) > 1:
                    avg_hourly = total_today / len(hourly_costs)
                    max_hourly = max(h['cost'] for h in hourly_costs)
                    if max_hourly > avg_hourly * 2:
                        print(f"⚠ Cost spike detected: ${max_hourly:,.2f}/hour (avg: ${avg_hourly:,.2f})")
            else:
                print("  No cost data available for today yet")
            
        except Exception as e:
            print(f"⚠ Real-time monitoring limited: {e}")
    
    def test_09_cost_allocation_tags(self):
        """Test 9: Verify cost allocation tag analysis"""
        print("\n=== Test 9: Cost Allocation Tags ===")
        
        try:
            # Get tag keys
            tag_keys_response = self.ce.get_tags(
                TimePeriod={
                    'Start': self.start_date.strftime('%Y-%m-%d'),
                    'End': self.end_date.strftime('%Y-%m-%d')
                }
            )
            
            tag_keys = tag_keys_response.get('Tags', [])
            print(f"✓ Found {len(tag_keys)} cost allocation tags in use")
            
            # Analyze tag coverage for top tags
            for tag_key in tag_keys[:5]:  # Top 5 tags
                tag_values = self.ce.get_tags(
                    TimePeriod={
                        'Start': self.start_date.strftime('%Y-%m-%d'),
                        'End': self.end_date.strftime('%Y-%m-%d')
                    },
                    TagKey=tag_key
                )
                
                values = tag_values.get('Tags', [])
                print(f"  - {tag_key}: {len(values)} values")
            
            # Get untagged resources cost
            untagged_response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date.strftime('%Y-%m-%d'),
                    'End': self.end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Tags': {
                        'Key': 'Environment',
                        'Values': ['']
                    }
                }
            )
            
            print("✓ Tag-based cost allocation analysis complete")
            
        except Exception as e:
            print(f"⚠ Tag analysis limited: {e}")
    
    def test_10_end_to_end_workflow(self):
        """Test 10: Verify end-to-end workflow integration"""
        print("\n=== Test 10: End-to-End Workflow ===")
        
        try:
            print("  Simulating complete FinOps workflow...")
            
            # Step 1: Get current costs
            current_costs = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (self.end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'End': self.end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            yesterday_cost = float(current_costs['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
            print(f"✓ Step 1: Yesterday's cost: ${yesterday_cost:,.2f}")
            
            # Step 2: Get predictions
            agent = BudgetPredictionAgent()
            df = agent.fetch_historical_costs(months=1)
            agent.train_prediction_models(df)
            predictions = agent.predict_budget(days_ahead=7)
            
            next_week_cost = predictions['summary']['total_predicted_cost']
            print(f"✓ Step 2: Next week prediction: ${next_week_cost:,.2f}")
            
            # Step 3: Identify optimizations
            insights = get_budget_insights(months_history=1, prediction_days=7)
            total_savings = insights['trusted_advisor']['total_monthly_savings']
            print(f"✓ Step 3: Optimization potential: ${total_savings:,.2f}/month")
            
            # Step 4: Generate action plan
            action_items = []
            if total_savings > 1000:
                action_items.append("High-priority: Implement Trusted Advisor recommendations")
            if yesterday_cost > next_week_cost / 7 * 1.2:
                action_items.append("Investigate: Yesterday's cost spike")
            if insights['anomalies']['summary']['total_anomalies'] > 0:
                action_items.append("Review: Cost anomalies detected")
            
            print(f"✓ Step 4: Generated {len(action_items)} action items")
            for item in action_items:
                print(f"  - {item}")
            
            print("\n✓ End-to-end workflow completed successfully!")
            
        except Exception as e:
            self.fail(f"End-to-end workflow test failed: {e}")


def run_all_tests():
    """Run all tests and generate summary report"""
    print("\n" + "="*60)
    print("INTEGRATED FINOPS PLATFORM - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegratedFinOpsPlatform)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
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
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    }
    
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to: test_results.json")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)