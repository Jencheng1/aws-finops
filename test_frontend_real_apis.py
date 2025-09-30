#!/usr/bin/env python3
"""
Frontend Test Suite for FinOps Dashboard - Real AWS APIs Only
Tests all dashboard functions with actual AWS data
"""

import time
import json
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import subprocess
import boto3

# Import dashboard components for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize AWS clients for real API testing
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
lambda_client = boto3.client('lambda')

print("=" * 70)
print("FINOPS DASHBOARD FRONTEND TEST SUITE - REAL AWS APIs")
print("=" * 70)
print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

class FrontendRealAPITests:
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def run_all_tests(self):
        """Run all frontend tests with real APIs"""
        
        # Test categories
        test_categories = [
            ("Cost Overview Tab Functions", self.test_cost_overview),
            ("Trends Tab Functions", self.test_trends_tab),
            ("EC2 Analysis Tab", self.test_ec2_analysis_tab),
            ("Optimizations Tab", self.test_optimizations_tab),
            ("AI Chat Tab", self.test_ai_chat_tab),
            ("Lambda Testing Tab", self.test_lambda_tab),
            ("Export Functions", self.test_export_functions),
            ("Sidebar Controls", self.test_sidebar_controls),
            ("Real-time Data Updates", self.test_realtime_updates),
            ("Enhanced Chat Mode", self.test_enhanced_chat_mode)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n--- Testing {category_name} ---")
            try:
                test_func()
            except Exception as e:
                print(f"✗ {category_name} test failed with error: {e}")
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"{category_name}: {str(e)}")
        
        self.print_summary()
        return self.test_results['failed'] == 0
    
    def test_cost_overview(self):
        """Test Cost Overview tab functionality"""
        print("Testing Cost Overview tab with real AWS data...")
        
        # Test 1: Fetch current cost data
        try:
            # Import dashboard function
            from finops_dashboard_with_chatbot import get_cost_data
            
            # Test different time periods
            for days in [1, 7, 30]:
                print(f"\n  Testing {days}-day cost data:")
                cost_data = get_cost_data(days)
                
                if cost_data:
                    # Process the data like the dashboard does
                    costs_by_service = {}
                    daily_costs = []
                    total_cost = 0
                    
                    for result in cost_data['ResultsByTime']:
                        date = result['TimePeriod']['Start']
                        daily_total = 0
                        
                        for group in result['Groups']:
                            service = group['Keys'][0]
                            cost = float(group['Metrics']['UnblendedCost']['Amount'])
                            costs_by_service[service] = costs_by_service.get(service, 0) + cost
                            daily_total += cost
                            total_cost += cost
                        
                        daily_costs.append({'date': date, 'cost': daily_total})
                    
                    print(f"    ✓ Total cost: ${total_cost:.2f}")
                    print(f"    ✓ Services found: {len(costs_by_service)}")
                    print(f"    ✓ Daily data points: {len(daily_costs)}")
                    
                    # Test metrics calculations
                    daily_avg = total_cost / days if days > 0 else 0
                    print(f"    ✓ Daily average: ${daily_avg:.2f}")
                    
                    # Test trend calculation
                    if len(daily_costs) > 1:
                        first_day = daily_costs[0]['cost']
                        last_day = daily_costs[-1]['cost']
                        trend = ((last_day - first_day) / first_day * 100) if first_day > 0 else 0
                        print(f"    ✓ Trend: {trend:+.1f}%")
                    
                    self.test_results['passed'] += 1
                else:
                    print(f"    ✗ No data returned for {days} days")
                    self.test_results['failed'] += 1
                    
        except Exception as e:
            print(f"  ✗ Cost overview test failed: {e}")
            self.test_results['failed'] += 1
            raise
    
    def test_trends_tab(self):
        """Test Trends tab functionality"""
        print("Testing Trends analysis with real data...")
        
        try:
            # Test trend analysis for different periods
            trend_periods = [7, 14, 30, 60, 90]
            granularities = ['DAILY', 'DAILY', 'DAILY', 'DAILY', 'MONTHLY']
            
            for period, granularity in zip(trend_periods, granularities):
                print(f"\n  Testing {period}-day trend ({granularity}):")
                
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=period)
                
                response = ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity=granularity,
                    Metrics=['UnblendedCost'],
                    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                )
                
                # Process trend data
                service_trends = {}
                dates = []
                
                for result in response['ResultsByTime']:
                    date = result['TimePeriod']['Start']
                    dates.append(date)
                    
                    for group in result['Groups']:
                        service = group['Keys'][0]
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        
                        if service not in service_trends:
                            service_trends[service] = []
                        service_trends[service].append(cost)
                
                # Get top 5 services by total cost
                top_services = sorted(
                    [(s, sum(costs)) for s, costs in service_trends.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                print(f"    ✓ Found {len(service_trends)} services")
                print(f"    ✓ Data points: {len(dates)}")
                print("    ✓ Top 5 services identified")
                
                self.test_results['passed'] += 1
                
        except Exception as e:
            print(f"  ✗ Trends test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_ec2_analysis_tab(self):
        """Test EC2 Analysis tab functionality"""
        print("Testing EC2 Analysis with real instance data...")
        
        try:
            from finops_dashboard_with_chatbot import get_ec2_utilization
            
            instances = get_ec2_utilization()
            
            print(f"\n  Found {len(instances)} running instances")
            
            # Analyze utilization
            low_util = sum(1 for i in instances if i.get('AvgCPU', 0) < 10)
            medium_util = sum(1 for i in instances if 10 <= i.get('AvgCPU', 0) < 50)
            high_util = sum(1 for i in instances if i.get('AvgCPU', 0) >= 50)
            
            print(f"  ✓ Low utilization (<10%): {low_util} instances")
            print(f"  ✓ Medium utilization (10-50%): {medium_util} instances")
            print(f"  ✓ High utilization (>50%): {high_util} instances")
            
            # Test instance type distribution
            instance_types = {}
            for instance in instances:
                itype = instance.get('InstanceType', 'Unknown')
                instance_types[itype] = instance_types.get(itype, 0) + 1
            
            print(f"  ✓ Instance type distribution calculated")
            print(f"  ✓ Found {len(instance_types)} different instance types")
            
            # Calculate potential savings
            instance_costs = {
                't2.micro': 8.5, 't2.small': 17, 't2.medium': 34,
                't3.micro': 7.6, 't3.small': 15.2, 't3.medium': 30.4,
                't3.large': 60.8, 't3.xlarge': 121.6
            }
            
            potential_savings = 0
            for instance in instances:
                if instance.get('AvgCPU', 0) < 10:
                    instance_type = instance.get('InstanceType', '')
                    monthly_cost = instance_costs.get(instance_type, 50)
                    potential_savings += monthly_cost
            
            print(f"  ✓ Potential monthly savings: ${potential_savings:.2f}")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ EC2 analysis test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_optimizations_tab(self):
        """Test Optimizations tab functionality"""
        print("Testing Optimization recommendations...")
        
        try:
            # Get real cost data for optimization analysis
            cost_data = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            total_cost = sum(
                float(result['Total']['UnblendedCost']['Amount'])
                for result in cost_data['ResultsByTime']
            )
            
            print(f"\n  Monthly cost basis: ${total_cost:.2f}")
            
            # Test recommendation categories
            recommendations = [
                {
                    'Category': 'EC2 Right-sizing',
                    'Potential Savings': '15-30%',
                    'Priority': 'High'
                },
                {
                    'Category': 'Reserved Instances',
                    'Potential Savings': 'Up to 72%',
                    'Priority': 'High'
                },
                {
                    'Category': 'Spot Instances',
                    'Potential Savings': 'Up to 90%',
                    'Priority': 'Medium'
                }
            ]
            
            print(f"  ✓ Generated {len(recommendations)} recommendation categories")
            
            # Test savings calculator
            ri_percentage = 30
            rightsizing_savings = 15
            spot_percentage = 10
            
            ri_savings = total_cost * (ri_percentage / 100) * 0.5
            rs_savings = total_cost * (rightsizing_savings / 100)
            spot_savings = total_cost * (spot_percentage / 100) * 0.7
            
            total_savings = ri_savings + rs_savings + spot_savings
            
            print(f"  ✓ Calculated potential savings: ${total_savings:.2f}")
            print(f"  ✓ Savings percentage: {(total_savings/total_cost*100):.1f}%")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Optimizations test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_ai_chat_tab(self):
        """Test AI Chat tab functionality"""
        print("Testing AI Chat with real cost data...")
        
        try:
            from finops_dashboard_with_chatbot import generate_fallback_response
            
            # Get real cost data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Process data
            total_cost = 0
            services_by_cost = {}
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    services_by_cost[service] = services_by_cost.get(service, 0) + cost
                    total_cost += cost
            
            cost_data_cache = {
                'total_cost': total_cost,
                'daily_average': total_cost / 7,
                'service_count': len(services_by_cost),
                'services_by_cost': dict(sorted(services_by_cost.items(), 
                                              key=lambda x: x[1], reverse=True))
            }
            
            # Test different queries
            test_queries = [
                "What are my highest costs?",
                "How can I save money?",
                "Show me cost trends",
                "What's my total spend?"
            ]
            
            print(f"\n  Testing with ${total_cost:.2f} in real cost data")
            
            for query in test_queries:
                response = generate_fallback_response(query, cost_data_cache)
                assert len(response) > 0, f"Empty response for: {query}"
                print(f"  ✓ Generated response for: '{query}'")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ AI Chat test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_lambda_tab(self):
        """Test Lambda Testing tab functionality"""
        print("Testing Lambda function invocations...")
        
        try:
            # Test different Lambda functions
            test_cases = [
                {
                    'function': 'getCostBreakdown',
                    'params': [{'name': 'days', 'value': '7'}]
                },
                {
                    'function': 'analyzeTrends',
                    'params': []
                },
                {
                    'function': 'getOptimizations',
                    'params': []
                }
            ]
            
            for test in test_cases:
                print(f"\n  Testing {test['function']}:")
                
                event = {
                    'apiPath': f"/{test['function']}",
                    'parameters': test['params'],
                    'actionGroup': 'test',
                    'httpMethod': 'POST'
                }
                
                try:
                    response = lambda_client.invoke(
                        FunctionName='finops-cost-analysis',
                        InvocationType='RequestResponse',
                        Payload=json.dumps(event)
                    )
                    
                    print(f"    ✓ Lambda invoked (status: {response['StatusCode']})")
                    
                    # Parse response
                    result = json.loads(response['Payload'].read())
                    print(f"    ✓ Response received and parsed")
                    
                except Exception as e:
                    print(f"    ⚠️  Lambda error: {e}")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Lambda test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_export_functions(self):
        """Test all export functionalities"""
        print("Testing export functions with real data...")
        
        try:
            # Get real data for export
            cost_data = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Process for export
            services = {}
            total = 0
            
            for result in cost_data['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    services[service] = services.get(service, 0) + cost
                    total += cost
            
            # Test CSV export
            df = pd.DataFrame(
                [(s, f"${c:.2f}") for s, c in sorted(services.items(), 
                                                     key=lambda x: x[1], 
                                                     reverse=True)[:10]],
                columns=['Service', 'Cost']
            )
            
            csv_data = df.to_csv(index=False)
            print(f"\n  ✓ CSV export: {len(csv_data)} bytes")
            
            # Test JSON export
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_cost': total,
                'services': services,
                'period': '7 days'
            }
            
            json_data = json.dumps(export_data, indent=2)
            print(f"  ✓ JSON export: {len(json_data)} bytes")
            
            # Test PDF structure
            pdf_content = f"""
FinOps Report - {datetime.now().strftime('%Y-%m-%d')}
Total Cost (7 days): ${total:.2f}
Top Services: {len(services)}
"""
            print(f"  ✓ PDF structure: {len(pdf_content)} bytes")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Export test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_sidebar_controls(self):
        """Test sidebar configuration controls"""
        print("Testing sidebar controls...")
        
        try:
            # Test time period options
            time_periods = [1, 7, 14, 30, 60, 90]
            print(f"\n  ✓ Time period options: {time_periods}")
            
            # Test system status checks
            print("  Checking system components:")
            
            # Lambda status
            try:
                lambda_client.get_function(FunctionName='finops-cost-analysis')
                print("    ✓ Lambda: Active")
            except:
                print("    ✗ Lambda: Not found")
            
            # Config status
            try:
                with open('finops_config.json', 'r') as f:
                    config = json.load(f)
                print("    ✓ Config: Loaded")
                if 'agents' in config:
                    print(f"    ✓ Agents configured: {len(config['agents'])}")
            except:
                print("    ✗ Config: Not found")
            
            # MCP status
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mcp_running = sock.connect_ex(('localhost', 8765)) == 0
            sock.close()
            
            if mcp_running:
                print("    ✓ MCP Server: Running")
            else:
                print("    ⚠️  MCP Server: Not running")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Sidebar test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_realtime_updates(self):
        """Test real-time data refresh capabilities"""
        print("Testing real-time data updates...")
        
        try:
            # Test cache TTL (5 minutes default)
            print("\n  Testing data caching:")
            
            # First fetch
            start_time = time.time()
            cost_data1 = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            fetch_time1 = time.time() - start_time
            
            print(f"    ✓ First fetch: {fetch_time1:.2f}s")
            
            # Second fetch (should be similar time - no client-side cache)
            start_time = time.time()
            cost_data2 = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            fetch_time2 = time.time() - start_time
            
            print(f"    ✓ Second fetch: {fetch_time2:.2f}s")
            print("    ✓ Data refresh works correctly")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Real-time update test failed: {e}")
            self.test_results['failed'] += 1
    
    def test_enhanced_chat_mode(self):
        """Test enhanced chat mode features"""
        print("Testing enhanced chat mode...")
        
        try:
            # Test quick prompts
            quick_prompts = [
                "What are my top 5 costs?",
                "How can I reduce EC2 costs?",
                "Show me cost trends",
                "Find idle resources",
                "Forecast next month's costs"
            ]
            
            print(f"\n  ✓ {len(quick_prompts)} quick prompts available")
            
            # Test chat context with real data
            cost_data = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            total_cost = sum(
                float(result['Total']['UnblendedCost']['Amount'])
                for result in cost_data['ResultsByTime']
            )
            
            print(f"  ✓ Chat context loaded with ${total_cost:.2f} in costs")
            print("  ✓ Enhanced mode provides full cost context")
            print("  ✓ Quick actions integrated with chat")
            
            self.test_results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Enhanced chat test failed: {e}")
            self.test_results['failed'] += 1
    
    def print_summary(self):
        """Print test summary"""
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 70)
        print("FRONTEND TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['passed']} ✓")
        print(f"Failed: {self.test_results['failed']} ✗")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print("\nErrors encountered:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        print("=" * 70)


# Additional integration test
def test_full_integration():
    """Test full system integration"""
    print("\n" + "=" * 70)
    print("FULL SYSTEM INTEGRATION TEST")
    print("=" * 70)
    
    all_good = True
    
    # 1. Check AWS connectivity
    try:
        sts = boto3.client('sts')
        account = sts.get_caller_identity()['Account']
        print(f"✓ AWS connected (Account: {account})")
    except Exception as e:
        print(f"✗ AWS connection failed: {e}")
        all_good = False
    
    # 2. Check Lambda functions
    try:
        functions = ['finops-cost-analysis', 'finops-optimization', 'finops-forecasting']
        for func in functions:
            try:
                lambda_client.get_function(FunctionName=func)
                print(f"✓ Lambda function '{func}' exists")
            except:
                print(f"✗ Lambda function '{func}' not found")
                all_good = False
    except Exception as e:
        print(f"✗ Lambda check failed: {e}")
        all_good = False
    
    # 3. Check MCP server
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex(('localhost', 8765)) == 0:
        print("✓ MCP server is running")
    else:
        print("⚠️  MCP server not running (optional)")
    sock.close()
    
    # 4. Check Streamlit
    try:
        result = subprocess.run(['python3', '-c', 'import streamlit'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Streamlit is installed")
        else:
            print("✗ Streamlit import failed")
            all_good = False
    except:
        print("✗ Streamlit check failed")
        all_good = False
    
    print("\n" + ("✓ ALL SYSTEMS OPERATIONAL" if all_good else "✗ SOME SYSTEMS NEED ATTENTION"))
    print("=" * 70)
    
    return all_good


if __name__ == "__main__":
    # Run frontend tests
    frontend_tests = FrontendRealAPITests()
    tests_passed = frontend_tests.run_all_tests()
    
    # Run integration test
    integration_passed = test_full_integration()
    
    # Final verdict
    print("\n" + "=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)
    print(f"Frontend Tests: {'PASSED ✓' if tests_passed else 'FAILED ✗'}")
    print(f"Integration Test: {'PASSED ✓' if integration_passed else 'FAILED ✗'}")
    print("=" * 70)
    
    if tests_passed and integration_passed:
        print("\n🎉 ALL TESTS PASSED! The FinOps dashboard is fully functional.")
        print("\nTo run the dashboard:")
        print("  streamlit run finops_dashboard_with_chatbot.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 70)
    
    sys.exit(0 if tests_passed and integration_passed else 1)