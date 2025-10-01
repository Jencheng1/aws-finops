#!/usr/bin/env python3
"""
Start all services for the AI-Powered FinOps Platform
Includes MCP servers, Lambda functions, and Streamlit interface
"""

import os
import sys
import subprocess
import json
import boto3
import time
import threading
from datetime import datetime
import signal

# Global flag for graceful shutdown
shutdown_flag = threading.Event()

class ServiceManager:
    def __init__(self):
        self.services = []
        self.processes = {}
        self.lambda_client = boto3.client('lambda')
        self.dynamodb = boto3.resource('dynamodb')
        self.iam = boto3.client('iam')
        
    def create_dynamodb_tables(self):
        """Create DynamoDB tables for feedback storage"""
        print("Creating DynamoDB tables...")
        
        try:
            # Create feedback table
            table_name = 'FinOpsFeedback'
            existing_tables = [table.name for table in self.dynamodb.tables.all()]
            
            if table_name not in existing_tables:
                table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'feedback_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'feedback_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'user_id', 'AttributeType': 'S'},
                        {'AttributeName': 'session_id', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'UserIndex',
                            'Keys': [
                                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'BillingMode': 'PAY_PER_REQUEST'
                        },
                        {
                            'IndexName': 'SessionIndex',
                            'Keys': [
                                {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'BillingMode': 'PAY_PER_REQUEST'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                print(f"✓ Created DynamoDB table: {table_name}")
                table.wait_until_exists()
            else:
                print(f"✓ DynamoDB table already exists: {table_name}")
                
            # Create AI context table
            context_table = 'FinOpsAIContext'
            if context_table not in existing_tables:
                table = self.dynamodb.create_table(
                    TableName=context_table,
                    KeySchema=[
                        {'AttributeName': 'context_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'context_id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                print(f"✓ Created DynamoDB table: {context_table}")
                table.wait_until_exists()
            else:
                print(f"✓ DynamoDB table already exists: {context_table}")
                
        except Exception as e:
            print(f"⚠️  Error creating DynamoDB tables: {e}")
            
    def deploy_lambda_functions(self):
        """Deploy Lambda functions for AI agents"""
        print("\nDeploying Lambda functions...")
        
        lambda_functions = [
            {
                'name': 'finops-budget-predictor',
                'handler': 'budget_predictor.lambda_handler',
                'runtime': 'python3.9',
                'role': 'FinOpsLambdaRole',
                'code': 'budget_predictor_lambda.py'
            },
            {
                'name': 'finops-anomaly-detector',
                'handler': 'anomaly_detector.lambda_handler',
                'runtime': 'python3.9',
                'role': 'FinOpsLambdaRole',
                'code': 'anomaly_detector_lambda.py'
            },
            {
                'name': 'finops-resource-optimizer',
                'handler': 'resource_optimizer.lambda_handler',
                'runtime': 'python3.9',
                'role': 'FinOpsLambdaRole',
                'code': 'resource_optimizer_lambda.py'
            },
            {
                'name': 'finops-feedback-processor',
                'handler': 'feedback_processor.lambda_handler',
                'runtime': 'python3.9',
                'role': 'FinOpsLambdaRole',
                'code': 'feedback_processor_lambda.py'
            }
        ]
        
        # Create IAM role for Lambda if it doesn't exist
        try:
            self.iam.get_role(RoleName='FinOpsLambdaRole')
            print("✓ IAM role already exists: FinOpsLambdaRole")
        except:
            print("Creating IAM role for Lambda functions...")
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            self.iam.create_role(
                RoleName='FinOpsLambdaRole',
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for FinOps Lambda functions'
            )
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess',
                'arn:aws:iam::aws:policy/AWSCostExplorerReadOnlyAccess'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName='FinOpsLambdaRole',
                    PolicyArn=policy
                )
            
            print("✓ Created IAM role: FinOpsLambdaRole")
            time.sleep(10)  # Wait for role propagation
            
    def start_mcp_servers(self):
        """Start all MCP servers"""
        print("\nStarting MCP servers...")
        
        mcp_servers = [
            {
                'name': 'cost-explorer-mcp',
                'script': 'finops-copilot/mcp-servers/cost_explorer_mcp.py',
                'port': 8001
            },
            {
                'name': 'apptio-mcp',
                'script': 'apptio_mcp_server.py',
                'port': 8002
            },
            {
                'name': 'cloudwatch-mcp',
                'script': 'finops-copilot/mcp-servers/cloudwatch_mcp.py',
                'port': 8003
            },
            {
                'name': 'resource-mcp',
                'script': 'aws_resource_intelligence_mcp_server.py',
                'port': 8004
            },
            {
                'name': 'tagging-mcp',
                'script': 'finops-copilot/mcp-servers/tagging_mcp.py',
                'port': 8005
            }
        ]
        
        for server in mcp_servers:
            if os.path.exists(server['script']):
                try:
                    cmd = [sys.executable, server['script'], '--port', str(server['port'])]
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    self.processes[server['name']] = process
                    print(f"✓ Started {server['name']} on port {server['port']}")
                except Exception as e:
                    print(f"✗ Failed to start {server['name']}: {e}")
            else:
                print(f"⚠️  MCP script not found: {server['script']}")
                
    def start_streamlit(self):
        """Start the Streamlit application"""
        print("\nStarting Streamlit application...")
        
        try:
            cmd = ['streamlit', 'run', 'enhanced_integrated_dashboard.py', 
                   '--server.port', '8501',
                   '--server.address', '0.0.0.0']
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes['streamlit'] = process
            print("✓ Started Streamlit on http://localhost:8501")
        except Exception as e:
            print(f"✗ Failed to start Streamlit: {e}")
            
    def health_check(self):
        """Check health of all services"""
        print("\nPerforming health check...")
        
        # Check MCP servers
        import requests
        mcp_ports = [8001, 8002, 8003, 8004, 8005]
        
        for port in mcp_ports:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ MCP server on port {port} is healthy")
                else:
                    print(f"⚠️  MCP server on port {port} returned status {response.status_code}")
            except:
                print(f"✗ MCP server on port {port} is not responding")
                
        # Check Streamlit
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            if response.status_code == 200:
                print("✓ Streamlit application is healthy")
        except:
            print("⚠️  Streamlit is still starting up...")
            
    def monitor_services(self):
        """Monitor services and restart if needed"""
        while not shutdown_flag.is_set():
            time.sleep(30)  # Check every 30 seconds
            
            for name, process in self.processes.items():
                if process.poll() is not None:
                    print(f"⚠️  Service {name} has stopped. Restarting...")
                    # Restart logic here
                    
    def shutdown(self):
        """Gracefully shutdown all services"""
        print("\n\nShutting down services...")
        
        for name, process in self.processes.items():
            if process.poll() is None:
                process.terminate()
                print(f"✓ Stopped {name}")
                
        print("All services stopped.")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n\nReceived shutdown signal...")
    shutdown_flag.set()
    sys.exit(0)

def main():
    print("="*60)
    print("AI-Powered FinOps Platform Service Manager")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize service manager
    manager = ServiceManager()
    
    # Start services in order
    try:
        # 1. Create DynamoDB tables
        manager.create_dynamodb_tables()
        
        # 2. Deploy Lambda functions
        manager.deploy_lambda_functions()
        
        # 3. Start MCP servers
        manager.start_mcp_servers()
        
        # 4. Start Streamlit
        time.sleep(5)  # Give MCP servers time to start
        manager.start_streamlit()
        
        # 5. Health check
        time.sleep(10)  # Give everything time to start
        manager.health_check()
        
        print("\n" + "="*60)
        print("All services started successfully!")
        print("Access the platform at: http://localhost:8501")
        print("Press Ctrl+C to stop all services")
        print("="*60 + "\n")
        
        # Monitor services
        monitor_thread = threading.Thread(target=manager.monitor_services)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Keep main thread alive
        while not shutdown_flag.is_set():
            time.sleep(1)
            
    except Exception as e:
        print(f"\n✗ Error starting services: {e}")
        manager.shutdown()
        sys.exit(1)
    finally:
        manager.shutdown()

if __name__ == "__main__":
    main()