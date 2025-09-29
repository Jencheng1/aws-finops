import unittest
from unittest.mock import patch, MagicMock, call
import json
import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the lambda-functions directory to the path
lambda_functions_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'lambda-functions'
)
sys.path.insert(0, lambda_functions_path)

# Import the orchestrator module
import orchestrator_agent
from orchestrator_agent import lambda_handler, FinOpsOrchestrator

class TestFinOpsOrchestratorE2E(unittest.TestCase):
    """End-to-end test cases for the FinOps Orchestrator."""

    def setUp(self):
        """Set up test fixtures for E2E testing."""
        self.maxDiff = None
        
        # User query for comprehensive analysis
        self.comprehensive_query = "What are my biggest AWS cost optimization opportunities across all services?"
        
        # Mock responses from various agents
        self.ec2_agent_response = {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'analyze_all',
                'summary': {
                    'instance_count': 25,
                    'total_monthly_cost': 5000,
                    'potential_monthly_savings': 1500,
                    'high_priority_recommendations': 3,
                    'total_recommendations': 8
                },
                'recommendations': [
                    {
                        'type': 'right_sizing',
                        'instance_id': 'i-1234567890',
                        'instance_type': 't3.2xlarge',
                        'recommendation': 'Downsize to t3.large - CPU utilization only 15%',
                        'priority': 'high',
                        'estimated_monthly_savings': 800
                    },
                    {
                        'type': 'idle_instance',
                        'instance_id': 'i-0987654321',
                        'recommendation': 'Terminate idle instance - no connections for 30 days',
                        'priority': 'high',
                        'estimated_monthly_savings': 400
                    }
                ]
            })
        }
        
        self.s3_agent_response = {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'analyze_all',
                'summary': {
                    'bucket_count': 15,
                    'total_size_gb': 5000,
                    'total_monthly_cost': 2000,
                    'potential_monthly_savings': 600,
                    'high_priority_recommendations': 2,
                    'total_recommendations': 5
                },
                'recommendations': [
                    {
                        'type': 'storage_class_optimization',
                        'bucket_name': 'data-archive-bucket',
                        'size_gb': 2000,
                        'recommendation': 'Enable S3 Intelligent-Tiering for infrequently accessed data',
                        'priority': 'high',
                        'estimated_monthly_savings': 400
                    }
                ]
            })
        }
        
        self.rds_agent_response = {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'analyze_all',
                'summary': {
                    'instance_count': 8,
                    'total_monthly_cost': 3000,
                    'potential_monthly_savings': 900,
                    'high_priority_recommendations': 2,
                    'total_recommendations': 4
                },
                'recommendations': [
                    {
                        'type': 'idle_instance',
                        'instance_id': 'db-prod-analytics',
                        'recommendation': 'No connections detected - consider stopping',
                        'priority': 'high',
                        'estimated_monthly_savings': 500
                    }
                ]
            })
        }
        
        self.ri_sp_agent_response = {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'analyze_all',
                'summary': {
                    'potential_monthly_savings': 2000,
                    'high_priority_recommendations': 1,
                    'total_recommendations': 3,
                    'ri_average_utilization': 65,
                    'sp_average_utilization': 80
                },
                'recommendations': [
                    {
                        'type': 'ri_purchase_opportunity',
                        'recommendation': 'Purchase Reserved Instances for consistent EC2 workloads',
                        'priority': 'high',
                        'estimated_monthly_savings': 2000
                    }
                ]
            })
        }
        
        self.tagging_agent_response = {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'analyze_all',
                'summary': {
                    'total_resources': 150,
                    'compliance_percentage': 72,
                    'non_compliant_resources': 42,
                    'monthly_untagged_cost': 1500,
                    'high_priority_recommendations': 1,
                    'total_recommendations': 3
                },
                'recommendations': [
                    {
                        'type': 'tagging_compliance',
                        'recommendation': '42 resources missing required tags affecting cost allocation',
                        'priority': 'medium'
                    }
                ]
            })
        }
        
        self.apptio_integration_response = {
            'statusCode': 200,
            'body': json.dumps({
                'apptio_insights': {
                    'budget_variance': '+15%',
                    'forecast_accuracy': 'High',
                    'cost_allocation_gaps': '28% of costs unallocated'
                },
                'combined_analysis': {
                    'total_identified_savings': 7000,
                    'confidence_score': 0.92,
                    'opportunity_areas': [
                        {
                            'type': 'cross-service-optimization',
                            'description': 'Consolidated savings across EC2, S3, and RDS'
                        }
                    ]
                }
            })
        }

    @patch('lambda_functions.orchestrator_agent.boto3.client')
    def test_comprehensive_cost_analysis_e2e(self, mock_boto3_client):
        """Test end-to-end flow of comprehensive cost analysis."""
        # Configure mock Lambda client
        mock_lambda = MagicMock()
        mock_boto3_client.return_value = mock_lambda
        
        # Configure Lambda invoke responses
        def lambda_invoke_side_effect(**kwargs):
            function_name = kwargs['FunctionName']
            response = MagicMock()
            response['StatusCode'] = 200
            
            # Return appropriate response based on function name
            if 'ec2-agent' in function_name:
                response['Payload'].read.return_value = json.dumps(self.ec2_agent_response)
            elif 's3-agent' in function_name:
                response['Payload'].read.return_value = json.dumps(self.s3_agent_response)
            elif 'rds-agent' in function_name:
                response['Payload'].read.return_value = json.dumps(self.rds_agent_response)
            elif 'ri-sp-agent' in function_name:
                response['Payload'].read.return_value = json.dumps(self.ri_sp_agent_response)
            elif 'tagging-agent' in function_name:
                response['Payload'].read.return_value = json.dumps(self.tagging_agent_response)
            elif 'apptio-integration' in function_name:
                response['Payload'].read.return_value = json.dumps(self.apptio_integration_response)
            else:
                response['Payload'].read.return_value = json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({'summary': {}, 'recommendations': []})
                })
            
            return response
        
        mock_lambda.invoke.side_effect = lambda_invoke_side_effect
        
        # Prepare event
        event = {
            'query': self.comprehensive_query,
            'days': 30,
            'depth': 'detailed'
        }
        
        # Call the orchestrator
        result = lambda_handler(event, {})
        
        # Basic assertions
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        
        # Verify query processing
        self.assertEqual(body['query'], self.comprehensive_query)
        self.assertIn('natural_response', body)
        self.assertIn('detailed_analysis', body)
        
        # Verify all agents were invoked
        detailed_analysis = body['detailed_analysis']
        self.assertIn('agents_consulted', detailed_analysis)
        expected_agents = ['ec2_agent', 's3_agent', 'rds_agent', 'ri_sp_agent', 'tagging_agent']
        for agent in expected_agents:
            self.assertIn(agent, detailed_analysis['agents_consulted'])
        
        # Verify cost summary
        self.assertIn('cost_impact', detailed_analysis)
        cost_impact = detailed_analysis['cost_impact']
        self.assertGreater(cost_impact['current_monthly_cost'], 0)
        self.assertGreater(cost_impact['potential_monthly_savings'], 0)
        self.assertGreater(cost_impact['savings_percentage'], 0)
        
        # Verify recommendations were aggregated
        self.assertIn('recommendations', detailed_analysis)
        recommendations = detailed_analysis['recommendations']
        self.assertGreater(len(recommendations), 0)
        
        # Verify high priority recommendations are first
        high_priority_recs = [r for r in recommendations if r.get('priority') == 'high']
        self.assertGreater(len(high_priority_recs), 0)
        
        # Verify Apptio insights were included
        self.assertIn('apptio_insights', detailed_analysis)
        apptio_insights = detailed_analysis['apptio_insights']
        self.assertIn('budget_variance', apptio_insights)
        self.assertIn('forecast_accuracy', apptio_insights)
        
        # Verify natural language response
        natural_response = body['natural_response']
        self.assertIn('cost', natural_response.lower())
        self.assertIn('savings', natural_response.lower())
        self.assertIn('recommendation', natural_response.lower())

    @patch('lambda_functions.orchestrator_agent.boto3.client')
    def test_service_specific_query_e2e(self, mock_boto3_client):
        """Test E2E flow for service-specific queries."""
        # Configure mock Lambda client
        mock_lambda = MagicMock()
        mock_boto3_client.return_value = mock_lambda
        
        # Configure response for EC2-specific query
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps(self.ec2_agent_response))
        }
        
        # EC2-specific query
        event = {
            'query': 'Analyze my EC2 instances for cost optimization',
            'days': 30,
            'depth': 'standard'
        }
        
        result = lambda_handler(event, {})
        
        # Assertions
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        
        # Verify only EC2 agent was consulted
        analysis_plan = body['analysis_plan']
        self.assertIn('ec2_agent', analysis_plan['agents_to_invoke'])
        self.assertEqual(len(analysis_plan['agents_to_invoke']), 1)

    @patch('lambda_functions.orchestrator_agent.boto3.client')
    def test_error_handling_e2e(self, mock_boto3_client):
        """Test E2E error handling when agents fail."""
        # Configure mock Lambda client
        mock_lambda = MagicMock()
        mock_boto3_client.return_value = mock_lambda
        
        # Configure some agents to fail
        def lambda_invoke_with_errors(**kwargs):
            function_name = kwargs['FunctionName']
            response = MagicMock()
            
            if 'ec2-agent' in function_name:
                # EC2 agent fails
                response['StatusCode'] = 500
                response['Payload'].read.return_value = json.dumps({
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Internal error'})
                })
            else:
                # Other agents succeed
                response['StatusCode'] = 200
                response['Payload'].read.return_value = json.dumps(self.s3_agent_response)
            
            return response
        
        mock_lambda.invoke.side_effect = lambda_invoke_with_errors
        
        event = {
            'query': 'Analyze all AWS costs',
            'days': 30
        }
        
        result = lambda_handler(event, {})
        
        # Should still succeed overall
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        
        # Verify partial results are included
        self.assertIn('detailed_analysis', body)
        self.assertIn('agent_results', body)
        
        # Check that failed agent is noted
        agent_results = body['agent_results']
        failed_agents = [r for r in agent_results if not r.get('success', True)]
        self.assertGreater(len(failed_agents), 0)

    @patch('lambda_functions.orchestrator_agent.boto3.client')
    def test_performance_metrics_e2e(self, mock_boto3_client):
        """Test that performance metrics are tracked in E2E flow."""
        # Configure mock Lambda client
        mock_lambda = MagicMock()
        mock_boto3_client.return_value = mock_lambda
        
        # Quick responses for performance testing
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=lambda: json.dumps({
                'statusCode': 200,
                'body': json.dumps({'summary': {}, 'recommendations': []})
            }))
        }
        
        event = {
            'query': 'Quick cost check',
            'days': 7,
            'depth': 'summary'
        }
        
        start_time = datetime.utcnow()
        result = lambda_handler(event, {})
        end_time = datetime.utcnow()
        
        # Assertions
        self.assertEqual(result['statusCode'], 200)
        
        # Verify response includes timestamp
        body = json.loads(result['body'])
        self.assertIn('timestamp', body)
        
        # Verify execution time is reasonable (< 30 seconds for Lambda)
        execution_time = (end_time - start_time).total_seconds()
        self.assertLess(execution_time, 30)

    def test_orchestrator_analysis_plan_generation(self):
        """Test that orchestrator correctly generates analysis plans."""
        orchestrator = FinOpsOrchestrator()
        
        # Test various queries
        test_cases = [
            {
                'query': 'analyze EC2 and S3 costs',
                'expected_agents': ['ec2_agent', 's3_agent'],
                'expected_scope': 'general'
            },
            {
                'query': 'urgent cost optimization needed',
                'expected_priority': 'high',
                'expected_scope': 'comprehensive'
            },
            {
                'query': 'check tagging compliance',
                'expected_agents': ['tagging_agent'],
                'expected_scope': 'general'
            }
        ]
        
        for test_case in test_cases:
            plan = orchestrator.parse_user_query(test_case['query'])
            
            if 'expected_agents' in test_case:
                for agent in test_case['expected_agents']:
                    self.assertIn(agent, plan['agents_to_invoke'])
            
            if 'expected_priority' in test_case:
                self.assertEqual(plan['priority'], test_case['expected_priority'])
            
            if 'expected_scope' in test_case:
                self.assertEqual(plan['scope'], test_case['expected_scope'])

if __name__ == '__main__':
    unittest.main()