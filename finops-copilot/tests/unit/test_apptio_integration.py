import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Mock httpx before importing the module that uses it
sys.modules['httpx'] = MagicMock()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the lambda-functions directory to the path
lambda_functions_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'lambda-functions'
)
sys.path.insert(0, lambda_functions_path)

# Import AsyncMock compatibility for Python 3.7
try:
    from unittest.mock import AsyncMock
except ImportError:
    # Add the tests directory to path for the mock_async module
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mock_async import AsyncMock

# Import the Apptio integration module
import apptio_integration
from apptio_integration import (
    lambda_handler, ApptioMCPClient, ApptioDataEnricher
)

class TestApptioMCPClient(unittest.TestCase):
    """Test cases for the Apptio MCP Client."""

    def setUp(self):
        """Set up test fixtures."""
        self.mcp_endpoint = "http://test-mcp:8000"
        self.api_key = "test-api-key"
        self.env_id = "test-env-id"

    @patch('apptio_integration.boto3.client')
    def test_load_configuration(self, mock_boto3_client):
        """Test loading configuration from Parameter Store."""
        # Configure mock SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Set up parameter responses
        mock_ssm.get_parameter.side_effect = [
            {'Parameter': {'Value': self.mcp_endpoint}},
            {'Parameter': {'Value': self.api_key}},
            {'Parameter': {'Value': self.env_id}}
        ]
        
        # Create client instance
        client = ApptioMCPClient()
        
        # Assertions
        self.assertEqual(client.mcp_endpoint, self.mcp_endpoint)
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.env_id, self.env_id)
        
        # Verify SSM calls
        self.assertEqual(mock_ssm.get_parameter.call_count, 3)

    @patch('apptio_integration.boto3.client')
    def test_load_configuration_failure(self, mock_boto3_client):
        """Test configuration loading with SSM failures."""
        # Configure mock SSM client to raise exception
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        mock_ssm.get_parameter.side_effect = Exception("Parameter not found")
        
        # Create client instance
        client = ApptioMCPClient()
        
        # Should fall back to defaults
        self.assertEqual(client.mcp_endpoint, "http://localhost:8000")
        self.assertEqual(client.api_key, "")
        self.assertEqual(client.env_id, "")

    @patch('httpx.AsyncClient')
    async def test_call_mcp_tool_success(self, mock_async_client):
        """Test successful MCP tool call."""
        # Configure mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client
        
        # Configure response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 'test_123',
            'result': {'cost_data': 'test_data'}
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        # Create client and call tool
        client = ApptioMCPClient()
        client.mcp_endpoint = self.mcp_endpoint
        client.api_key = self.api_key
        client.env_id = self.env_id
        
        result = await client.call_mcp_tool(
            'get_cost_data',
            {'start_date': '2023-01-01', 'end_date': '2023-01-31'}
        )
        
        # Assertions
        self.assertEqual(result, {'cost_data': 'test_data'})
        mock_client.post.assert_called_once()
        
        # Verify request format
        call_args = mock_client.post.call_args
        self.assertEqual(call_args[0][0], self.mcp_endpoint)
        self.assertIn('Authorization', call_args[1]['headers'])

    @patch('httpx.AsyncClient')
    async def test_call_mcp_tool_error(self, mock_async_client):
        """Test MCP tool call with error response."""
        # Configure mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client
        
        # Configure error response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'id': 'test_123',
            'error': {'code': -32000, 'message': 'Internal error'}
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        # Create client and call tool
        client = ApptioMCPClient()
        client.mcp_endpoint = self.mcp_endpoint
        
        result = await client.call_mcp_tool('get_cost_data', {})
        
        # Should return error
        self.assertIn('error', result)
        self.assertEqual(result['error']['code'], -32000)

