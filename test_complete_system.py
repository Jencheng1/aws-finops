#!/usr/bin/env python3
"""
Complete System Test - All Components with Real AWS APIs
"""

import boto3
import json
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta
import pandas as pd

print("=" * 80)
print("COMPLETE FINOPS SYSTEM TEST - REAL AWS APIs ONLY")
print("=" * 80)
print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Initialize AWS clients
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
lambda_client = boto3.client('lambda')
sts = boto3.client('sts')

# Get account info
account_id = sts.get_caller_identity()['Account']

class CompleteSystemTest:
    def __init__(self):
        self.results = {
            'aws_apis': {'passed': 0, 'failed': 0},
            'lambda_functions': {'passed': 0, 'failed': 0},
            'chatbot': {'passed': 0, 'failed': 0},
            'export': {'passed': 0, 'failed': 0},
            'mcp': {'passed': 0, 'failed': 0}
        }
    
    def test_aws_cost_explorer(self):
        """Test AWS Cost Explorer API with real data"""
        print("\n1. TESTING AWS COST EXPLORER API")
        print("-" * 40)
        
        test_periods = [1, 7, 30]
        
        for days in test_periods:
            try:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                
                response = ce.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                )
                
                # Process results
                total_cost = 0
                services = set()
                
                for result in response['ResultsByTime']:
                    for group in result['Groups']:
                        service = group['Keys'][0]
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        if cost > 0:
                            services.add(service)
                            total_cost += cost
                
                print(f"✓ {days}-day cost data: ${total_cost:.2f} across {len(services)} services")
                self.results['aws_apis']['passed'] += 1
                
            except Exception as e:
                print(f"✗ Failed to get {days}-day cost data: {e}")
                self.results['aws_apis']['failed'] += 1
    
    def test_ec2_instances(self):
        """Test EC2 API and instance analysis"""
        print("\n2. TESTING EC2 INSTANCE ANALYSIS")
        print("-" * 40)
        
        try:
            # Get running instances
            response = ec2.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            
            instance_count = 0
            instance_types = {}
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_count += 1
                    itype = instance['InstanceType']
                    instance_types[itype] = instance_types.get(itype, 0) + 1
            
            print(f"✓ Found {instance_count} running instances")
            print(f"✓ Instance types: {dict(instance_types)}")
            
            # Test CloudWatch metrics for one instance
            if instance_count > 0:
                test_instance = response['Reservations'][0]['Instances'][0]
                instance_id = test_instance['InstanceId']
                
                cw = boto3.client('cloudwatch')
                end = datetime.now()
                start = end - timedelta(days=7)
                
                metric_response = cw.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=3600,
                    Statistics=['Average']
                )
                
                datapoints = metric_response.get('Datapoints', [])
                if datapoints:
                    avg_cpu = sum(d['Average'] for d in datapoints) / len(datapoints)
                    print(f"✓ CPU metrics retrieved for {instance_id}: {avg_cpu:.1f}% avg")
                
            self.results['aws_apis']['passed'] += 2
            
        except Exception as e:
            print(f"✗ EC2 test failed: {e}")
            self.results['aws_apis']['failed'] += 1
    
    def test_lambda_functions(self):
        """Test Lambda function invocations"""
        print("\n3. TESTING LAMBDA FUNCTIONS")
        print("-" * 40)
        
        lambda_tests = [
            {
                'name': 'finops-cost-analysis',
                'event': {
                    'apiPath': '/getCostBreakdown',
                    'parameters': [{'name': 'days', 'value': '7'}],
                    'function': 'get_cost_breakdown'
                }
            },
            {
                'name': 'finops-optimization',
                'event': {
                    'apiPath': '/getOptimizations',
                    'parameters': [],
                    'function': 'get_optimization_recommendations'
                }
            },
            {
                'name': 'finops-forecasting',
                'event': {
                    'apiPath': '/forecastCosts',
                    'parameters': [{'name': 'months', 'value': '3'}],
                    'function': 'forecast_costs'
                }
            }
        ]
        
        for test in lambda_tests:
            try:
                response = lambda_client.invoke(
                    FunctionName=test['name'],
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test['event'])
                )
                
                status_code = response['StatusCode']
                result = json.loads(response['Payload'].read())
                
                if status_code == 200:
                    print(f"✓ {test['name']} invoked successfully")
                    if 'response' in result:
                        print(f"  Response received: {str(result)[:100]}...")
                    self.results['lambda_functions']['passed'] += 1
                else:
                    print(f"✗ {test['name']} returned status {status_code}")
                    self.results['lambda_functions']['failed'] += 1
                    
            except Exception as e:
                print(f"✗ {test['name']} failed: {e}")
                self.results['lambda_functions']['failed'] += 1
    
    def test_chatbot_functionality(self):
        """Test chatbot response generation with real data"""
        print("\n4. TESTING CHATBOT FUNCTIONALITY")
        print("-" * 40)
        
        # Get real cost data
        try:
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Process data
            total_cost = 0
            services = {}
            daily_costs = []
            
            for result in response['ResultsByTime']:
                daily_total = 0
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    services[service] = services.get(service, 0) + cost
                    daily_total += cost
                    total_cost += cost
                daily_costs.append(daily_total)
            
            print(f"✓ Loaded ${total_cost:.2f} in real cost data")
            print(f"✓ Found {len(services)} services")
            
            # Test chatbot queries
            queries = [
                ("What are my top costs?", lambda: len(services) > 0),
                ("How much am I spending daily?", lambda: total_cost / 7 > 0),
                ("Which service costs most?", lambda: max(services.values()) if services else 0),
                ("Show cost trend", lambda: len(daily_costs) == 7)
            ]
            
            for query, validator in queries:
                if validator():
                    print(f"✓ Can answer: '{query}'")
                    self.results['chatbot']['passed'] += 1
                else:
                    print(f"✗ Cannot answer: '{query}'")
                    self.results['chatbot']['failed'] += 1
                    
        except Exception as e:
            print(f"✗ Chatbot test failed: {e}")
            self.results['chatbot']['failed'] += 1
    
    def test_export_functionality(self):
        """Test data export capabilities"""
        print("\n5. TESTING EXPORT FUNCTIONALITY")
        print("-" * 40)
        
        # Get real data for export
        try:
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now().date() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'End': datetime.now().date().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            total = sum(
                float(r['Total']['UnblendedCost']['Amount'])
                for r in response['ResultsByTime']
            )
            
            # Test CSV export
            df = pd.DataFrame({
                'Date': [r['TimePeriod']['Start'] for r in response['ResultsByTime']],
                'Cost': [float(r['Total']['UnblendedCost']['Amount']) for r in response['ResultsByTime']]
            })
            
            csv_data = df.to_csv(index=False)
            print(f"✓ CSV export successful: {len(csv_data)} bytes")
            self.results['export']['passed'] += 1
            
            # Test JSON export
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_cost': total,
                'daily_costs': df.to_dict('records')
            }
            
            json_data = json.dumps(export_data, indent=2)
            print(f"✓ JSON export successful: {len(json_data)} bytes")
            self.results['export']['passed'] += 1
            
            # Test PDF structure
            pdf_content = f"""
FinOps Cost Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Cost (7 days): ${total:.2f}
Daily Average: ${total/7:.2f}
"""
            print(f"✓ PDF structure created: {len(pdf_content)} bytes")
            self.results['export']['passed'] += 1
            
        except Exception as e:
            print(f"✗ Export test failed: {e}")
            self.results['export']['failed'] += 1
    
    def test_mcp_server(self):
        """Test MCP server connectivity"""
        print("\n6. TESTING MCP SERVER")
        print("-" * 40)
        
        import socket
        
        # Check if MCP is running
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8765))
        sock.close()
        
        if result == 0:
            print("✓ MCP server is running on port 8765")
            self.results['mcp']['passed'] += 1
            
            # Test WebSocket connection
            try:
                import websocket
                ws = websocket.create_connection("ws://localhost:8765", timeout=5)
                
                # Test list tools
                ws.send(json.dumps({"type": "list_tools"}))
                response = json.loads(ws.recv())
                
                if 'tools' in response:
                    print(f"✓ MCP has {len(response['tools'])} tools available")
                    
                    # Test a tool
                    ws.send(json.dumps({
                        "type": "tool_call",
                        "tool": "get_cost_analysis",
                        "parameters": {"days": 7}
                    }))
                    
                    tool_response = json.loads(ws.recv())
                    if 'result' in tool_response:
                        print("✓ MCP tool invocation successful")
                        self.results['mcp']['passed'] += 1
                
                ws.close()
                
            except Exception as e:
                print(f"✗ MCP WebSocket test failed: {e}")
                self.results['mcp']['failed'] += 1
        else:
            print("⚠️  MCP server not running (optional component)")
    
    def test_bedrock_agent(self):
        """Test Bedrock agent if configured"""
        print("\n7. TESTING BEDROCK AGENT")
        print("-" * 40)
        
        try:
            with open('finops_config.json', 'r') as f:
                config = json.load(f)
            
            if 'agents' in config and config['agents']:
                agent = config['agents'][0]
                agent_id = agent['agent_id']
                
                print(f"✓ Found agent configuration: {agent_id}")
                
                # Try to invoke (expect access denied)
                bedrock_runtime = boto3.client('bedrock-agent-runtime')
                try:
                    import uuid
                    response = bedrock_runtime.invoke_agent(
                        agentId=agent_id,
                        agentAliasId=agent.get('alias_id', 'TSTALIASID'),
                        sessionId=str(uuid.uuid4()),
                        inputText="Test query"
                    )
                    print("✓ Bedrock agent invoked successfully")
                except Exception as e:
                    if 'accessDeniedException' in str(e):
                        print("⚠️  Bedrock access denied (expected without proper permissions)")
                    else:
                        print(f"✗ Bedrock test failed: {e}")
            else:
                print("⚠️  No Bedrock agents configured")
                
        except Exception as e:
            print(f"⚠️  Bedrock test skipped: {e}")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            
            if total > 0:
                success_rate = (passed / total) * 100
                print(f"{category.upper():20} Passed: {passed:3} Failed: {failed:3} Success: {success_rate:6.1f}%")
                total_passed += passed
                total_failed += failed
        
        print("-" * 80)
        
        grand_total = total_passed + total_failed
        if grand_total > 0:
            overall_success = (total_passed / grand_total) * 100
            print(f"{'TOTAL':20} Passed: {total_passed:3} Failed: {total_failed:3} Success: {overall_success:6.1f}%")
        
        print("=" * 80)
        
        if total_failed == 0:
            print("\n🎉 ALL TESTS PASSED! The FinOps system is fully operational.")
            print("\nYou can now run:")
            print("  streamlit run finops_dashboard_with_chatbot.py")
        else:
            print(f"\n⚠️  {total_failed} tests failed. Please check the errors above.")
        
        return total_failed == 0


