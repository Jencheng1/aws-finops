#!/usr/bin/env python3
"""
Real API Tests for Cost Explorer MCP Server
Tests the MCP server with real AWS Cost Explorer API
"""

import unittest
import json
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp-servers'))

class TestCostExplorerMCPReal(unittest.TestCase):
    """Test Cost Explorer MCP Server with real AWS APIs"""
    
    def test_mcp_server_initialization(self):
        """Test MCP server initialization with real AWS"""
        try:
            from cost_explorer_mcp import CostExplorerMCPServer
            
            server = CostExplorerMCPServer()
            self.assertIsNotNone(server)
            self.assertIsNotNone(server.cost_explorer_client)
            logger.info("✓ Cost Explorer MCP Server initialized successfully")
            
        except Exception as e:
            self.fail(f"Failed to initialize MCP server: {str(e)}")
    
    def test_get_cost_and_usage_real(self):
        """Test get_cost_and_usage with real AWS data"""
        try:
            from cost_explorer_mcp import CostExplorerMCPServer
            
            server = CostExplorerMCPServer()
            
            # Prepare dates
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7)
            
            # Create async function to call the method
            async def get_costs():
                result = await server.get_cost_and_usage(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    granularity='DAILY',
                    metrics=['UnblendedCost']
                )
                return result
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(get_costs())
                
                # Verify result structure
                self.assertIn('time_period', result)
                self.assertIn('results', result)
                self.assertIn('total_cost', result)
                self.assertIsInstance(result['total_cost'], (int, float))
                
                logger.info(f"✓ Retrieved cost data for 7 days, total cost: ${result['total_cost']:.2f}")
                
            finally:
                loop.close()
                
        except Exception as e:
            self.fail(f"Failed to get cost and usage: {str(e)}")
    
    def test_get_dimension_values_real(self):
        """Test get_dimension_values with real AWS data"""
        try:
            from cost_explorer_mcp import CostExplorerMCPServer
            
            server = CostExplorerMCPServer()
            
            # Prepare dates
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=30)
            
            # Create async function
            async def get_dimensions():
                result = await server.get_dimension_values(
                    dimension='SERVICE',
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                return result
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(get_dimensions())
                
                # Verify result
                self.assertIn('dimension', result)
                self.assertIn('values', result)
                self.assertEqual(result['dimension'], 'SERVICE')
                self.assertIsInstance(result['values'], list)
                self.assertGreater(len(result['values']), 0)
                
                logger.info(f"✓ Retrieved {len(result['values'])} service dimensions")
                
            finally:
                loop.close()
                
        except Exception as e:
            self.fail(f"Failed to get dimension values: {str(e)}")
    
    def test_process_mcp_request_real(self):
        """Test process_mcp_request with real request"""
        try:
            from cost_explorer_mcp import CostExplorerMCPServer
            
            server = CostExplorerMCPServer()
            
            # Prepare request
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7)
            
            request = {
                'method': 'get_cost_and_usage',
                'params': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'granularity': 'DAILY',
                    'metrics': ['UnblendedCost'],
                    'group_by': [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                }
            }
            
            # Process request
            async def process():
                result = await server.process_mcp_request(request)
                return result
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(process())
                
                # Verify result
                self.assertNotIn('error', result)
                self.assertIn('results', result)
                self.assertGreater(len(result['results']), 0)
                
                logger.info("✓ MCP request processed successfully")
                
            finally:
                loop.close()
                
        except Exception as e:
            self.fail(f"Failed to process MCP request: {str(e)}")
    
    def test_mcp_protocol_handler_real(self):
        """Test MCPProtocolHandler with real request"""
        try:
            from cost_explorer_mcp import MCPProtocolHandler
            
            handler = MCPProtocolHandler()
            
            # Prepare JSON-RPC request
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=3)
            
            request_data = json.dumps({
                "jsonrpc": "2.0",
                "id": "test_123",
                "method": "get_cost_and_usage",
                "params": {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'granularity': 'DAILY',
                    'metrics': ['UnblendedCost']
                }
            })
            
            # Handle request
            async def handle():
                result = await handler.handle_request(request_data)
                return result
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result_json = loop.run_until_complete(handle())
                result = json.loads(result_json)
                
                # Verify JSON-RPC response
                self.assertEqual(result['jsonrpc'], '2.0')
                self.assertEqual(result['id'], 'test_123')
                self.assertIn('result', result)
                self.assertNotIn('error', result)
                
                logger.info("✓ MCPProtocolHandler processed JSON-RPC request successfully")
                
            finally:
                loop.close()
                
        except Exception as e:
            self.fail(f"Failed to handle MCP protocol request: {str(e)}")


def run_all_tests():
    """Run all Cost Explorer MCP tests"""
    logger.info("Starting Cost Explorer MCP Real API Tests")
    logger.info("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCostExplorerMCPReal))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("COST EXPLORER MCP TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        logger.info("\n✓ All Cost Explorer MCP tests passed!")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)