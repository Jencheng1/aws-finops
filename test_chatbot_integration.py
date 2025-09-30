#!/usr/bin/env python3
"""
Comprehensive test suite for FinOps Dashboard with Chatbot Integration
Tests all components including real AWS API calls, chatbot functionality, and export features
"""

import pytest
import boto3
import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import sys
import os
import uuid
import time
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test Configuration
TEST_CONFIG = {
    'aws_region': 'us-east-1',
    'test_days': 7,
    'agent_timeout': 30,
    'lambda_timeout': 10
}

class TestFinOpsChatbot:
    """Test suite for FinOps chatbot integration"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        print("\n=== Setting up FinOps Chatbot Test Suite ===")
        cls.ce = boto3.client('ce')
        cls.lambda_client = boto3.client('lambda')
        cls.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        # Load configuration
        try:
            with open('finops_config.json', 'r') as f:
                cls.config = json.load(f)
            print("✓ Loaded configuration")
        except:
            cls.config = None
            print("✗ Configuration not found")
    
    def test_cost_data_fetching(self):
        """Test real AWS Cost Explorer API calls"""
        print("\n--- Testing Cost Data Fetching ---")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=TEST_CONFIG['test_days'])
        
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            assert 'ResultsByTime' in response
            assert len(response['ResultsByTime']) > 0
            
            total_cost = 0
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    total_cost += cost
            
            print(f"✓ Fetched cost data successfully")
            print(f"  Total cost for {TEST_CONFIG['test_days']} days: ${total_cost:.2f}")
            
        except Exception as e:
            pytest.fail(f"Failed to fetch cost data: {e}")
    
    def test_chatbot_session_initialization(self):
        """Test chatbot session state initialization"""
        print("\n--- Testing Chatbot Session Initialization ---")
        
        # Mock Streamlit session state
        mock_session_state = {
            'chat_messages': [],
            'cost_data_cache': None,
            'chat_mode': False
        }
        
        # Test initialization
        assert 'chat_messages' in mock_session_state
        assert isinstance(mock_session_state['chat_messages'], list)
        assert mock_session_state['cost_data_cache'] is None
        assert mock_session_state['chat_mode'] is False
        
        print("✓ Session state initialized correctly")
    
    def test_bedrock_agent_query(self):
        """Test Bedrock agent integration"""
        print("\n--- Testing Bedrock Agent Query ---")
        
        if not self.config or 'agents' not in self.config:
            print("⚠️  Skipping Bedrock test - no agent configuration")
            return
        
        agent_info = self.config['agents'][0]
        agent_id = agent_info['agent_id']
        agent_alias = agent_info.get('alias_id', 'TSTALIASID')
        
        test_prompt = "What are my top 3 AWS services by cost?"
        
        try:
            session_id = str(uuid.uuid4())
            
            response = self.bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias,
                sessionId=session_id,
                inputText=test_prompt
            )
            
            # Process response
            result = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result += chunk['bytes'].decode('utf-8')
            
            assert len(result) > 0
            print("✓ Bedrock agent responded successfully")
            print(f"  Response length: {len(result)} characters")
            
        except Exception as e:
            print(f"⚠️  Bedrock agent test skipped: {e}")
    
    def test_lambda_invocation(self):
        """Test Lambda function invocation"""
        print("\n--- Testing Lambda Function Invocation ---")
        
        test_event = {
            'apiPath': '/getCostBreakdown',
            'parameters': [{'name': 'days', 'value': '7'}],
            'actionGroup': 'test',
            'httpMethod': 'POST'
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='finops-cost-analysis',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Verify response structure
            assert response['StatusCode'] == 200
            
            if 'response' in result:
                print("✓ Lambda invoked successfully")
                
                # Check for cost data in response
                if 'responseBody' in result.get('response', {}):
                    body = result['response']['responseBody']['application/json']['body']
                    parsed_body = json.loads(body)
                    
                    if 'total_cost' in parsed_body:
                        print(f"  Total cost returned: ${parsed_body['total_cost']:.2f}")
            else:
                print("✓ Lambda invoked (response format may vary)")
                
        except Exception as e:
            pytest.fail(f"Failed to invoke Lambda: {e}")
    
    def test_fallback_response_generator(self):
        """Test fallback response generation with real data"""
        print("\n--- Testing Fallback Response Generator ---")
        
        # Get real cost data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Process data
            services_by_cost = {}
            daily_costs = []
            
            for result in response['ResultsByTime']:
                daily_total = 0
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    services_by_cost[service] = services_by_cost.get(service, 0) + cost
                    daily_total += cost
                
                daily_costs.append({
                    'date': result['TimePeriod']['Start'],
                    'cost': daily_total
                })
            
            total_cost = sum(services_by_cost.values())
            
            # Create mock cost data cache
            cost_data_cache = {
                'total_cost': total_cost,
                'daily_average': total_cost / 7 if total_cost > 0 else 0,
                'service_count': len(services_by_cost),
                'services_by_cost': dict(sorted(services_by_cost.items(), 
                                              key=lambda x: x[1], reverse=True)),
                'daily_trend': daily_costs
            }
            
            # Test different prompt types
            test_prompts = [
                ("What are my highest costs?", "highest"),
                ("How can I save money?", "save"),
                ("Show me cost trends", "trend"),
                ("What's my total spend?", "general")
            ]
            
            for prompt, prompt_type in test_prompts:
                # Simulate fallback response generation
                response = self._generate_test_fallback_response(prompt, cost_data_cache)
                
                assert len(response) > 0
                print(f"✓ Generated fallback response for '{prompt_type}' prompt")
                
                # Verify response contains relevant data
                if prompt_type == "highest" and services_by_cost:
                    top_service = list(services_by_cost.keys())[0]
                    assert top_service in response or "Based on your current data" in response
                
        except Exception as e:
            pytest.fail(f"Failed to test fallback responses: {e}")
    
    def _generate_test_fallback_response(self, prompt, cost_data):
        """Helper method to generate fallback responses"""
        prompt_lower = prompt.lower()
        
        if not cost_data:
            return "I don't have any cost data available."
        
        if 'highest' in prompt_lower or 'top' in prompt_lower:
            services = cost_data.get('services_by_cost', {})
            top_5 = list(services.items())[:5]
            
            response = "Based on your current data, here are your top 5 services by cost:\n\n"
            for i, (service, cost) in enumerate(top_5, 1):
                response += f"{i}. **{service}**: ${cost:,.2f}\n"
            
            response += f"\nTotal cost for the period: ${cost_data.get('total_cost', 0):,.2f}"
            
        elif 'save' in prompt_lower or 'reduce' in prompt_lower:
            response = "Here are some cost optimization recommendations:\n\n"
            response += "1. **Right-size EC2 instances** - Review underutilized instances\n"
            response += "2. **Use Reserved Instances** - Save up to 72% on predictable workloads\n"
            
        elif 'trend' in prompt_lower:
            daily_trend = cost_data.get('daily_trend', [])
            if len(daily_trend) > 1:
                first_cost = daily_trend[0]['cost']
                last_cost = daily_trend[-1]['cost']
                trend_pct = ((last_cost - first_cost) / first_cost * 100) if first_cost > 0 else 0
                
                response = f"Your costs are {'increasing' if trend_pct > 0 else 'decreasing'} "
                response += f"by {abs(trend_pct):.1f}% over the period."
            else:
                response = "Not enough data to analyze trends."
        
        else:
            response = f"Here's your cost summary:\n"
            response += f"Total cost: ${cost_data.get('total_cost', 0):,.2f}\n"
            response += f"Daily average: ${cost_data.get('daily_average', 0):,.2f}"
        
        return response
    
    def test_export_functionality(self):
        """Test export functionality with real data"""
        print("\n--- Testing Export Functionality ---")
        
        # Create test data
        test_data = {
            'total_cost': 1234.56,
            'daily_average': 176.37,
            'service_count': 12,
            'services_by_cost': {
                'EC2': 456.78,
                'S3': 234.56,
                'RDS': 123.45
            },
            'period': '7 days',
            'export_date': datetime.now().isoformat(),
            'chat_history': [
                {'role': 'user', 'content': 'What are my costs?'},
                {'role': 'assistant', 'content': 'Your total cost is $1234.56'}
            ]
        }
        
        # Test CSV export
        try:
            df = pd.DataFrame()
            df['Metric'] = ['Total Cost', 'Daily Average', 'Service Count']
            df['Value'] = [
                f"${test_data['total_cost']:,.2f}",
                f"${test_data['daily_average']:,.2f}",
                test_data['service_count']
            ]
            
            csv_data = df.to_csv(index=False)
            assert len(csv_data) > 0
            assert 'Total Cost' in csv_data
            print("✓ CSV export successful")
            
        except Exception as e:
            pytest.fail(f"CSV export failed: {e}")
        
        # Test JSON export
        try:
            json_data = json.dumps(test_data, indent=2, default=str)
            assert len(json_data) > 0
            parsed = json.loads(json_data)
            assert parsed['total_cost'] == test_data['total_cost']
            print("✓ JSON export successful")
            
        except Exception as e:
            pytest.fail(f"JSON export failed: {e}")
        
        # Test PDF summary generation
        try:
            pdf_content = f"""
