import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the EC2 agent module
from lambda_functions.ec2_agent import lambda_handler, analyze_utilization, recommend_right_sizing

class TestEC2Agent(unittest.TestCase):
    """Test cases for the EC2 Agent Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample event data
        self.event = {
            "action": "analyzeUtilization",
            "parameters": {
                "instanceId": "i-1234567890abcdef0",
                "timeRange": "30d"
            }
        }
        
        # Sample CloudWatch metrics data
        self.cloudwatch_metrics = {
            "MetricDataResults": [
                {
                    "Id": "cpu",
                    "Label": "CPUUtilization",
                    "Timestamps": [
                        "2023-09-01T00:00:00Z",
                        "2023-09-02T00:00:00Z",
                        "2023-09-03T00:00:00Z"
                    ],
                    "Values": [10.5, 15.2, 8.7],
                    "StatusCode": "Complete"
                },
                {
                    "Id": "memory",
                    "Label": "MemoryUtilization",
                    "Timestamps": [
                        "2023-09-01T00:00:00Z",
                        "2023-09-02T00:00:00Z",
                        "2023-09-03T00:00:00Z"
                    ],
                    "Values": [30.1, 35.8, 28.4],
                    "StatusCode": "Complete"
                }
            ]
        }
        
        # Sample EC2 instance data
        self.ec2_instance = {
            "InstanceId": "i-1234567890abcdef0",
            "InstanceType": "t3.large",
            "State": {
                "Name": "running"
            },
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "TestInstance"
                },
                {
                    "Key": "Environment",
                    "Value": "Development"
                }
            ]
        }
        
        # Sample cost data
        self.cost_data = {
            "ResultsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2023-09-01",
                        "End": "2023-09-30"
                    },
                    "Total": {
                        "UnblendedCost": {
                            "Amount": "100.50",
                            "Unit": "USD"
                        }
                    }
                }
            ]
        }

    @patch('lambda_functions.ec2_agent.boto3.client')
    def test_analyze_utilization(self, mock_boto3_client):
        """Test the analyze_utilization function."""
        # Configure the mock objects
        mock_cloudwatch = MagicMock()
        mock_ec2 = MagicMock()
        mock_ce = MagicMock()
        
        # Set up the return values for the mock objects
        mock_cloudwatch.get_metric_data.return_value = self.cloudwatch_metrics
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [self.ec2_instance]
                }
            ]
        }
        mock_ce.get_cost_and_usage.return_value = self.cost_data
        
        # Configure the boto3.client mock to return our mock objects
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'cloudwatch': mock_cloudwatch,
            'ec2': mock_ec2,
            'ce': mock_ce
        }[service]
        
        # Call the function being tested
        result = analyze_utilization("i-1234567890abcdef0", "30d")
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["instanceId"], "i-1234567890abcdef0")
        self.assertEqual(result["instanceType"], "t3.large")
        self.assertIn("cpuUtilization", result)
        self.assertIn("memoryUtilization", result)
        self.assertIn("cost", result)
        
        # Verify that the mock objects were called with the expected arguments
        mock_cloudwatch.get_metric_data.assert_called()
        mock_ec2.describe_instances.assert_called_with(
            InstanceIds=["i-1234567890abcdef0"]
        )
        mock_ce.get_cost_and_usage.assert_called()

    @patch('lambda_functions.ec2_agent.boto3.client')
    def test_recommend_right_sizing(self, mock_boto3_client):
        """Test the recommend_right_sizing function."""
        # Configure the mock objects
        mock_cloudwatch = MagicMock()
        mock_ec2 = MagicMock()
        mock_pricing = MagicMock()
        
        # Set up the return values for the mock objects
        mock_cloudwatch.get_metric_data.return_value = self.cloudwatch_metrics
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [self.ec2_instance]
                }
            ]
        }
        mock_pricing.get_products.return_value = {
            "PriceList": [
                json.dumps({
                    "product": {
                        "attributes": {
                            "instanceType": "t3.medium"
                        }
                    },
                    "terms": {
                        "OnDemand": {
                            "1": {
                                "priceDimensions": {
                                    "1": {
                                        "pricePerUnit": {
                                            "USD": "0.0416"
                                        }
                                    }
                                }
                            }
                        }
                    }
                })
            ]
        }
        
        # Configure the boto3.client mock to return our mock objects
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'cloudwatch': mock_cloudwatch,
            'ec2': mock_ec2,
            'pricing': mock_pricing
        }[service]
        
        # Call the function being tested
        result = recommend_right_sizing("i-1234567890abcdef0")
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["instanceId"], "i-1234567890abcdef0")
        self.assertEqual(result["currentInstanceType"], "t3.large")
        self.assertIn("recommendedInstanceType", result)
        self.assertIn("estimatedMonthlySavings", result)
        self.assertIn("utilizationMetrics", result)
        
        # Verify that the mock objects were called with the expected arguments
        mock_cloudwatch.get_metric_data.assert_called()
        mock_ec2.describe_instances.assert_called_with(
            InstanceIds=["i-1234567890abcdef0"]
        )
        mock_pricing.get_products.assert_called()

    @patch('lambda_functions.ec2_agent.analyze_utilization')
    @patch('lambda_functions.ec2_agent.recommend_right_sizing')
    def test_lambda_handler_analyze_utilization(self, mock_recommend_right_sizing, mock_analyze_utilization):
        """Test the lambda_handler function with analyzeUtilization action."""
        # Configure the mock objects
        mock_analyze_utilization.return_value = {
            "instanceId": "i-1234567890abcdef0",
            "instanceType": "t3.large",
            "cpuUtilization": {
                "average": 11.47,
                "max": 15.2,
                "min": 8.7
            },
            "memoryUtilization": {
                "average": 31.43,
                "max": 35.8,
                "min": 28.4
            },
            "cost": {
                "monthly": 100.50,
                "daily": 3.35
            }
        }
        
        # Call the function being tested
        result = lambda_handler(self.event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 200)
        
        # Parse the response body
        body = json.loads(result["body"])
        self.assertEqual(body["instanceId"], "i-1234567890abcdef0")
        self.assertEqual(body["instanceType"], "t3.large")
        self.assertIn("cpuUtilization", body)
        self.assertIn("memoryUtilization", body)
        self.assertIn("cost", body)
        
        # Verify that the mock objects were called with the expected arguments
        mock_analyze_utilization.assert_called_with(
            "i-1234567890abcdef0", "30d"
        )
        mock_recommend_right_sizing.assert_not_called()

    @patch('lambda_functions.ec2_agent.analyze_utilization')
    @patch('lambda_functions.ec2_agent.recommend_right_sizing')
    def test_lambda_handler_recommend_right_sizing(self, mock_recommend_right_sizing, mock_analyze_utilization):
        """Test the lambda_handler function with recommendRightSizing action."""
        # Update the event for this test
        self.event["action"] = "recommendRightSizing"
        
        # Configure the mock objects
        mock_recommend_right_sizing.return_value = {
            "instanceId": "i-1234567890abcdef0",
            "currentInstanceType": "t3.large",
            "recommendedInstanceType": "t3.medium",
            "estimatedMonthlySavings": 50.25,
            "utilizationMetrics": {
                "cpu": {
                    "average": 11.47,
                    "max": 15.2,
                    "min": 8.7
                },
                "memory": {
                    "average": 31.43,
                    "max": 35.8,
                    "min": 28.4
                }
            }
        }
        
        # Call the function being tested
        result = lambda_handler(self.event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 200)
        
        # Parse the response body
        body = json.loads(result["body"])
        self.assertEqual(body["instanceId"], "i-1234567890abcdef0")
        self.assertEqual(body["currentInstanceType"], "t3.large")
        self.assertEqual(body["recommendedInstanceType"], "t3.medium")
        self.assertEqual(body["estimatedMonthlySavings"], 50.25)
        self.assertIn("utilizationMetrics", body)
        
        # Verify that the mock objects were called with the expected arguments
        mock_analyze_utilization.assert_not_called()
        mock_recommend_right_sizing.assert_called_with(
            "i-1234567890abcdef0"
        )

    def test_lambda_handler_invalid_action(self):
        """Test the lambda_handler function with an invalid action."""
        # Update the event for this test
        self.event["action"] = "invalidAction"
        
        # Call the function being tested
        result = lambda_handler(self.event, {})
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["statusCode"], 400)
        
        # Parse the response body
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"], "Invalid action: invalidAction")

if __name__ == '__main__':
    unittest.main()