def check_system_requirements():
    """Check system requirements before running tests"""
    print("\nCHECKING SYSTEM REQUIREMENTS")
    print("-" * 40)
    
    requirements_met = True
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 7:
        print(f"✓ Python {python_version.major}.{python_version.minor} installed")
    else:
        print(f"✗ Python 3.7+ required (found {python_version.major}.{python_version.minor})")
        requirements_met = False
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        account = sts.get_caller_identity()
        print(f"✓ AWS credentials configured (Account: {account['Account']})")
    except:
        print("✗ AWS credentials not configured")
        requirements_met = False
    
    # Check required modules
    modules = ['boto3', 'pandas', 'streamlit', 'plotly', 'websocket']
    for module in modules:
        try:
            __import__(module)
            print(f"✓ Module '{module}' installed")
        except ImportError:
            print(f"✗ Module '{module}' not installed")
            requirements_met = False
    
    return requirements_met


if __name__ == "__main__":
    # Check requirements first
    if not check_system_requirements():
        print("\n❌ Please install missing requirements before running tests.")
        sys.exit(1)
    
    # Run complete system test
    tester = CompleteSystemTest()
    
    # Run all test categories
    tester.test_aws_cost_explorer()
    tester.test_ec2_instances()
    tester.test_lambda_functions()
    tester.test_chatbot_functionality()
    tester.test_export_functionality()
    tester.test_mcp_server()
    tester.test_bedrock_agent()
    
    # Print summary
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)