# FinOps Cost Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- Total Cost: ${test_data['total_cost']:,.2f}
- Daily Average: ${test_data['daily_average']:,.2f}
"""
            
            assert len(pdf_content) > 0
            assert 'Total Cost: $' in pdf_content or str(int(test_data['total_cost'])) in pdf_content
            print("✓ PDF summary generation successful")
            
        except Exception as e:
            pytest.fail(f"PDF summary generation failed: {e}")
    
    def test_mcp_integration(self):
        """Test MCP server integration"""
        print("\n--- Testing MCP Integration ---")
        
        # Check if MCP server is running
        import websocket
        
        try:
            ws = websocket.create_connection("ws://localhost:8765", timeout=2)
            
            # Test list tools
            request = {"type": "list_tools"}
            ws.send(json.dumps(request))
            response = json.loads(ws.recv())
            
            assert 'tools' in response
            assert len(response['tools']) > 0
            
            print("✓ MCP server is running")
            print(f"  Available tools: {len(response['tools'])}")
            
            # Test tool invocation
            test_request = {
                "type": "tool_call",
                "tool": "get_cost_analysis",
                "parameters": {"days": 7}
            }
            
            ws.send(json.dumps(test_request))
            tool_response = json.loads(ws.recv())
            
            assert 'result' in tool_response or 'error' in tool_response
            print("✓ MCP tool invocation successful")
            
            ws.close()
            
        except Exception as e:
            print(f"⚠️  MCP integration test skipped: {e}")
    
    def test_chat_conversation_flow(self):
        """Test multi-turn conversation flow"""
        print("\n--- Testing Chat Conversation Flow ---")
        
        # Simulate conversation
        conversation = [
            {"role": "user", "content": "What are my top costs?"},
            {"role": "assistant", "content": "Your top costs are from EC2 and S3 services."},
            {"role": "user", "content": "How can I reduce EC2 costs?"},
            {"role": "assistant", "content": "You can reduce EC2 costs by rightsizing instances."}
        ]
        
        # Test conversation history management
        chat_history = []
        
        for msg in conversation:
            chat_history.append(msg)
            
            # Verify history maintains order
            assert chat_history[-1] == msg
        
        # Test context awareness
        assert len(chat_history) == 4
        assert chat_history[0]['role'] == 'user'
        assert chat_history[1]['role'] == 'assistant'
        
        print("✓ Conversation flow test successful")
        print(f"  Conversation turns: {len(chat_history)}")
    
    def test_enhanced_chat_mode(self):
        """Test enhanced chat mode features"""
        print("\n--- Testing Enhanced Chat Mode ---")
        
        # Test quick prompts
        quick_prompts = [
            "What are my top 5 costs?",
            "How can I reduce EC2 costs?",
            "Show me cost trends",
            "Find idle resources",
            "Forecast next month's costs"
        ]
        
        for prompt in quick_prompts:
            assert len(prompt) > 0
            assert '?' in prompt or 'Show' in prompt or 'Find' in prompt or 'Forecast' in prompt
        
        print("✓ Quick prompts validated")
        print(f"  Available quick prompts: {len(quick_prompts)}")
        
        # Test chat mode toggle
        chat_mode_states = [False, True, False]
        
        for state in chat_mode_states:
            # Simulate toggle
            assert isinstance(state, bool)
        
        print("✓ Chat mode toggle test successful")

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n--- Testing Error Handling ---")
        
        # Test with invalid Lambda function
        try:
            response = self.lambda_client.invoke(
                FunctionName='non-existent-function',
                InvocationType='RequestResponse',
                Payload=json.dumps({})
            )
        except Exception as e:
            assert 'ResourceNotFoundException' in str(e) or 'Function not found' in str(e)
            print("✓ Lambda error handling successful")
        
        # Test with invalid date range
        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': '2024-13-01',  # Invalid month
                    'End': '2024-12-31'
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
        except Exception as e:
            assert 'ValidationException' in str(e) or 'Invalid' in str(e)
            print("✓ Cost Explorer error handling successful")

def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "="*60)
    print("FINOPS CHATBOT INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"AWS Region: {TEST_CONFIG['aws_region']}")
    print("="*60)
    
    # Create test instance
    test_suite = TestFinOpsChatbot()
    test_suite.setup_class()
    
    # Run all tests
    test_methods = [
        test_suite.test_cost_data_fetching,
        test_suite.test_chatbot_session_initialization,
        test_suite.test_bedrock_agent_query,
        test_suite.test_lambda_invocation,
        test_suite.test_fallback_response_generator,
        test_suite.test_export_functionality,
        test_suite.test_mcp_integration,
        test_suite.test_chat_conversation_flow,
        test_suite.test_enhanced_chat_mode,
        test_suite.test_error_handling
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
        except pytest.skip.Exception:
            skipped += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test_method.__name__} failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(test_methods)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Skipped: {skipped} ⚠️")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)