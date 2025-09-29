import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import boto3
from botocore.stub import Stubber

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the lambda-functions directory to the path
lambda_functions_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'lambda-functions'
)
sys.path.insert(0, lambda_functions_path)

# Import the modules
import orchestrator_agent
import ec2_agent
from orchestrator_agent import lambda_handler as orchestrator_handler
from ec2_agent import lambda_handler as ec2_handler

class TestOrchestratorEC2Integration(unittest.TestCase):
    """Integration tests for the Orchestrator Agent and EC2 Agent."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample event data for the orchestrator
        self.orchestrator_event = {
            "action": "analyzeEC2Costs",
            "parameters": {
                "accountId": "123456789012",
                "region": "us-east-1",
                "timeRange": "30d"
            }
        }
        
        # Sample EC2 instance data
        self.ec2_instances = [
            {
                "InstanceId": "i-1234567890abcdef0",
                "InstanceType": "t3.large",
                "State": {
                    "Name": "running"
                },
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": "TestInstance1"
                    },
                    {
                        "Key": "Environment",
                        "Value": "Development"
                    }
                ]
            },
            {
                "InstanceId": "i-0987654321fedcba0",
                "InstanceType": "m5.xlarge",
                "State": {
                    "Name": "running"
                },
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": "TestInstance2"
                    },
                    {
                        "Key": "Environment",
                        "Value": "Production"
                    }
                ]
            }
        ]
        
        # Sample CloudWatch metrics data
        self.cloudwatch_metrics = {
            "MetricDataResults": [
                {
                    "Id": "cpu_i_1234567890abcdef0",
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
                    "Id": "cpu_i_0987654321fedcba0",
                    "Label": "CPUUtilization",
                    "Timestamps": [
                        "2023-09-01T00:00:00Z",
                        "2023-09-02T00:00:00Z",
                        "2023-09-03T00:00:00Z"
                    ],
                    "Values": [45.2, 52.8, 48.3],
                    "StatusCode": "Complete"
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
                            "Amount": "350.75",
                            "Unit": "USD"
                        }
                    },
                    "Groups": [
                        {
                            "Keys": ["i-1234567890abcdef0"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "100.50",
                                    "Unit": "USD"
                                }
                            }
                        },
                        {
                            "Keys": ["i-0987654321fedcba0"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "250.25",
                                    "Unit": "USD"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        # Sample EC2 pricing data
        self.pricing_data = {
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
                }),
                json.dumps({
                    "product": {
                        "attributes": {
                            "instanceType": "m5.large"
                        }
                    },
                    "terms": {
                        "OnDemand": {
                            "1": {
                                "priceDimensions": {
                                    "1": {
                                        "pricePerUnit": {
                                            "USD": "0.096"
                                        }
                                    }
                                }
                            }
                        }
                    }
                })
            ]
        }

    @patch('lambda_functions.orchestrator_agent.boto3.client')
    @patch('lambda_functions.ec2_agent.boto3.client')
    def test_orchestrator_ec2_integration(self, mock_ec2_boto3_client, mock_orchestrator_boto3_client):
        """Test the integration between the Orchestrator Agent and EC2 Agent."""
        # Configure the mock objects for the EC2 agent
        mock_ec2_cloudwatch = MagicMock()
        mock_ec2_ec2 = MagicMock()
        mock_ec2_ce = MagicMock()
        mock_ec2_pricing = MagicMock()
        
        # Set up the return values for the EC2 agent mock objects
        mock_ec2_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [self.ec2_instances[0]]
                },
                {
                    "Instances": [self.ec2_instances[1]]
                }
            ]
        }
        mock_ec2_cloudwatch.get_metric_data.return_value = self.cloudwatch_metrics
        mock_ec2_ce.get_cost_and_usage.return_value = self.cost_data
        mock_ec2_pricing.get_products.return_value = self.pricing_data
        
        # Configure the boto3.client mock for the EC2 agent
        mock_ec2_boto3_client.side_effect = lambda service, **kwargs: {
            'cloudwatch': mock_ec2_cloudwatch,
            'ec2': mock_ec2_ec2,
            'ce': mock_ec2_ce,
            'pricing': mock_ec2_pricing
        }[service]
        
        # Configure the mock objects for the orchestrator agent
        mock_orchestrator_lambda = MagicMock()
        mock_orchestrator_ec2 = MagicMock()
        mock_orchestrator_dynamodb = MagicMock()
        
        # Set up the return values for the orchestrator agent mock objects
        mock_orchestrator_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [self.ec2_instances[0]]
                },
                {
                    "Instances": [self.ec2_instances[1]]
                }
            ]
        }
        
        # Mock the Lambda invoke function to simulate calling the EC2 agent
        def mock_invoke(FunctionName, InvocationType, Payload):
            # Parse the payload
            payload = json.loads(Payload)
            
            # Call the EC2 agent directly
            ec2_response = ec2_handler(payload, {})
            
            # Return a mock response with the EC2 agent's response
            return {
                'StatusCode': 200,
                'Payload': MagicMock(
                    read=lambda: json.dumps(ec2_response).encode('utf-8')
                )
            }
        
        mock_orchestrator_lambda.invoke.side_effect = mock_invoke
        
        # Configure the boto3.client mock for the orchestrator agent
        mock_orchestrator_boto3_client.side_effect = lambda service, **kwargs: {
            'lambda': mock_orchestrator_lambda,
            'ec2': mock_orchestrator_ec2,
            'dynamodb': mock_orchestrator_dynamodb
        }[service]
        
        # Call the orchestrator handler
        orchestrator_response = orchestrator_handler(self.orchestrator_event, {})
        
        # Assertions
        self.assertIsNotNone(orchestrator_response)
        self.assertEqual(orchestrator_response["statusCode"], 200)
        
        # Parse the response body
        body = json.loads(orchestrator_response["body"])
        
        # Verify the response contains the expected data
        self.assertIn("accountId", body)
        self.assertEqual(body["accountId"], "123456789012")
        self.assertIn("region", body)
        self.assertEqual(body["region"], "us-east-1")
        self.assertIn("timeRange", body)
        self.assertEqual(body["timeRange"], "30d")
        self.assertIn("totalCost", body)
        self.assertIn("instances", body)
        self.assertEqual(len(body["instances"]), 2)
        
        # Verify the instance data
        for instance in body["instances"]:
            self.assertIn("instanceId", instance)
            self.assertIn("instanceType", instance)
            self.assertIn("utilizationMetrics", instance)
            self.assertIn("cost", instance)
            self.assertIn("recommendedAction", instance)
            
            # Verify the utilization metrics
            self.assertIn("cpu", instance["utilizationMetrics"])
            self.assertIn("average", instance["utilizationMetrics"]["cpu"])
            self.assertIn("max", instance["utilizationMetrics"]["cpu"])
            self.assertIn("min", instance["utilizationMetrics"]["cpu"])
            
            # Verify the cost data
            self.assertIn("monthly", instance["cost"])
            self.assertIn("daily", instance["cost"])
            
            # Verify the recommended action
            self.assertIn("action", instance["recommendedAction"])
            self.assertIn("details", instance["recommendedAction"])
            self.assertIn("estimatedSavings", instance["recommendedAction"])
        
        # Verify that the mock objects were called with the expected arguments
        mock_orchestrator_ec2.describe_instances.assert_called()
        mock_orchestrator_lambda.invoke.assert_called()
        
        # Verify that the EC2 agent mock objects were called with the expected arguments
        mock_ec2_ec2.describe_instances.assert_called()
        mock_ec2_cloudwatch.get_metric_data.assert_called()
        mock_ec2_ce.get_cost_and_usage.assert_called()
        mock_ec2_pricing.get_products.assert_called()

if __name__ == '__main__':
    unittest.main()
