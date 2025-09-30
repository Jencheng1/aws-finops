import boto3
import json
import time
from datetime import datetime

# Initialize clients
bedrock_runtime = boto3.client('bedrock-agent-runtime')
lambda_client = boto3.client('lambda')

# Configuration
AGENT_ID = "S8AZOE6JRP"
AGENT_ALIAS = "L9ZMELFBMS"
LAMBDA_NAME = "finops-cost-analysis"

class FinOpsTestSuite:
    def __init__(self):
        self.results = []
    
    def test_lambda_function(self):
        """Test Lambda function directly"""
        print("Testing Lambda function...")
        
        test_event = {
            'apiPath': '/getCostBreakdown',
            'parameters': [{'name': 'days', 'value': '7'}]
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            assert 'response' in result
            assert result['response']['httpStatusCode'] == 200
            
            self.results.append({'test': 'Lambda Function', 'status': 'PASSED'})
            print("✓ Lambda function test passed")
            
        except Exception as e:
            self.results.append({'test': 'Lambda Function', 'status': 'FAILED', 'error': str(e)})
            print(f"✗ Lambda function test failed: {e}")
    
    def test_bedrock_agent(self):
        """Test Bedrock agent"""
        print("Testing Bedrock agent...")
        
        test_queries = [
            "What are my AWS costs for the last 7 days?",
            "Show me cost trends",
            "What optimization recommendations do you have?"
        ]
        
        for query in test_queries:
            try:
                session_id = f"test-{datetime.now().timestamp()}"
                
                response = bedrock_runtime.invoke_agent(
                    agentId=AGENT_ID,
                    agentAliasId=AGENT_ALIAS,
                    sessionId=session_id,
                    inputText=query
                )
                
                # Check response
                result = ""
                for event in response.get('completion', []):
                    if 'chunk' in event:
                        result += event['chunk']['bytes'].decode('utf-8')
                
                assert len(result) > 0
                
                self.results.append({
                    'test': f'Agent Query: {query[:30]}...',
                    'status': 'PASSED'
                })
                print(f"✓ Agent test passed: {query[:30]}...")
                
                time.sleep(2)  # Avoid rate limiting
                
            except Exception as e:
                self.results.append({
                    'test': f'Agent Query: {query[:30]}...',
                    'status': 'FAILED',
                    'error': str(e)
                })
                print(f"✗ Agent test failed: {e}")
    
    def test_cost_explorer_access(self):
        """Test Cost Explorer access"""
        print("Testing Cost Explorer access...")
        
        ce = boto3.client('ce')
        
        try:
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': '2024-01-01',
                    'End': '2024-01-02'
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            assert 'ResultsByTime' in response
            
            self.results.append({'test': 'Cost Explorer Access', 'status': 'PASSED'})
            print("✓ Cost Explorer access test passed")
            
        except Exception as e:
            self.results.append({
                'test': 'Cost Explorer Access',
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"✗ Cost Explorer test failed: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\nRunning FinOps Test Suite...")
        print("=" * 50)
        
        self.test_lambda_function()
        self.test_cost_explorer_access()
        self.test_bedrock_agent()
        
        # Summary
        print("\nTest Summary:")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        
        for result in self.results:
            status = "✓" if result['status'] == 'PASSED' else "✗"
            print(f"{status} {result['test']}: {result['status']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        print(f"\nTotal: {len(self.results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        return failed == 0

if __name__ == "__main__":
    suite = FinOpsTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