class TestApptioDataEnricher(unittest.TestCase):
    """Test cases for the Apptio Data Enricher."""

    def setUp(self):
        """Set up test fixtures."""
        self.aws_cost_data = {
            'summary': {
                'total_monthly_cost': 10000,
                'potential_monthly_savings': 2000
            }
        }
        
        self.apptio_cost_response = {
            'result': {
                'totalCost': 10500,
                'services': [
                    {'name': 'EC2', 'cost': 5000},
                    {'name': 'S3', 'cost': 2000}
                ]
            }
        }
        
        self.apptio_forecast_response = {
            'result': {
                'forecast_accuracy': 'high',
                'projected_spend': 11000
            }
        }
        
        self.apptio_recommendations_response = {
            'result': [
                {
                    'title': 'Optimize Reserved Instances',
                    'savings': 1500,
                    'impact': 'High'
                }
            ]
        }

    @patch('apptio_integration.ApptioMCPClient')
    async def test_enrich_cost_analysis(self, mock_client_class):
        """Test enriching AWS cost data with Apptio insights."""
        # Configure mock MCP client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Set up mock responses
        mock_client.get_cost_data.return_value = self.apptio_cost_response
        mock_client.get_forecast_data.return_value = self.apptio_forecast_response
        mock_client.get_optimization_recommendations.return_value = self.apptio_recommendations_response
        mock_client.get_budget_vs_actual.return_value = {
            'result': {'budget_variance': 500}
        }
        
        # Create enricher and enrich data
        enricher = ApptioDataEnricher()
        result = await enricher.enrich_cost_analysis(self.aws_cost_data, days=30)
        
        # Assertions
        self.assertIn('aws_data', result)
        self.assertIn('apptio_insights', result)
        self.assertIn('combined_analysis', result)
        
        # Verify AWS data is preserved
        self.assertEqual(result['aws_data'], self.aws_cost_data)
        
        # Verify Apptio insights structure
        insights = result['apptio_insights']
        self.assertIn('cost_analysis', insights)
        self.assertIn('forecast', insights)
        self.assertIn('budget_comparison', insights)
        self.assertIn('additional_recommendations', insights)
        
        # Verify combined analysis
        combined = result['combined_analysis']
        self.assertIn('total_identified_savings', combined)
        self.assertIn('confidence_score', combined)
        self.assertIn('opportunity_areas', combined)

    @patch('apptio_integration.ApptioMCPClient')
    async def test_enrich_cost_analysis_failure(self, mock_client_class):
        """Test enrichment when Apptio calls fail."""
        # Configure mock MCP client to raise exception
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get_cost_data.side_effect = Exception("API Error")
        
        # Create enricher and enrich data
        enricher = ApptioDataEnricher()
        result = await enricher.enrich_cost_analysis(self.aws_cost_data, days=30)
        
        # Should return original data with error
        self.assertEqual(result['aws_data'], self.aws_cost_data)
        self.assertIn('error', result['apptio_insights'])
        self.assertEqual(result['combined_analysis'], {})

class TestLambdaHandler(unittest.TestCase):
    """Test cases for the Lambda handler."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_enrich = {
            'action': 'enrich_analysis',
            'aws_cost_data': {
                'summary': {
                    'total_monthly_cost': 10000,
                    'potential_monthly_savings': 2000
                }
            },
            'days': 30
        }
        
        self.event_get_data = {
            'action': 'get_apptio_data',
            'days': 30
        }

    @patch('apptio_integration.ApptioDataEnricher')
    @patch('asyncio.new_event_loop')
    def test_lambda_handler_enrich_analysis(self, mock_event_loop, mock_enricher_class):
        """Test lambda handler with enrich_analysis action."""
        # Configure mock event loop
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        
        # Configure mock enricher
        mock_enricher = MagicMock()
        mock_enricher_class.return_value = mock_enricher
        
        # Configure enrichment result
        enriched_data = {
            'aws_data': self.event_enrich['aws_cost_data'],
            'apptio_insights': {'test': 'data'},
            'combined_analysis': {}
        }
        mock_loop.run_until_complete.return_value = enriched_data
        
        # Call handler
        result = lambda_handler(self.event_enrich, {})
        
        # Assertions
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body, enriched_data)
        
        # Verify enricher was called
        mock_enricher_class.assert_called_once()
        mock_loop.run_until_complete.assert_called_once()

    @patch('apptio_integration.ApptioMCPClient')
    @patch('asyncio.new_event_loop')
    def test_lambda_handler_get_apptio_data(self, mock_event_loop, mock_client_class):
        """Test lambda handler with get_apptio_data action."""
        # Configure mock event loop
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        
        # Configure mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Configure gather result
        gather_results = [
            {'cost_data': 'test'},
            {'forecast': 'test'},
            {'recommendations': 'test'}
        ]
        mock_loop.run_until_complete.return_value = gather_results
        
        # Call handler
        result = lambda_handler(self.event_get_data, {})
        
        # Assertions
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('cost_data', body)
        self.assertIn('forecast', body)
        self.assertIn('recommendations', body)

    def test_lambda_handler_invalid_action(self):
        """Test lambda handler with invalid action."""
        event = {'action': 'invalid_action'}
        
        result = lambda_handler(event, {})
        
        # Should return 400 error
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Invalid action')

    def test_lambda_handler_exception(self):
        """Test lambda handler exception handling."""
        # Event that will cause an error
        event = {'action': 'enrich_analysis'}  # Missing required data
        
        result = lambda_handler(event, {})
        
        # Should return 500 error
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertIn('error', body)
        self.assertIn('details', body)

# Helper function to run async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

# Apply async_test decorator to async test methods
TestApptioMCPClient.test_call_mcp_tool_success = async_test(
    TestApptioMCPClient.test_call_mcp_tool_success
)
TestApptioMCPClient.test_call_mcp_tool_error = async_test(
    TestApptioMCPClient.test_call_mcp_tool_error
)
TestApptioDataEnricher.test_enrich_cost_analysis = async_test(
    TestApptioDataEnricher.test_enrich_cost_analysis
)
TestApptioDataEnricher.test_enrich_cost_analysis_failure = async_test(
    TestApptioDataEnricher.test_enrich_cost_analysis_failure
)

if __name__ == '__main__':
    unittest.main()