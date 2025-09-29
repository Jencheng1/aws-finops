import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the Cost Explorer MCP server module
from mcp_servers.cost_explorer_mcp import lambda_handler, get_cost_and_usage, get_cost_forecast, get_reservation_utilization, get_savings_plans_utilization

class TestCostExplorerMCP(unittest.TestCase):
    """Test cases for the Cost Explorer MCP Server Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample event data for getCostAndUsage
        self.cost_and_usage_event = {
            "requestType": "getCostAndUsage",
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
        
        # Sample event data for getCostForecast
        self.cost_forecast_event = {
            "requestType": "getCostForecast",
            "parameters": {
                "timePeriod": {
                    "Start": "2023-10-01",
                    "End": "2023-12-31"
                },
                "metric": "UNBLENDED_COST",
                "granularity": "MONTHLY"
            }
        }
        
        # Sample event data for getReservationUtilization
        self.reservation_utilization_event = {
            "requestType": "getReservationUtilization",
            "parameters": {
                "timePeriod": {
                    "Start": "2023-09-01",
                    "End": "2023-09-30"
                }
            }
        }
        
        # Sample event data for getSavingsPlansUtilization
        self.savings_plans_utilization_event = {
            "requestType": "getSavingsPlansUtilization",
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

    @patch('mcp_servers.cost_explorer_mcp.boto3.client')
    @patch('mcp_servers.cost_explorer_mcp.get_from_cache')
    @patch('mcp_servers.cost_explorer_mcp.store_in_cache')
    def test_get_cost_and_usage(self, mock_store_in_cache, mock_get_from_cache, mock_boto3_client):
        """Test the get_cost_and_usage function."""
        # Configure the mock objects
        mock_get_from_cache.return_value = None
        mock_ce = MagicMock()
        mock_ce.get_cost_and_usage.return_value = self.cost_and_usage_data
        mock_boto3_client.return_value = mock_ce
        
        # Call the function being tested
        result = get_cost_and_usage(self.cost_and_usage_event["parameters"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.cost_and_usage_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_from_cache.assert_called()
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
        mock_store_in_cache.assert_called()

    @patch('mcp_servers.cost_explorer_mcp.boto3.client')
    @patch('mcp_servers.cost_explorer_mcp.get_from_cache')
    @patch('mcp_servers.cost_explorer_mcp.store_in_cache')
    def test_get_cost_forecast(self, mock_store_in_cache, mock_get_from_cache, mock_boto3_client):
        """Test the get_cost_forecast function."""
        # Configure the mock objects
        mock_get_from_cache.return_value = None
        mock_ce = MagicMock()
        mock_ce.get_cost_forecast.return_value = self.cost_forecast_data
        mock_boto3_client.return_value = mock_ce
        
        # Call the function being tested
        result = get_cost_forecast(self.cost_forecast_event["parameters"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.cost_forecast_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_from_cache.assert_called()
        mock_ce.get_cost_forecast.assert_called_with(
            TimePeriod={
                "Start": "2023-10-01",
                "End": "2023-12-31"
            },
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY"
        )
        mock_store_in_cache.assert_called()

    @patch('mcp_servers.cost_explorer_mcp.boto3.client')
    @patch('mcp_servers.cost_explorer_mcp.get_from_cache')
    @patch('mcp_servers.cost_explorer_mcp.store_in_cache')
    def test_get_reservation_utilization(self, mock_store_in_cache, mock_get_from_cache, mock_boto3_client):
        """Test the get_reservation_utilization function."""
        # Configure the mock objects
        mock_get_from_cache.return_value = None
        mock_ce = MagicMock()
        mock_ce.get_reservation_utilization.return_value = self.reservation_utilization_data
        mock_boto3_client.return_value = mock_ce
        
        # Call the function being tested
        result = get_reservation_utilization(self.reservation_utilization_event["parameters"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.reservation_utilization_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_from_cache.assert_called()
        mock_ce.get_reservation_utilization.assert_called_with(
            TimePeriod={
                "Start": "2023-09-01",
                "End": "2023-09-30"
            }
        )
        mock_store_in_cache.assert_called()

    @patch('mcp_servers.cost_explorer_mcp.boto3.client')
    @patch('mcp_servers.cost_explorer_mcp.get_from_cache')
    @patch('mcp_servers.cost_explorer_mcp.store_in_cache')
    def test_get_savings_plans_utilization(self, mock_store_in_cache, mock_get_from_cache, mock_boto3_client):
        """Test the get_savings_plans_utilization function."""
        # Configure the mock objects
        mock_get_from_cache.return_value = None
        mock_ce = MagicMock()
        mock_ce.get_savings_plans_utilization.return_value = self.savings_plans_utilization_data
        mock_boto3_client.return_value = mock_ce
        
        # Call the function being tested
        result = get_savings_plans_utilization(self.savings_plans_utilization_event["parameters"])
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, self.savings_plans_utilization_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_from_cache.assert_called()
        mock_ce.get_savings_plans_utilization.assert_called_with(
            TimePeriod={
                "Start": "2023-09-01",
                "End": "2023-09-30"
            }
        )
        mock_store_in_cache.assert_called()

    @patch('mcp_servers.cost_explorer_mcp.get_cost_and_usage')
    def test_lambda_handler_get_cost_and_usage(self, mock_get_cost_and_usage):
        """Test the lambda_handler function with getCostAndUsage request type."""
        # Configure the mock objects
        mock_get_cost_and_usage.return_value = self.cost_and_usage_data
        
        # Call the function being tested
        result = lambda_handler(self.cost_and_usage_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], self.cost_and_usage_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_cost_and_usage.assert_called_with(self.cost_and_usage_event["parameters"])

    @patch('mcp_servers.cost_explorer_mcp.get_cost_forecast')
    def test_lambda_handler_get_cost_forecast(self, mock_get_cost_forecast):
        """Test the lambda_handler function with getCostForecast request type."""
        # Configure the mock objects
        mock_get_cost_forecast.return_value = self.cost_forecast_data
        
        # Call the function being tested
        result = lambda_handler(self.cost_forecast_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], self.cost_forecast_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_cost_forecast.assert_called_with(self.cost_forecast_event["parameters"])

    @patch('mcp_servers.cost_explorer_mcp.get_reservation_utilization')
    def test_lambda_handler_get_reservation_utilization(self, mock_get_reservation_utilization):
        """Test the lambda_handler function with getReservationUtilization request type."""
        # Configure the mock objects
        mock_get_reservation_utilization.return_value = self.reservation_utilization_data
        
        # Call the function being tested
        result = lambda_handler(self.reservation_utilization_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], self.reservation_utilization_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_reservation_utilization.assert_called_with(self.reservation_utilization_event["parameters"])

    @patch('mcp_servers.cost_explorer_mcp.get_savings_plans_utilization')
    def test_lambda_handler_get_savings_plans_utilization(self, mock_get_savings_plans_utilization):
        """Test the lambda_handler function with getSavingsPlansUtilization request type."""
        # Configure the mock objects
        mock_get_savings_plans_utilization.return_value = self.savings_plans_utilization_data
        
        # Call the function being tested
        result = lambda_handler(self.savings_plans_utilization_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], self.savings_plans_utilization_data)
        
        # Verify that the mock objects were called with the expected arguments
        mock_get_savings_plans_utilization.assert_called_with(self.savings_plans_utilization_event["parameters"])

    def test_lambda_handler_invalid_request_type(self):
        """Test the lambda_handler function with an invalid request type."""
        # Create an event with an invalid request type
        invalid_event = {
            "requestType": "invalidRequestType",
            "parameters": {}
        }
        
        # Call the function being tested
        result = lambda_handler(invalid_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], "Unsupported request type: invalidRequestType")

    def test_lambda_handler_missing_request_type(self):
        """Test the lambda_handler function with a missing request type."""
        # Create an event with a missing request type
        invalid_event = {
            "parameters": {}
        }
        
        # Call the function being tested
        result = lambda_handler(invalid_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 400)
        self.assertTrue("Missing required parameter: requestType" in result["body"])

    @patch('mcp_servers.cost_explorer_mcp.get_cost_and_usage')
    def test_lambda_handler_exception(self, mock_get_cost_and_usage):
        """Test the lambda_handler function when an exception occurs."""
        # Configure the mock objects to raise an exception
        mock_get_cost_and_usage.side_effect = Exception("Test exception")
        
        # Call the function being tested
        result = lambda_handler(self.cost_and_usage_event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(result["body"], "Error processing request: Test exception")

if __name__ == '__main__':
    unittest.main()
