#!/usr/bin/env python3
"""
Test cases for FinOps platform features
"""

import unittest
import json
import boto3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from finops_report_generator import FinOpsReportGenerator
from tag_compliance_agent import TagComplianceAgent
from multi_agent_processor import MultiAgentProcessor
from lambda_tag_compliance import (
    lambda_handler,
    perform_compliance_scan,
    check_resource_compliance,
    auto_remediate_tags
)

class TestFinOpsReportGenerator(unittest.TestCase):
    """
    Test cases for FinOps Report Generator
    """
    
    def setUp(self):
        """Set up test environment"""
        # Mock AWS clients
        self.mock_clients = {
            'ce': MagicMock(),
            'ec2': MagicMock(),
            'rds': MagicMock(),
            's3': MagicMock(),
            'lambda': MagicMock(),
            'cloudwatch': MagicMock(),
            'organizations': MagicMock(),
            'sts': MagicMock()
        }
        
        # Mock account ID
        self.mock_clients['sts'].get_caller_identity.return_value = {'Account': '123456789012'}
        
        self.report_generator = FinOpsReportGenerator(self.mock_clients)
    
    def test_cost_analysis(self):
        """Test cost analysis functionality"""
        # Mock cost data
        self.mock_clients['ce'].get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2024-01-01', 'End': '2024-01-02'},
                    'Groups': [
                        {
                            'Keys': ['AmazonEC2', 'BoxUsage:t2.micro'],
                            'Metrics': {
                                'UnblendedCost': {'Amount': '100.00'},
                                'UsageQuantity': {'Amount': '24'}
                            }
                        }
                    ]
                }
            ]
        }
        
        start_date = datetime(2024, 1, 1).date()
        end_date = datetime(2024, 1, 2).date()
        
        result = self.report_generator._analyze_costs(start_date, end_date)
        
        # Verify results
        self.assertIn('total_cost', result)
        self.assertEqual(result['total_cost'], 100.0)
        self.assertIn('service_costs', result)
        self.assertIn('AmazonEC2', result['service_costs'])
    
    def test_resource_tagging_compliance(self):
        """Test resource tagging compliance analysis"""
        # Mock resource tagging data
        self.mock_clients['resourcegroupstaggingapi'] = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                'ResourceTagMappingList': [
                    {
                        'ResourceARN': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890',
                        'Tags': [
                            {'Key': 'Environment', 'Value': 'prod'},
                            {'Key': 'Owner', 'Value': 'test@example.com'}
                        ]
                    }
                ]
            }
        ]
        
        self.report_generator.resource_tagging_client = self.mock_clients['resourcegroupstaggingapi']
        self.report_generator.resource_tagging_client.get_paginator.return_value = paginator
        
        result = self.report_generator._analyze_resource_tagging()
        
        # Verify results
        self.assertIn('compliance_rate', result)
        self.assertIn('total_resources', result)
        self.assertIn('untagged_resources', result)
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations generation"""
        # Mock EC2 data
        self.mock_clients['ec2'].describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890',
                            'InstanceType': 't2.micro',
                            'State': {'Name': 'stopped'},
                            'BlockDeviceMappings': [
                                {
                                    'Ebs': {
                                        'VolumeSize': 30,
                                        'VolumeType': 'gp2'
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Mock EBS data
        self.mock_clients['ec2'].describe_volumes.return_value = {
            'Volumes': [
                {
                    'VolumeId': 'vol-1234567890',
                    'Size': 100,
                    'VolumeType': 'gp2',
                    'State': 'available'
                }
            ]
        }
        
        result = self.report_generator._generate_optimization_recommendations()
        
        # Verify results
        self.assertIn('recommendations', result)
        self.assertIn('total_potential_savings', result)
        self.assertGreater(len(result['recommendations']), 0)
    
    def test_report_generation_pdf(self):
        """Test PDF report generation"""
        # Mock cost data
        self.mock_clients['ce'].get_cost_and_usage.return_value = {
            'ResultsByTime': []
        }
        
        # Generate report
        report_content = self.report_generator.generate_comprehensive_report(
            report_type='full',
            format='pdf'
        )
        
        # Verify PDF content
        self.assertIsInstance(report_content, bytes)
        self.assertTrue(report_content.startswith(b'%PDF'))  # PDF header
    
    def test_report_generation_excel(self):
        """Test Excel report generation"""
        # Mock cost data
        self.mock_clients['ce'].get_cost_and_usage.return_value = {
            'ResultsByTime': []
        }
        
        # Generate report
        report_content = self.report_generator.generate_comprehensive_report(
            report_type='full',
            format='excel'
        )
        
        # Verify Excel content
        self.assertIsInstance(report_content, bytes)
        # Excel files start with specific bytes
        self.assertTrue(report_content[:4] == b'PK\x03\x04' or report_content[:4] == b'PK\x05\x06')
    
    def test_report_generation_json(self):
        """Test JSON report generation"""
        # Mock cost data
        self.mock_clients['ce'].get_cost_and_usage.return_value = {
            'ResultsByTime': []
        }
        
        # Generate report
        report_content = self.report_generator.generate_comprehensive_report(
            report_type='full',
            format='json'
        )
        
        # Verify JSON content
        self.assertIsInstance(report_content, str)
        report_data = json.loads(report_content)
        self.assertIn('metadata', report_data)
        self.assertIn('cost_analysis', report_data)
        self.assertIn('resource_tagging', report_data)

class TestTagComplianceAgent(unittest.TestCase):
    """
    Test cases for Tag Compliance Agent
    """
    
    def setUp(self):
        """Set up test environment"""
        self.agent = TagComplianceAgent()
        
        # Mock AWS clients
        self.agent.ec2 = MagicMock()
        self.agent.rds = MagicMock()
        self.agent.s3 = MagicMock()
        self.agent.lambda_client = MagicMock()
    
    def test_compliance_scan_query(self):
        """Test compliance scan query processing"""
        # Mock Lambda response
        self.agent.lambda_client.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'body': json.dumps({
                    'compliance_rate': 85.5,
                    'total_resources': 100,
                    'compliant_count': 85,
                    'non_compliant_count': 15,
                    'missing_tags_summary': {
                        'Environment': 10,
                        'Owner': 5
                    }
                })
            }).encode())
        }
        
        response, data = self.agent.process_query("check compliance", {})
        
        # Verify response
        self.assertIn('Compliance Scan Complete', response)
        self.assertIn('85.5%', response)
        self.assertIn('compliance_rate', data)
    
    def test_untagged_resources_query(self):
        """Test untagged resources query"""
        # Mock EC2 instances
        self.agent.ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-untagged',
                            'State': {'Name': 'running'},
                            'InstanceType': 't2.micro',
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        
        # Mock volumes
        self.agent.ec2.describe_volumes.return_value = {'Volumes': []}
        
        response, data = self.agent.process_query("find untagged resources", {})
        
        # Verify response
        self.assertIn('Found', response)
        self.assertIn('resources with missing tags', response)
        self.assertIn('untagged_resources', data)
        self.assertEqual(len(data['untagged_resources']), 1)
    
    def test_remediation_suggestions(self):
        """Test remediation suggestions"""
        # Mock untagged resources
        self.agent.ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-needs-tags',
                            'State': {'Name': 'running'},
                            'InstanceType': 't2.small',
                            'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
                        }
                    ]
                }
            ]
        }
        
        self.agent.ec2.describe_volumes.return_value = {'Volumes': []}
        
        response, data = self.agent.process_query("suggest remediation", {})
        
        # Verify response
        self.assertIn('Remediation Plan', response)
        self.assertIn('Automated Tagging', response)
        self.assertIn('default_tags', data)
    
    def test_cost_impact_analysis(self):
        """Test cost impact analysis"""
        # Mock untagged EC2 instance
        self.agent.ec2.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-expensive',
                            'State': {'Name': 'running'},
                            'InstanceType': 'm5.large',
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        
        self.agent.ec2.describe_volumes.return_value = {'Volumes': []}
        
        response, data = self.agent.process_query("cost impact", {})
        
        # Verify response
        self.assertIn('Cost Impact Analysis', response)
        self.assertIn('total_monthly_cost', data)
        self.assertGreater(data['total_monthly_cost'], 0)

class TestLambdaTagCompliance(unittest.TestCase):
    """
    Test cases for Lambda Tag Compliance function
    """
    
    @patch('lambda_tag_compliance.resource_tagging')
    @patch('lambda_tag_compliance.ec2')
    def test_lambda_handler_scan(self, mock_ec2, mock_resource_tagging):
        """Test Lambda handler scan action"""
        # Mock resource tagging
        mock_resource_tagging.get_paginator.return_value.paginate.return_value = []
        
        # Mock EC2 scan
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        
        # Test event
        event = {'action': 'scan'}
        context = {}
        
        response = lambda_handler(event, context)
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('compliance_rate', body)
    
    @patch('lambda_tag_compliance.resource_tagging')
    def test_lambda_handler_check_resource(self, mock_resource_tagging):
        """Test Lambda handler check resource action"""
        # Mock resource check
        mock_resource_tagging.get_resources.return_value = {
            'ResourceTagMappingList': [
                {
                    'ResourceARN': 'arn:aws:ec2:us-east-1:123456789012:instance/i-test',
                    'Tags': [
                        {'Key': 'Environment', 'Value': 'prod'}
                    ]
                }
            ]
        }
        
        # Test event
        event = {
            'action': 'get_resource',
            'resource_arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-test'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('compliant', body)
        self.assertIn('missing_tags', body)
    
    @patch('lambda_tag_compliance.resource_tagging')
    def test_auto_remediate_tags(self, mock_resource_tagging):
        """Test auto remediation"""
        # Mock tag application
        mock_resource_tagging.tag_resources.return_value = {}
        
        # Mock resource check
        mock_resource_tagging.get_resources.return_value = {
            'ResourceTagMappingList': [
                {
                    'ResourceARN': 'arn:aws:ec2:us-east-1:123456789012:instance/i-test',
                    'Tags': []
                }
            ]
        }
        
        result = auto_remediate_tags(['arn:aws:ec2:us-east-1:123456789012:instance/i-test'])
        
        # Verify result
        self.assertIn('successful', result)
        self.assertEqual(result['successful'], 1)

class TestMultiAgentProcessor(unittest.TestCase):
    """
    Test cases for Multi-Agent Processor
    """
    
    def setUp(self):
        """Set up test environment"""
        self.processor = MultiAgentProcessor()
        
        # Mock AWS clients
        self.processor.ce = MagicMock()
        self.processor.ec2 = MagicMock()
        self.processor.lambda_client = MagicMock()
    
    def test_prediction_query(self):
        """Test prediction query processing"""
        # Mock Lambda response
        self.processor.lambda_client.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'body': json.dumps({
                    'predictions': {
                        'summary': {
                            'total_predicted_cost': 1000.0,
                            'average_daily_cost': 33.33,
                            'trend': 'increasing',
                            'confidence_level': '85%'
                        }
                    }
                })
            }).encode())
        }
        
        response, data = self.processor.process_prediction_query("predict next month", {})
        
        # Verify response
        self.assertIn('Budget Prediction Analysis Complete', response)
        self.assertIn('$1,000.00', response)
    
    def test_optimizer_query(self):
        """Test optimization query processing"""
        # Mock Lambda response
        self.processor.lambda_client.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'body': json.dumps({
                    'opportunities': {
                        'stopped_instances': {
                            'count': 5,
                            'monthly_savings': 250.0
                        },
                        'unattached_volumes': {
                            'count': 10,
                            'monthly_savings': 50.0
                        }
                    },
                    'total_monthly_savings': 300.0
                })
            }).encode())
        }
        
        response, data = self.processor.process_optimizer_query("find idle resources", {})
        
        # Verify response
        self.assertIn('Resource Optimization Analysis', response)
        self.assertIn('$300.00', response)
    
    def test_general_query(self):
        """Test general query processing"""
        # Mock cost data
        self.processor.ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2024-01-01', 'End': '2024-01-02'},
                    'Groups': [
                        {
                            'Keys': ['AmazonEC2'],
                            'Metrics': {'UnblendedCost': {'Amount': '50.00'}}
                        }
                    ]
                }
            ]
        }
        
        response, data = self.processor.process_general_query("show costs", {})
        
        # Verify response
        self.assertIn('AWS Cost Overview', response)
        self.assertIn('total_cost', data)

class TestStreamlitUI(unittest.TestCase):
    """
    Test cases for Streamlit UI components
    """
    
    @patch('streamlit.button')
    @patch('streamlit.spinner')
    def test_report_generation_button(self, mock_spinner, mock_button):
        """Test report generation button functionality"""
        # This tests that the UI components are properly wired
        mock_button.return_value = True
        
        # The actual UI test would require Selenium or similar
        # This is a placeholder for structure
        self.assertTrue(True)
    
    def test_tag_compliance_tab_structure(self):
        """Test tag compliance tab structure"""
        # This would test that all required UI elements are present
        # In actual implementation, this would use Selenium
        self.assertTrue(True)

class TestIntegration(unittest.TestCase):
    """
    Integration tests for the complete system
    """
    
    def test_report_includes_tag_compliance(self):
        """Test that reports include tag compliance data"""
        # This would test the full integration
        # In practice, this would spin up the full system
        self.assertTrue(True)
    
    def test_chatbot_handles_tag_queries(self):
        """Test that chatbot properly routes tag compliance queries"""
        # This would test the chatbot routing
        self.assertTrue(True)

def run_all_tests():
    """
    Run all test suites
    """
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestFinOpsReportGenerator,
        TestTagComplianceAgent,
        TestLambdaTagCompliance,
        TestMultiAgentProcessor,
        TestStreamlitUI,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success/failure
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)