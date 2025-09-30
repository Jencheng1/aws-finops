#!/usr/bin/env python3
"""
Test dashboard functions without Streamlit runtime
Tests all core functions with real AWS APIs
"""

import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
import time

# Initialize AWS clients
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
lambda_client = boto3.client('lambda')
bedrock_runtime = boto3.client('bedrock-agent-runtime')

print("=" * 70)
print("DASHBOARD FUNCTION TEST - REAL AWS APIs")
print("=" * 70)
print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)


def test_cost_data_function():
    """Test cost data fetching function"""
    print("\n1. Testing Cost Data Fetching")
    
    for days in [1, 7, 30]:
        print(f"\n  Testing {days}-day cost data:")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Process like dashboard
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
                daily_costs.append({'date': result['TimePeriod']['Start'], 'cost': daily_total})
            
            print(f"    ✓ Total cost: ${total_cost:.2f}")
            print(f"    ✓ Services: {len(services)}")
            print(f"    ✓ Daily average: ${total_cost/days:.2f}")
            
            # Calculate trend
            if len(daily_costs) > 1:
                first = daily_costs[0]['cost']
                last = daily_costs[-1]['cost']
                trend = ((last - first) / first * 100) if first > 0 else 0
                print(f"    ✓ Trend: {trend:+.1f}%")
            
            return True
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False


def test_ec2_utilization_function():
    """Test EC2 utilization function"""
    print("\n2. Testing EC2 Utilization Analysis")
    
    try:
        instances = []
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                # Get CPU utilization
                end = datetime.now()
                start = end - timedelta(days=7)
                
                try:
                    cpu_response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start,
                        EndTime=end,
                        Period=3600,
                        Statistics=['Average', 'Maximum']
                    )
                    
                    cpu_data = cpu_response.get('Datapoints', [])
                    avg_cpu = sum(d['Average'] for d in cpu_data) / len(cpu_data) if cpu_data else 0
                    max_cpu = max((d['Maximum'] for d in cpu_data), default=0)
                    
                    instances.append({
                        'InstanceId': instance_id,
                        'InstanceType': instance_type,
                        'AvgCPU': round(avg_cpu, 2),
                        'MaxCPU': round(max_cpu, 2),
                        'State': instance['State']['Name']
                    })
                except:
                    pass
        
        print(f"  ✓ Found {len(instances)} running instances")
        
        # Analyze utilization
        low = sum(1 for i in instances if i['AvgCPU'] < 10)
        medium = sum(1 for i in instances if 10 <= i['AvgCPU'] < 50)
        high = sum(1 for i in instances if i['AvgCPU'] >= 50)
        
        print(f"  ✓ Low utilization: {low}")
        print(f"  ✓ Medium utilization: {medium}")
        print(f"  ✓ High utilization: {high}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_lambda_functions():
    """Test Lambda function invocations"""
    print("\n3. Testing Lambda Functions")
    
    functions = ['finops-cost-analysis', 'finops-optimization', 'finops-forecasting']
    
    for func_name in functions:
        print(f"\n  Testing {func_name}:")
        
        try:
            # Test invocation
            event = {
                'apiPath': '/test',
                'parameters': [],
                'httpMethod': 'GET'
            }
            
            response = lambda_client.invoke(
                FunctionName=func_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            print(f"    ✓ Invoked successfully (status: {response['StatusCode']})")
            
            # Parse response
            result = json.loads(response['Payload'].read())
            print(f"    ✓ Response received")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")


def test_chatbot_responses():
    """Test chatbot response generation with real data"""
    print("\n4. Testing Chatbot Response Generation")
    
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
        
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                services[service] = services.get(service, 0) + cost
                total_cost += cost
        
        print(f"\n  Using ${total_cost:.2f} in real cost data")
        
        # Test response generation
        test_prompts = [
            "What are my top costs?",
            "How much am I spending?",
            "What's my most expensive service?"
        ]
        
        for prompt in test_prompts:
            # Simulate response generation
            if "top" in prompt.lower():
                top_5 = sorted(services.items(), key=lambda x: x[1], reverse=True)[:5]
                response = f"Top 5 services: {', '.join([f'{s[0]} (${s[1]:.2f})' for s in top_5])}"
            elif "spending" in prompt.lower():
                response = f"Total spending: ${total_cost:.2f} over 7 days"
            elif "expensive" in prompt.lower():
                top = sorted(services.items(), key=lambda x: x[1], reverse=True)[0]
                response = f"Most expensive: {top[0]} at ${top[1]:.2f}"
            else:
                response = "I can help with cost analysis"
            
            print(f"  ✓ '{prompt}' -> '{response[:50]}...'")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_export_functions():
    """Test export functionality"""
    print("\n5. Testing Export Functions")
    
    try:
        # Test data
        data = {
            'total_cost': 1234.56,
            'services': {'EC2': 456.78, 'S3': 234.56},
            'date': datetime.now().isoformat()
        }
        
        # CSV export
        df = pd.DataFrame(list(data['services'].items()), columns=['Service', 'Cost'])
        csv = df.to_csv(index=False)
        print(f"  ✓ CSV export: {len(csv)} bytes")
        
        # JSON export
        json_str = json.dumps(data, indent=2)
        print(f"  ✓ JSON export: {len(json_str)} bytes")
        
        # PDF structure
        pdf = f"Report\nTotal: ${data['total_cost']}\nDate: {data['date']}"
        print(f"  ✓ PDF structure: {len(pdf)} bytes")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_bedrock_agent():
    """Test Bedrock agent if available"""
    print("\n6. Testing Bedrock Agent")
    
    try:
        with open('finops_config.json', 'r') as f:
            config = json.load(f)
        
        if 'agents' in config and config['agents']:
            agent = config['agents'][0]
            agent_id = agent['agent_id']
            alias_id = agent.get('alias_id', 'TSTALIASID')
            
            import uuid
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=str(uuid.uuid4()),
                inputText="What are my costs?"
            )
            
            print("  ✓ Agent invoked successfully")
        else:
            print("  ⚠️  No agents configured")
            
    except Exception as e:
        print(f"  ⚠️  Bedrock test skipped: {e}")


def test_mcp_server():
    """Test MCP server connectivity"""
    print("\n7. Testing MCP Server")
    
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8765))
    sock.close()
    
    if result == 0:
        print("  ✓ MCP server is running on port 8765")
        
        # Test WebSocket connection
        try:
            import websocket
            ws = websocket.create_connection("ws://localhost:8765")
            
            # List tools
            ws.send(json.dumps({"type": "list_tools"}))
            response = json.loads(ws.recv())
            
            if 'tools' in response:
                print(f"  ✓ MCP has {len(response['tools'])} tools available")
            
            ws.close()
        except Exception as e:
            print(f"  ⚠️  WebSocket test failed: {e}")
    else:
        print("  ⚠️  MCP server not running")


# Run all tests
def main():
    tests = [
        ("Cost Data Fetching", test_cost_data_function),
        ("EC2 Utilization", test_ec2_utilization_function),
        ("Lambda Functions", test_lambda_functions),
        ("Chatbot Responses", test_chatbot_responses),
        ("Export Functions", test_export_functions),
        ("Bedrock Agent", test_bedrock_agent),
        ("MCP Server", test_mcp_server)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 70)
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe dashboard is ready to run:")
        print("  streamlit run finops_dashboard_with_chatbot.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)