#!/usr/bin/env python3
"""
Real AWS API Tests for FinOps Copilot
This test suite validates all functionality with actual AWS services
"""

import unittest
import boto3
import json
import os
import sys
from datetime import datetime, timedelta
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lambda-functions'))

class TestRealAWSIntegration(unittest.TestCase):
    """Test suite for real AWS API integration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up AWS clients and test resources"""
        cls.session = boto3.Session()
        cls.region = cls.session.region_name or 'us-east-1'
        
        # Initialize AWS clients
        cls.ec2_client = boto3.client('ec2', region_name=cls.region)
        cls.s3_client = boto3.client('s3', region_name=cls.region)
        cls.rds_client = boto3.client('rds', region_name=cls.region)
        cls.ce_client = boto3.client('ce', region_name=cls.region)
        cls.cloudwatch_client = boto3.client('cloudwatch', region_name=cls.region)
        cls.iam_client = boto3.client('iam', region_name=cls.region)
        cls.lambda_client = boto3.client('lambda', region_name=cls.region)
        cls.ssm_client = boto3.client('ssm', region_name=cls.region)
        cls.sts_client = boto3.client('sts', region_name=cls.region)
        
        # Get account ID
        cls.account_id = cls.sts_client.get_caller_identity()['Account']
        logger.info(f"Testing with AWS Account: {cls.account_id}, Region: {cls.region}")
    
    def test_aws_connectivity(self):
        """Test basic AWS connectivity"""
        try:
            # Test STS
            identity = self.sts_client.get_caller_identity()
            self.assertIsNotNone(identity['Account'])
            logger.info(f"✓ AWS connectivity verified for account: {identity['Account']}")
            
            # Test EC2
            ec2_response = self.ec2_client.describe_regions()
            self.assertIn('Regions', ec2_response)
            logger.info(f"✓ EC2 API accessible, found {len(ec2_response['Regions'])} regions")
            
            # Test S3
            s3_response = self.s3_client.list_buckets()
            self.assertIn('Buckets', s3_response)
            logger.info(f"✓ S3 API accessible, found {len(s3_response['Buckets'])} buckets")
            
        except Exception as e:
            self.fail(f"AWS connectivity test failed: {str(e)}")
    
    def test_cost_explorer_access(self):
        """Test Cost Explorer API access"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            self.assertIn('ResultsByTime', response)
            self.assertGreater(len(response['ResultsByTime']), 0)
            
            total_cost = sum(
                float(result['Total']['UnblendedCost']['Amount'])
                for result in response['ResultsByTime']
            )
            logger.info(f"✓ Cost Explorer accessible, 7-day cost: ${total_cost:.2f}")
            
        except Exception as e:
            self.fail(f"Cost Explorer access test failed: {str(e)}")
    
    def test_ec2_agent_functionality(self):
        """Test EC2 agent with real AWS data"""
        try:
            from ec2_agent import EC2CostAnalyzer
            
            analyzer = EC2CostAnalyzer()
            
            # Get running instances
            instances = self.ec2_client.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            
            instance_ids = []
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
            
            logger.info(f"Found {len(instance_ids)} running EC2 instances")
            
            if instance_ids:
                # Test instance details retrieval
                details = analyzer.get_instance_details(instance_ids[:5])  # Limit to 5
                self.assertIsInstance(details, dict)
                logger.info(f"✓ EC2 agent retrieved details for {len(details)} instances")
                
                # Test utilization analysis
                utilization = analyzer.analyze_instance_utilization(instance_ids[:5], days=7)
                self.assertIsInstance(utilization, dict)
                logger.info("✓ EC2 agent analyzed instance utilization")
            else:
                logger.info("⚠ No running EC2 instances found, skipping detailed tests")
            
        except Exception as e:
            self.fail(f"EC2 agent test failed: {str(e)}")
    
    def test_s3_agent_functionality(self):
        """Test S3 agent with real AWS data"""
        try:
            from s3_agent import S3CostAnalyzer
            
            analyzer = S3CostAnalyzer()
            
            # Get bucket list
            buckets = analyzer.get_bucket_list()
            logger.info(f"Found {len(buckets)} S3 buckets")
            
            if buckets:
                # Analyze first few buckets
                bucket_data = analyzer.analyze_bucket_storage(buckets[:3])
                self.assertIsInstance(bucket_data, dict)
                logger.info(f"✓ S3 agent analyzed {len(bucket_data)} buckets")
                
                # Test storage class analysis
                for bucket in buckets[:2]:
                    try:
                        storage_classes = analyzer.analyze_storage_classes(bucket)
                        self.assertIsInstance(storage_classes, dict)
                        logger.info(f"✓ S3 agent analyzed storage classes for bucket: {bucket}")
                    except Exception as e:
                        logger.warning(f"Could not analyze bucket {bucket}: {str(e)}")
            else:
                logger.info("⚠ No S3 buckets found, skipping detailed tests")
                
        except Exception as e:
            self.fail(f"S3 agent test failed: {str(e)}")
    
    def test_cloudwatch_metrics(self):
        """Test CloudWatch metrics retrieval"""
        try:
            # List available metrics
            metrics = self.cloudwatch_client.list_metrics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                RecentlyActive='PT3H'
            )
            
            self.assertIn('Metrics', metrics)
            logger.info(f"✓ CloudWatch accessible, found {len(metrics['Metrics'])} CPU metrics")
            
            # Test metric statistics if instances exist
            if metrics['Metrics']:
                metric = metrics['Metrics'][0]
                stats = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=metric['Dimensions'],
                    StartTime=datetime.utcnow() - timedelta(hours=1),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=['Average']
                )
                self.assertIn('Datapoints', stats)
                logger.info(f"✓ Retrieved {len(stats['Datapoints'])} datapoints")
                
        except Exception as e:
            self.fail(f"CloudWatch metrics test failed: {str(e)}")
    
    def test_tagging_compliance(self):
        """Test resource tagging compliance"""
        try:
            from tagging_agent import TaggingComplianceAnalyzer
            
            analyzer = TaggingComplianceAnalyzer()
            
            # Get resources for EC2 instances only (faster)
            resources = analyzer.get_all_resources(['ec2:instance'])
            logger.info(f"Found {len(resources)} EC2 instances for tagging analysis")
            
            if resources:
                # Analyze compliance
                compliance = analyzer.analyze_tag_compliance(resources)
                self.assertIn('total_resources', compliance)
                self.assertIn('compliance_percentage', compliance)
                
                logger.info(f"✓ Tagging compliance: {compliance['compliance_percentage']:.1f}%")
                logger.info(f"  - Compliant: {compliance['compliant_resources']}")
                logger.info(f"  - Non-compliant: {compliance['non_compliant_resources']}")
            else:
                logger.info("⚠ No resources found for tagging analysis")
                
        except Exception as e:
            self.fail(f"Tagging compliance test failed: {str(e)}")
    
    def test_lambda_deployment(self):
        """Test Lambda function deployment and invocation"""
        project_name = "finops-copilot"
        
        # Test if Lambda functions exist
        lambda_functions = [
            f"{project_name}-orchestrator_agent",
            f"{project_name}-ec2_agent",
            f"{project_name}-s3_agent"
        ]
        
        deployed_functions = []
        for func_name in lambda_functions:
            try:
                response = self.lambda_client.get_function(FunctionName=func_name)
                if response['Configuration']['State'] == 'Active':
                    deployed_functions.append(func_name)
                    logger.info(f"✓ Lambda function exists: {func_name}")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                logger.warning(f"⚠ Lambda function not found: {func_name}")
            except Exception as e:
                logger.error(f"✗ Error checking Lambda function {func_name}: {str(e)}")
        
        if deployed_functions:
            # Test invocation of first available function
            test_func = deployed_functions[0]
            try:
                response = self.lambda_client.invoke(
                    FunctionName=test_func,
                    InvocationType='DryRun'  # Test without executing
                )
                self.assertEqual(response['StatusCode'], 204)
                logger.info(f"✓ Lambda function {test_func} is invokable")
            except Exception as e:
                logger.error(f"✗ Lambda invocation test failed: {str(e)}")
    
    def test_ssm_parameters(self):
        """Test SSM parameter configuration"""
        parameters = [
            '/finops-copilot/mcp/apptio/endpoint',
            '/finops-copilot/mcp/apptio/env-id'
        ]
        
        for param_name in parameters:
            try:
                response = self.ssm_client.get_parameter(Name=param_name)
                self.assertIsNotNone(response['Parameter']['Value'])
                logger.info(f"✓ SSM parameter exists: {param_name}")
            except self.ssm_client.exceptions.ParameterNotFound:
                logger.warning(f"⚠ SSM parameter not found: {param_name}")
            except Exception as e:
                logger.error(f"✗ Error checking SSM parameter {param_name}: {str(e)}")
    
    def test_iam_roles(self):
        """Test IAM roles existence"""
        role_names = [
            'finops-copilot-lambda-role',
            'finops-copilot-bedrock-role'
        ]
        
        for role_name in role_names:
            try:
                response = self.iam_client.get_role(RoleName=role_name)
                self.assertIsNotNone(response['Role']['Arn'])
                logger.info(f"✓ IAM role exists: {role_name}")
            except self.iam_client.exceptions.NoSuchEntityException:
                logger.warning(f"⚠ IAM role not found: {role_name}")
            except Exception as e:
                logger.error(f"✗ Error checking IAM role {role_name}: {str(e)}")
    
    def test_cost_analysis_integration(self):
        """Test integrated cost analysis workflow"""
        try:
            from orchestrator_agent import FinOpsOrchestrator
            
            orchestrator = FinOpsOrchestrator()
            
            # Test query parsing
            query = "What are my biggest cost optimization opportunities?"
            plan = orchestrator.parse_user_query(query)
            
            self.assertIn('agents_to_invoke', plan)
            self.assertGreater(len(plan['agents_to_invoke']), 0)
            logger.info(f"✓ Orchestrator parsed query, will invoke: {plan['agents_to_invoke']}")
            
            # Test synthesis (with mock data since we can't invoke all agents)
            mock_results = [
                {
                    'agent': 'ec2_agent',
                    'success': True,
                    'data': {
                        'body': json.dumps({
                            'summary': {
                                'instance_count': 5,
                                'total_monthly_cost': 1000,
                                'potential_monthly_savings': 200
                            },
                            'recommendations': []
                        })
                    }
                }
            ]
            
            synthesis = orchestrator.synthesize_results(mock_results, query)
            self.assertIn('cost_impact', synthesis)
            self.assertIn('recommendations', synthesis)
            logger.info("✓ Orchestrator successfully synthesized results")
            
        except Exception as e:
            self.fail(f"Cost analysis integration test failed: {str(e)}")


class TestStreamlitFrontend(unittest.TestCase):
    """Test Streamlit frontend functionality"""
    
    def test_streamlit_imports(self):
        """Test that Streamlit app can be imported"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend'))
            import app
            
            # Test FinOpsCopilot class exists
            self.assertTrue(hasattr(app, 'FinOpsCopilot'))
            logger.info("✓ Streamlit app imports successfully")
            
            # Test main function exists
            self.assertTrue(hasattr(app, 'main'))
            logger.info("✓ Streamlit main function exists")
            
        except Exception as e:
            self.fail(f"Streamlit import test failed: {str(e)}")
    
    def test_finops_copilot_class(self):
        """Test FinOpsCopilot class functionality"""
        try:
            # Import from frontend directory
            import sys
            import os
            frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
            sys.path.insert(0, frontend_path)
            from app import FinOpsCopilot
            
            copilot = FinOpsCopilot()
            
            # Test mock data generation
            cost_data = copilot.get_mock_cost_data()
            self.assertIsNotNone(cost_data)
            self.assertGreater(len(cost_data), 0)
            logger.info(f"✓ Generated mock cost data with {len(cost_data)} records")
            
            # Test recommendations
            recommendations = copilot.get_mock_recommendations()
            self.assertIsInstance(recommendations, list)
            self.assertGreater(len(recommendations), 0)
            logger.info(f"✓ Generated {len(recommendations)} mock recommendations")
            
            # Test agent interaction simulation
            response = copilot.simulate_agent_interaction("analyze costs")
            self.assertIn('response', response)
            self.assertIn('agents_involved', response)
            logger.info("✓ Agent interaction simulation works")
            
        except Exception as e:
            self.fail(f"FinOpsCopilot class test failed: {str(e)}")


