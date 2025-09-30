#!/usr/bin/env python3
"""
Comprehensive Test Suite for FinOps System
Tests all components: Lambda, S3, IAM, and direct AWS API calls
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from colorama import init, Fore, Style

init(autoreset=True)

class FinOpsTestSuite:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
        # Initialize clients
        self.lambda_client = boto3.client('lambda')
        self.s3 = boto3.client('s3')
        self.ce = boto3.client('ce')
        self.ec2 = boto3.client('ec2')
        self.iam = boto3.client('iam')
        
        # Load config
        try:
            with open('finops_config.json', 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {}
    
    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        if passed:
            print(f"{Fore.GREEN}✓ {test_name}{Style.RESET_ALL}")
            self.passed += 1
        else:
            print(f"{Fore.RED}✗ {test_name}{Style.RESET_ALL}")
            if details:
                print(f"  {Fore.YELLOW}Details: {details}{Style.RESET_ALL}")
            self.failed += 1
        
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    def test_iam_roles(self):
        """Test IAM roles exist"""
        print(f"\n{Fore.CYAN}Testing IAM Roles...{Style.RESET_ALL}")
        
        roles_to_check = ['FinOpsBedrockAgentRole', 'FinOpsLambdaRole']
        
        for role_name in roles_to_check:
            try:
                self.iam.get_role(RoleName=role_name)
                self.log_result(f"IAM Role: {role_name}", True)
            except Exception as e:
                self.log_result(f"IAM Role: {role_name}", False, str(e))
    
    def test_s3_bucket(self):
        """Test S3 bucket exists and is accessible"""
        print(f"\n{Fore.CYAN}Testing S3 Bucket...{Style.RESET_ALL}")
        
        if 'bucket_name' in self.config:
            bucket_name = self.config['bucket_name']
            
            try:
                self.s3.head_bucket(Bucket=bucket_name)
                self.log_result(f"S3 Bucket: {bucket_name}", True)
                
                # Test we can list objects
                response = self.s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                self.log_result("S3 List Objects", True)
                
            except Exception as e:
                self.log_result(f"S3 Bucket: {bucket_name}", False, str(e))
        else:
            self.log_result("S3 Bucket Config", False, "No bucket in config")
    
    def test_lambda_functions(self):
        """Test Lambda functions"""
        print(f"\n{Fore.CYAN}Testing Lambda Functions...{Style.RESET_ALL}")
        
        lambda_name = 'finops-cost-analysis'
        
        # Test function exists
        try:
            response = self.lambda_client.get_function(FunctionName=lambda_name)
            self.log_result(f"Lambda Exists: {lambda_name}", True)
            
            # Test function invocation
            test_event = {
                'apiPath': '/getCostBreakdown',
                'parameters': [{'name': 'days', 'value': '7'}],
                'actionGroup': 'test',
                'httpMethod': 'POST'
            }
            
            invoke_response = self.lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            status_code = invoke_response['StatusCode']
            if status_code == 200:
                result = json.loads(invoke_response['Payload'].read())
                
                if 'response' in result:
                    self.log_result("Lambda Invocation", True)
                    
                    # Check response structure
                    response_body = result['response'].get('responseBody', {})
                    if 'application/json' in response_body:
                        body = json.loads(response_body['application/json']['body'])
                        if 'total_cost' in body or 'error' not in body:
                            self.log_result("Lambda Response Valid", True)
                        else:
                            self.log_result("Lambda Response Valid", False, "Missing expected fields")
                    else:
                        self.log_result("Lambda Response Valid", False, "Invalid response format")
                else:
                    self.log_result("Lambda Invocation", False, "No response field")
            else:
                self.log_result("Lambda Invocation", False, f"Status code: {status_code}")
                
        except Exception as e:
            self.log_result(f"Lambda: {lambda_name}", False, str(e))
    
    def test_cost_explorer_access(self):
        """Test AWS Cost Explorer access"""
        print(f"\n{Fore.CYAN}Testing Cost Explorer Access...{Style.RESET_ALL}")
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            if 'ResultsByTime' in response:
                self.log_result("Cost Explorer API", True)
                
                # Check we got data
                total_cost = sum(
                    float(r['Total']['UnblendedCost']['Amount'])
                    for r in response['ResultsByTime']
                )
                self.log_result("Cost Data Retrieved", True, f"Total: ${total_cost:.2f}")
            else:
                self.log_result("Cost Explorer API", False, "No results")
                
        except Exception as e:
            self.log_result("Cost Explorer API", False, str(e))
    
    def test_ec2_access(self):
        """Test EC2 access"""
        print(f"\n{Fore.CYAN}Testing EC2 Access...{Style.RESET_ALL}")
        
        try:
            response = self.ec2.describe_instances(MaxResults=5)
            self.log_result("EC2 Describe Instances", True)
            
            instance_count = sum(
                len(r['Instances']) 
                for r in response.get('Reservations', [])
            )
            self.log_result("EC2 Instance Count", True, f"Found {instance_count} instances")
            
        except Exception as e:
            self.log_result("EC2 Access", False, str(e))
    
    def test_bedrock_agent(self):
        """Test Bedrock agent if configured"""
        print(f"\n{Fore.CYAN}Testing Bedrock Agent...{Style.RESET_ALL}")
        
        if 'agents' in self.config and self.config['agents']:
            agent_id = self.config['agents'][0]['agent_id']
            alias_id = self.config['agents'][0].get('alias_id', 'TSTALIASID')
            
            try:
                bedrock = boto3.client('bedrock-agent')
                
                # Check agent exists
                response = bedrock.get_agent(agentId=agent_id)
                self.log_result(f"Bedrock Agent Exists: {agent_id}", True)
                
                # Check agent status
                status = response['agent']['agentStatus']
                if status == 'PREPARED':
                    self.log_result("Bedrock Agent Status", True, status)
                else:
                    self.log_result("Bedrock Agent Status", False, f"Status: {status}")
                    
            except Exception as e:
                self.log_result("Bedrock Agent", False, str(e))
        else:
            self.log_result("Bedrock Agent Config", False, "No agent in config")
    
    def test_mcp_config(self):
        """Test MCP configuration exists"""
        print(f"\n{Fore.CYAN}Testing MCP Configuration...{Style.RESET_ALL}")
        
        try:
            with open('mcp_config.json', 'r') as f:
                mcp_config = json.load(f)
            
            self.log_result("MCP Config File", True)
            
            # Validate config structure
            required_fields = ['mcp_version', 'server', 'tools']
            for field in required_fields:
                if field in mcp_config:
                    self.log_result(f"MCP Config: {field}", True)
                else:
                    self.log_result(f"MCP Config: {field}", False, "Missing field")
                    
        except FileNotFoundError:
            self.log_result("MCP Config File", False, "File not found")
        except Exception as e:
            self.log_result("MCP Config", False, str(e))
    
    def test_streamlit_files(self):
        """Test Streamlit dashboard files exist"""
        print(f"\n{Fore.CYAN}Testing Streamlit Files...{Style.RESET_ALL}")
        
        files_to_check = [
            'finops_dashboard_direct.py',
            'finops_dashboard.py',
            'finops_config.json'
        ]
        
        import os
        for file in files_to_check:
            if os.path.exists(file):
                self.log_result(f"File: {file}", True)
            else:
                self.log_result(f"File: {file}", False, "Not found")
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}FinOps System Comprehensive Test Suite{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        start_time = time.time()
        
        # Run tests
        self.test_iam_roles()
        self.test_s3_bucket()
        self.test_lambda_functions()
        self.test_cost_explorer_access()
        self.test_ec2_access()
        self.test_bedrock_agent()
        self.test_mcp_config()
        self.test_streamlit_files()
        
        # Summary
        duration = time.time() - start_time
        
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}Test Summary{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        print(f"\nTotal Tests: {self.passed + self.failed}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")
        print(f"Duration: {duration:.2f} seconds")
        
        if self.failed == 0:
            print(f"\n{Fore.GREEN}🎉 All tests passed!{Style.RESET_ALL}")
            return True
        else:
            print(f"\n{Fore.RED}❌ Some tests failed. Check details above.{Style.RESET_ALL}")
            
            # Show failed tests
            print(f"\n{Fore.YELLOW}Failed Tests:{Style.RESET_ALL}")
            for result in self.results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
            
            return False

def main():
    # Install colorama if needed
    try:
        import colorama
    except ImportError:
        print("Installing colorama for colored output...")
        import subprocess
        subprocess.check_call(['pip3', 'install', 'colorama'])
        import colorama
    
    # Run tests
    suite = FinOpsTestSuite()
    success = suite.run_all_tests()
    
    # Exit code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()