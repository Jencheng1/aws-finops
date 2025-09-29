import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the mcp-servers directory to the path
mcp_servers_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'mcp-servers'
)
sys.path.insert(0, mcp_servers_path)

# Import the Cost Explorer MCP server module
import cost_explorer_mcp
from cost_explorer_mcp import CostExplorerMCPServer, MCPProtocolHandler

class TestCostExplorerMCP(unittest.TestCase):
    """Test cases for the Cost Explorer MCP Server Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample event data for get_cost_and_usage
        self.cost_and_usage_event = {
            "requestType": "get_cost_and_usage",
            "parameters": {
                "timePeriod": {
                    "Start": "2023-09-01",
                    "End": "2023-09-30"
                },
                "granularity": "MONTHLY",
                "metrics": ["UnblendedCost"],
                "groupBy": [
                    {
                        "Type": "DIMENSION",
                        "Key": "SERVICE"
                    }
                ]
            }
        }
        
        # Sample event data for get_cost_forecast
        self.cost_forecast_event = {
            "requestType": "get_cost_forecast",
            "parameters": {
                "timePeriod": {
                    "Start": "2023-10-01",
                    "End": "2023-12-31"
                },
                "metric": "UNBLENDED_COST",
                "granularity": "MONTHLY"
            }
        }
        
        # Sample event data for get_reservation_utilization
        self.reservation_utilization_event = {
            "requestType": "get_reservation_utilization",
            "parameters": {
                "timePeriod": {
                    "Start": "2023-09-01",
                    "End": "2023-09-30"
                }
            }
        }
        
        # Sample event data for get_savings_plans_utilization
        self.savings_plans_utilization_event = {
            "requestType": "get_savings_plans_utilization",
            "parameters": {
                "timePeriod": {
                    "Start": "2023-09-01",
                    "End": "2023-09-30"
                }
            }
        }
        
        # Sample cost and usage data
        self.cost_and_usage_data = {
            "GroupDefinitions": [
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE"
                }
            ],
            "ResultsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2023-09-01",
                        "End": "2023-09-30"
                    },
                    "Total": {
                        "UnblendedCost": {
                            "Amount": "1234.56",
                            "Unit": "USD"
                        }
                    },
                    "Groups": [
                        {
                            "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "800.00",
                                    "Unit": "USD"
                                }
                            }
                        },
                        {
                            "Keys": ["Amazon Simple Storage Service"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "200.00",
                                    "Unit": "USD"
                                }
                            }
                        },
                        {
                            "Keys": ["Amazon Relational Database Service"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "234.56",
                                    "Unit": "USD"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        # Sample cost forecast data
        self.cost_forecast_data = {
            "Total": {
                "Amount": "3800.00",
                "Unit": "USD"
            },
            "ForecastResultsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2023-10-01",
                        "End": "2023-10-31"
                    },
                    "MeanValue": "1200.00",
                    "PredictionIntervalLowerBound": "1000.00",
                    "PredictionIntervalUpperBound": "1400.00"
                },
                {
                    "TimePeriod": {
                        "Start": "2023-11-01",
                        "End": "2023-11-30"
                    },
                    "MeanValue": "1250.00",
                    "PredictionIntervalLowerBound": "1050.00",
                    "PredictionIntervalUpperBound": "1450.00"
                },
                {
                    "TimePeriod": {
                        "Start": "2023-12-01",
                        "End": "2023-12-31"
                    },
                    "MeanValue": "1350.00",
                    "PredictionIntervalLowerBound": "1150.00",
                    "PredictionIntervalUpperBound": "1550.00"
                }
            ]
        }
        
        # Sample reservation utilization data
        self.reservation_utilization_data = {
            "Total": {
                "UtilizationPercentage": "0.85",
                "PurchasedHours": "720.0",
                "TotalActualHours": "612.0",
                "UnusedHours": "108.0"
            },
            "UtilizationsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2023-09-01",
                        "End": "2023-09-30"
                    },
                    "Groups": [
                        {
                            "Key": ["EC2: t3.large"],
                            "Attributes": {
                                "UtilizationPercentage": "0.90",
                                "PurchasedHours": "360.0",
                                "TotalActualHours": "324.0",
                                "UnusedHours": "36.0"
                            }
                        },
                        {
                            "Key": ["EC2: m5.xlarge"],
                            "Attributes": {
                                "UtilizationPercentage": "0.80",
                                "PurchasedHours": "360.0",
                                "TotalActualHours": "288.0",
                                "UnusedHours": "72.0"
                            }
                        }
                    ]
                }
            ]
        }
        
        # Sample savings plans utilization data
        self.savings_plans_utilization_data = {
            "SavingsPlansUtilizationsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2023-09-01",
                        "End": "2023-09-30"
                    },
                    "Utilization": "0.85",
                    "TotalCommitment": "1000.00",
                    "UsedCommitment": "850.00",
                    "UnusedCommitment": "150.00"
                }
            ]
        }

    @patch('cost_explorer_mcp.boto3.client')
    def test_get_cost_and_usage(self, mock_boto3_client):
        """Test the get_cost_and_usage method."""
        # Configure the mock objects
        mock_ce = MagicMock()
        mock_ce.get_cost_and_usage.return_value = self.cost_and_usage_data
        mock_boto3_client.return_value = mock_ce
        
        # Create server instance and call the method being tested
        server = CostExplorerMCPServer()
        server.ce_client = mock_ce
        result = server.get_cost_and_usage(self.cost_and_usage_event["parameters"]["timePeriod"],
                                         self.cost_and_usage_event["parameters"]["granularity"],
                                         self.cost_and_usage_event["parameters"]["metrics"],
                                         self.cost_and_usage_event["parameters"]["groupBy"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.cost_and_usage_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_ce.get_cost_and_usage.assert_called_with(
            TimePeriod={
                "Start": "2023-09-01",
                "End": "2023-09-30"
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE"
                }
            ]
        )

    @patch('cost_explorer_mcp.boto3.client')
    def test_get_cost_forecast(self, mock_boto3_client):
        """Test the get_cost_forecast method."""
        # Configure the mock objects
        mock_ce = MagicMock()
        mock_ce.get_cost_forecast.return_value = self.cost_forecast_data
        mock_boto3_client.return_value = mock_ce
        
        # Create server instance and call the method being tested
        server = CostExplorerMCPServer()
        server.ce_client = mock_ce
        result = server.get_cost_forecast(self.cost_forecast_event["parameters"]["timePeriod"],
                                        self.cost_forecast_event["parameters"]["metric"],
                                        self.cost_forecast_event["parameters"]["granularity"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.cost_forecast_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_ce.get_cost_forecast.assert_called_with(
            TimePeriod={
                "Start": "2023-10-01",
                "End": "2023-12-31"
            },
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY"
        )

    @patch('cost_explorer_mcp.boto3.client')
    def test_get_reservation_utilization(self, mock_boto3_client):
        """Test the get_reservation_utilization method."""
        # Configure the mock objects
        mock_ce = MagicMock()
        mock_ce.get_reservation_utilization.return_value = self.reservation_utilization_data
        mock_boto3_client.return_value = mock_ce
        
        # Create server instance and call the method being tested
        server = CostExplorerMCPServer()
        server.ce_client = mock_ce
        result = server.get_reservation_utilization(self.reservation_utilization_event["parameters"]["timePeriod"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.reservation_utilization_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_ce.get_reservation_utilization.assert_called_with(
            TimePeriod={
                "Start": "2023-09-01",
                "End": "2023-09-30"
            }
        )

    @patch('cost_explorer_mcp.boto3.client')
    def test_get_savings_plans_utilization(self, mock_boto3_client):
        """Test the get_savings_plans_utilization method."""
        # Configure the mock objects
        mock_ce = MagicMock()
        mock_ce.get_savings_plans_utilization.return_value = self.savings_plans_utilization_data
        mock_boto3_client.return_value = mock_ce
        
        # Create server instance and call the method being tested
        server = CostExplorerMCPServer()
        server.ce_client = mock_ce
        result = server.get_savings_plans_utilization(self.savings_plans_utilization_event["parameters"]["timePeriod"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.savings_plans_utilization_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_ce.get_savings_plans_utilization.assert_called_with(
            TimePeriod={
                "Start": "2023-09-01",
                "End": "2023-09-30"
            }
        )

    async def test_process_mcp_request_get_cost_and_usage(self):
        """Test the process_mcp_request with get_cost_and_usage method."""
        # Create server instance
        server = CostExplorerMCPServer()
        
        # Create MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "test_123",
            "method": "get_cost_and_usage",
            "params": self.cost_and_usage_event["parameters"]
        }
        
        # Mock the boto3 client
        with patch('cost_explorer_mcp.boto3.client') as mock_boto3_client:
            mock_ce = MagicMock()
            mock_ce.get_cost_and_usage.return_value = self.cost_and_usage_data
            mock_boto3_client.return_value = mock_ce
            server.ce_client = mock_ce
            
            # Call the method being tested
            result = await server.process_mcp_request(mcp_request)
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result, self.cost_and_usage_data)

    async def test_process_mcp_request_get_cost_forecast(self):
        """Test the process_mcp_request with get_cost_forecast method."""
        # Create server instance
        server = CostExplorerMCPServer()
        
        # Create MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "test_123",
            "method": "get_cost_forecast",
            "params": self.cost_forecast_event["parameters"]
        }
        
        # Mock the boto3 client
        with patch('cost_explorer_mcp.boto3.client') as mock_boto3_client:
            mock_ce = MagicMock()
            mock_ce.get_cost_forecast.return_value = self.cost_forecast_data
            mock_boto3_client.return_value = mock_ce
            server.ce_client = mock_ce
            
            # Call the method being tested
            result = await server.process_mcp_request(mcp_request)
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result, self.cost_forecast_data)

    async def test_process_mcp_request_get_reservation_utilization(self):
        """Test the process_mcp_request with get_reservation_utilization method."""
        # Create server instance
        server = CostExplorerMCPServer()
        
        # Create MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "test_123",
            "method": "get_reservation_utilization",
            "params": self.reservation_utilization_event["parameters"]
        }
        
        # Mock the boto3 client
        with patch('cost_explorer_mcp.boto3.client') as mock_boto3_client:
            mock_ce = MagicMock()
            mock_ce.get_reservation_utilization.return_value = self.reservation_utilization_data
            mock_boto3_client.return_value = mock_ce
            server.ce_client = mock_ce
            
            # Call the method being tested
            result = await server.process_mcp_request(mcp_request)
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result, self.reservation_utilization_data)

    async def test_process_mcp_request_get_savings_plans_utilization(self):
        """Test the process_mcp_request with get_savings_plans_utilization method."""
        # Create server instance
        server = CostExplorerMCPServer()
        
        # Create MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "test_123",
            "method": "get_savings_plans_utilization",
            "params": self.savings_plans_utilization_event["parameters"]
        }
        
        # Mock the boto3 client
        with patch('cost_explorer_mcp.boto3.client') as mock_boto3_client:
            mock_ce = MagicMock()
            mock_ce.get_savings_plans_utilization.return_value = self.savings_plans_utilization_data
            mock_boto3_client.return_value = mock_ce
            server.ce_client = mock_ce
            
            # Call the method being tested
            result = await server.process_mcp_request(mcp_request)
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertEqual(result, self.savings_plans_utilization_data)

    async def test_process_mcp_request_invalid_method(self):
        """Test the process_mcp_request with an invalid method."""
        # Create server instance
        server = CostExplorerMCPServer()
        
        # Create MCP request with invalid method
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "test_123",
            "method": "invalidMethod",
            "params": {}
        }
        
        # Call the method being tested
        result = await server.process_mcp_request(mcp_request)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertIn("error", result)
        self.assertEqual(result["error"]["code"], -32601)
        self.assertIn("Method not found", result["error"]["message"])

    async def test_protocol_handler_handle_request(self):
        """Test the MCPProtocolHandler handle_request method."""
        # Create handler instance
        handler = MCPProtocolHandler()
        
        # Create request data
        request_data = json.dumps({
            "jsonrpc": "2.0",
            "id": "test_123",
            "method": "get_cost_and_usage",
            "params": self.cost_and_usage_event["parameters"]
        })
        
        # Mock the boto3 client
        with patch('cost_explorer_mcp.boto3.client') as mock_boto3_client:
            mock_ce = MagicMock()
            mock_ce.get_cost_and_usage.return_value = self.cost_and_usage_data
            mock_boto3_client.return_value = mock_ce
            handler.cost_explorer_server.ce_client = mock_ce
            
            # Call the method being tested
            result = await handler.handle_request(request_data)
            
            # Assertions
            self.assertIsNotNone(result)
            response = json.loads(result)
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], "test_123")
            self.assertIn("result", response)

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
TestCostExplorerMCP.test_process_mcp_request_get_cost_and_usage = async_test(
    TestCostExplorerMCP.test_process_mcp_request_get_cost_and_usage
)
TestCostExplorerMCP.test_process_mcp_request_get_cost_forecast = async_test(
    TestCostExplorerMCP.test_process_mcp_request_get_cost_forecast
)
TestCostExplorerMCP.test_process_mcp_request_get_reservation_utilization = async_test(
    TestCostExplorerMCP.test_process_mcp_request_get_reservation_utilization
)
TestCostExplorerMCP.test_process_mcp_request_get_savings_plans_utilization = async_test(
    TestCostExplorerMCP.test_process_mcp_request_get_savings_plans_utilization
)
TestCostExplorerMCP.test_process_mcp_request_invalid_method = async_test(
    TestCostExplorerMCP.test_process_mcp_request_invalid_method
)
TestCostExplorerMCP.test_protocol_handler_handle_request = async_test(
    TestCostExplorerMCP.test_protocol_handler_handle_request
)

if __name__ == '__main__':
    unittest.main()
