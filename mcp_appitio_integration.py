#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Integration for Appitio FinOps Platform
"""

import boto3
import json
import asyncio
import websockets
from datetime import datetime
import uuid

class MCPAppitioServer:
    """
    MCP Server for Appitio FinOps integration
    Provides standardized interface for AI agents to access FinOps data
    """
    
    def __init__(self, config):
        self.config = config
        self.bedrock = boto3.client('bedrock-agent-runtime')
        self.ce = boto3.client('ce')
        self.agent_id = config['agents'][0]['agent_id']
        self.alias_id = config['agents'][0]['alias_id']
        
    async def handle_request(self, websocket, path):
        """Handle incoming MCP requests"""
        async for message in websocket:
            try:
                request = json.loads(message)
                response = await self.process_request(request)
                await websocket.send(json.dumps(response))
            except Exception as e:
                error_response = {
                    "type": "error",
                    "error": str(e)
                }
                await websocket.send(json.dumps(error_response))
    
    async def process_request(self, request):
        """Process MCP request and route to appropriate handler"""
        request_type = request.get('type')
        
        if request_type == 'initialize':
            return await self.handle_initialize()
        elif request_type == 'list_tools':
            return await self.handle_list_tools()
        elif request_type == 'execute_tool':
            return await self.handle_execute_tool(request)
        elif request_type == 'get_context':
            return await self.handle_get_context(request)
        else:
            return {"type": "error", "error": f"Unknown request type: {request_type}"}
    
    async def handle_initialize(self):
        """Initialize MCP connection"""
        return {
            "type": "initialize_response",
            "protocol_version": "1.0",
            "capabilities": {
                "tools": True,
                "context": True,
                "streaming": True
            },
            "server_info": {
                "name": "Appitio FinOps MCP Server",
                "version": "1.0"
            }
        }
    
    async def handle_list_tools(self):
        """List available tools"""
        return {
            "type": "tools_list",
            "tools": [
                {
                    "name": "get_cost_analysis",
                    "description": "Get detailed AWS cost analysis",
                    "parameters": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to analyze",
                            "default": 7
                        }
                    }
                },
                {
                    "name": "get_optimization_recommendations",
                    "description": "Get AI-powered cost optimization recommendations",
                    "parameters": {}
                },
                {
                    "name": "forecast_costs",
                    "description": "Forecast future AWS costs",
                    "parameters": {
                        "months": {
                            "type": "integer",
                            "description": "Number of months to forecast",
                            "default": 3
                        }
                    }
                },
                {
                    "name": "analyze_service_costs",
                    "description": "Analyze costs for specific AWS service",
                    "parameters": {
                        "service": {
                            "type": "string",
                            "description": "AWS service name (e.g., EC2, RDS)"
                        }
                    }
                }
            ]
        }
    
    async def handle_execute_tool(self, request):
        """Execute a specific tool"""
        tool_name = request.get('tool')
        parameters = request.get('parameters', {})
        
        if tool_name == 'get_cost_analysis':
            result = await self.get_cost_analysis(parameters)
        elif tool_name == 'get_optimization_recommendations':
            result = await self.get_optimization_recommendations()
        elif tool_name == 'forecast_costs':
            result = await self.forecast_costs(parameters)
        elif tool_name == 'analyze_service_costs':
            result = await self.analyze_service_costs(parameters)
        else:
            return {"type": "error", "error": f"Unknown tool: {tool_name}"}
        
        return {
            "type": "tool_result",
            "tool": tool_name,
            "result": result
        }
    
    async def get_cost_analysis(self, params):
        """Get cost analysis using Bedrock agent"""
        days = params.get('days', 7)
        
        # Call Bedrock agent
        session_id = f"mcp-{uuid.uuid4()}"
        prompt = f"Analyze my AWS costs for the last {days} days and provide a detailed breakdown"
        
        response = self.bedrock.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        # Extract response
        result_text = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                result_text += event['chunk']['bytes'].decode('utf-8')
        
        return {
            "analysis": result_text,
            "period": f"{days} days",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_optimization_recommendations(self):
        """Get optimization recommendations"""
        session_id = f"mcp-{uuid.uuid4()}"
        prompt = "Provide comprehensive cost optimization recommendations based on current AWS usage"
        
        response = self.bedrock.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        result_text = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                result_text += event['chunk']['bytes'].decode('utf-8')
        
        return {
            "recommendations": result_text,
            "timestamp": datetime.now().isoformat()
        }
    
    async def forecast_costs(self, params):
        """Forecast future costs"""
        months = params.get('months', 3)
        session_id = f"mcp-{uuid.uuid4()}"
        prompt = f"Forecast my AWS costs for the next {months} months based on current trends"
        
        response = self.bedrock.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        result_text = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                result_text += event['chunk']['bytes'].decode('utf-8')
        
        return {
            "forecast": result_text,
            "period": f"{months} months",
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_service_costs(self, params):
        """Analyze specific service costs"""
        service = params.get('service', 'EC2')
        session_id = f"mcp-{uuid.uuid4()}"
        prompt = f"Analyze costs specifically for {service} service and provide insights"
        
        response = self.bedrock.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        result_text = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                result_text += event['chunk']['bytes'].decode('utf-8')
        
        return {
            "service": service,
            "analysis": result_text,
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_get_context(self, request):
        """Get context information"""
        context_type = request.get('context_type', 'account')
        
        if context_type == 'account':
            return {
                "type": "context",
                "context": {
                    "account_id": self.config['account_id'],
                    "region": self.config['region'],
                    "deployment_time": self.config['deployment_time']
                }
            }
        elif context_type == 'cost_summary':
            # Get current month cost
            ce = boto3.client('ce')
            now = datetime.now()
            start = now.replace(day=1).strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
            
            response = ce.get_cost_and_usage(
                TimePeriod={'Start': start, 'End': end},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            total = sum(float(r['Total']['UnblendedCost']['Amount']) 
                       for r in response['ResultsByTime'])
            
            return {
                "type": "context",
                "context": {
                    "current_month_cost": total,
                    "currency": "USD",
                    "period": f"{start} to {end}"
                }
            }
    
    async def start_server(self, host='0.0.0.0', port=8765):
        """Start MCP WebSocket server"""
        print(f"Starting MCP server on {host}:{port}")
        async with websockets.serve(self.handle_request, host, port):
            print(f"MCP server running on ws://{host}:{port}")
            await asyncio.Future()  # Run forever


class MCPClient:
    """Example MCP client for testing"""
    
    async def test_connection(self):
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            # Initialize
            await websocket.send(json.dumps({"type": "initialize"}))
            response = await websocket.recv()
            print("Initialize:", json.loads(response))
            
            # List tools
            await websocket.send(json.dumps({"type": "list_tools"}))
            response = await websocket.recv()
            print("Tools:", json.loads(response))
            
            # Execute tool
            await websocket.send(json.dumps({
                "type": "execute_tool",
                "tool": "get_cost_analysis",
                "parameters": {"days": 7}
            }))
            response = await websocket.recv()
            print("Cost Analysis:", json.loads(response))


def create_mcp_config():
    """Create MCP configuration for Appitio"""
    mcp_config = {
        "mcp_version": "1.0",
        "server": {
            "host": "0.0.0.0",
            "port": 8765,
            "protocol": "websocket"
        },
        "tools": [
            {
                "name": "get_cost_analysis",
                "endpoint": "/tools/cost_analysis",
                "description": "Get AWS cost analysis"
            },
            {
                "name": "get_optimization_recommendations",
                "endpoint": "/tools/optimizations",
                "description": "Get optimization recommendations"
            },
            {
                "name": "forecast_costs",
                "endpoint": "/tools/forecast",
                "description": "Forecast future costs"
            }
        ],
        "authentication": {
            "type": "api_key",
            "header": "X-MCP-API-Key"
        }
    }
    
    with open('mcp_config.json', 'w') as f:
        json.dump(mcp_config, f, indent=2)
    
    print("Created mcp_config.json")


if __name__ == "__main__":
    # Load configuration
    with open('finops_config.json', 'r') as f:
        config = json.load(f)
    
    # Create MCP configuration
    create_mcp_config()
    
    # Start server
    server = MCPAppitioServer(config)
    asyncio.run(server.start_server())