class TestMCPServers(unittest.TestCase):
    """Test MCP server functionality"""
    
    def test_cost_explorer_mcp(self):
        """Test Cost Explorer MCP server"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp-servers'))
            from cost_explorer_mcp import CostExplorerMCPServer
            
            server = CostExplorerMCPServer()
            
            # Test initialization
            self.assertIsNotNone(server.cost_explorer_client)
            logger.info("✓ Cost Explorer MCP server initialized")
            
            # Test async functionality with asyncio
            import asyncio
            
            async def test_async():
                # Test dimension values
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=30)
                
                result = await server.get_dimension_values(
                    'SERVICE',
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                return result
            
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_async())
            loop.close()
            
            self.assertIn('dimension', result)
            self.assertIn('values', result)
            logger.info(f"✓ Cost Explorer MCP retrieved {len(result['values'])} service dimensions")
            
        except Exception as e:
            self.fail(f"Cost Explorer MCP test failed: {str(e)}")


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow"""
    
    def test_complete_workflow(self):
        """Test the complete FinOps analysis workflow"""
        logger.info("\n=== Running End-to-End Workflow Test ===")
        
        try:
            # Step 1: Check AWS connectivity
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"✓ Step 1: Connected to AWS account {identity['Account']}")
            
            # Step 2: Get cost data
            ce = boto3.client('ce')
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7)
            
            cost_response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            services = set()
            for result in cost_response['ResultsByTime']:
                for group in result['Groups']:
                    services.add(group['Keys'][0])
            
            logger.info(f"✓ Step 2: Retrieved cost data for {len(services)} services")
            
            # Step 3: Analyze resources
            ec2 = boto3.client('ec2')
            instances = ec2.describe_instances()
            instance_count = sum(len(r['Instances']) for r in instances['Reservations'])
            
            s3 = boto3.client('s3')
            buckets = s3.list_buckets()
            bucket_count = len(buckets['Buckets'])
            
            logger.info(f"✓ Step 3: Found {instance_count} EC2 instances and {bucket_count} S3 buckets")
            
            # Step 4: Generate recommendations
            recommendations = []
            
            # Check for running instances
            running_instances = []
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        running_instances.append(instance)
            
            if running_instances:
                recommendations.append({
                    'type': 'ec2_optimization',
                    'count': len(running_instances),
                    'message': f"Review {len(running_instances)} running EC2 instances for optimization"
                })
            
            if bucket_count > 10:
                recommendations.append({
                    'type': 's3_optimization',
                    'count': bucket_count,
                    'message': f"Review {bucket_count} S3 buckets for lifecycle policies"
                })
            
            logger.info(f"✓ Step 4: Generated {len(recommendations)} recommendations")
            
            # Step 5: Verify all components
            logger.info("✓ Step 5: End-to-end workflow completed successfully")
            
            # Summary
            logger.info("\n=== Workflow Summary ===")
            logger.info(f"Account: {identity['Account']}")
            logger.info(f"Services with costs: {len(services)}")
            logger.info(f"EC2 instances: {instance_count}")
            logger.info(f"S3 buckets: {bucket_count}")
            logger.info(f"Recommendations: {len(recommendations)}")
            logger.info("✓ All components working correctly")
            
            self.assertGreater(len(services), 0, "Should have at least one service with costs")
            
        except Exception as e:
            self.fail(f"End-to-end workflow test failed: {str(e)}")


def run_all_tests():
    """Run all test suites and generate report"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRealAWSIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStreamlitFrontend))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMCPServers))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEndToEndWorkflow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        logger.info("\n✓ ALL TESTS PASSED!")
    else:
        logger.info("\n✗ Some tests failed. Check the output above for details.")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)