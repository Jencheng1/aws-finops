import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import asyncio
import concurrent.futures

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class FinOpsOrchestrator:
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.bedrock_client = boto3.client('bedrock-agent-runtime')
        
        # Agent Lambda function mappings
        self.agent_functions = {
            'ec2_agent': 'finops-copilot-ec2-agent',
            's3_agent': 'finops-copilot-s3-agent',
            'rds_agent': 'finops-copilot-rds-agent',
            'ri_sp_agent': 'finops-copilot-ri-sp-agent',
            'tagging_agent': 'finops-copilot-tagging-agent'
        }
    
    def parse_user_query(self, query: str) -> Dict[str, Any]:
        """Parse user query to determine which agents to invoke and what actions to take"""
        query_lower = query.lower()
        
        # Initialize analysis plan
        analysis_plan = {
            'agents_to_invoke': [],
            'actions': [],
            'priority': 'medium',
            'scope': 'general'
        }
        
        # Determine which agents to invoke based on query content
        if any(keyword in query_lower for keyword in ['ec2', 'instance', 'compute', 'server']):
            analysis_plan['agents_to_invoke'].append('ec2_agent')
            analysis_plan['actions'].append('analyze_ec2_utilization')
        
        if any(keyword in query_lower for keyword in ['s3', 'storage', 'bucket']):
            analysis_plan['agents_to_invoke'].append('s3_agent')
            analysis_plan['actions'].append('analyze_s3_storage')
        
        if any(keyword in query_lower for keyword in ['rds', 'database', 'db']):
            analysis_plan['agents_to_invoke'].append('rds_agent')
            analysis_plan['actions'].append('analyze_rds_utilization')
        
        if any(keyword in query_lower for keyword in ['reserved', 'savings', 'ri', 'sp']):
            analysis_plan['agents_to_invoke'].append('ri_sp_agent')
            analysis_plan['actions'].append('analyze_ri_opportunities')
        
        if any(keyword in query_lower for keyword in ['tag', 'tagging', 'compliance']):
            analysis_plan['agents_to_invoke'].append('tagging_agent')
            analysis_plan['actions'].append('analyze_tagging_compliance')
        
        # If no specific service mentioned, invoke all agents for comprehensive analysis
        if not analysis_plan['agents_to_invoke']:
            analysis_plan['agents_to_invoke'] = list(self.agent_functions.keys())
            analysis_plan['actions'] = ['comprehensive_analysis']
            analysis_plan['scope'] = 'comprehensive'
        
        # Determine priority based on keywords
        if any(keyword in query_lower for keyword in ['urgent', 'critical', 'high', 'immediate']):
            analysis_plan['priority'] = 'high'
        elif any(keyword in query_lower for keyword in ['low', 'minor', 'later']):
            analysis_plan['priority'] = 'low'
        
        # Determine analysis depth
        if any(keyword in query_lower for keyword in ['detailed', 'comprehensive', 'full', 'complete']):
            analysis_plan['depth'] = 'detailed'
        elif any(keyword in query_lower for keyword in ['quick', 'summary', 'brief']):
            analysis_plan['depth'] = 'summary'
        else:
            analysis_plan['depth'] = 'standard'
        
        return analysis_plan
    
    def invoke_agent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a specific agent Lambda function"""
        try:
            function_name = self.agent_functions.get(agent_name)
            if not function_name:
                return {'error': f'Unknown agent: {agent_name}'}
            
            logger.info(f"Invoking {agent_name} with payload: {payload}")
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                return {
                    'agent': agent_name,
                    'success': True,
                    'data': response_payload
                }
            else:
                return {
                    'agent': agent_name,
                    'success': False,
                    'error': response_payload
                }
                
        except Exception as e:
            logger.error(f"Error invoking {agent_name}: {str(e)}")
            return {
                'agent': agent_name,
                'success': False,
                'error': str(e)
            }
    
    def invoke_agents_parallel(self, agents_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Invoke multiple agents in parallel for better performance"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all agent invocations
            future_to_agent = {
                executor.submit(self.invoke_agent, payload['agent'], payload['payload']): payload['agent']
                for payload in agents_payload
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error getting result from {agent_name}: {str(e)}")
                    results.append({
                        'agent': agent_name,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def synthesize_results(self, agent_results: List[Dict[str, Any]], 
                          original_query: str) -> Dict[str, Any]:
        """Synthesize results from multiple agents into a coherent response"""
        try:
            synthesis = {
                'query': original_query,
                'timestamp': datetime.utcnow().isoformat(),
                'agents_consulted': [],
                'summary': {},
                'recommendations': [],
                'cost_impact': {},
                'next_steps': []
            }
            
            total_potential_savings = 0
            total_current_cost = 0
            all_recommendations = []
            
            # Process results from each agent
            for result in agent_results:
                if not result.get('success'):
                    continue
                
                agent_name = result['agent']
                agent_data = result['data']
                synthesis['agents_consulted'].append(agent_name)
                
                # Extract data from agent response
                if 'body' in agent_data:
                    body = json.loads(agent_data['body']) if isinstance(agent_data['body'], str) else agent_data['body']
                else:
                    body = agent_data
                
                # Extract summary information
                if 'summary' in body:
                    summary = body['summary']
                    synthesis['summary'][agent_name] = summary
                    
                    # Accumulate cost information
                    if 'total_monthly_cost' in summary:
                        total_current_cost += summary['total_monthly_cost']
                    if 'potential_monthly_savings' in summary:
                        total_potential_savings += summary['potential_monthly_savings']
                
                # Extract recommendations
                if 'recommendations' in body:
                    recommendations = body['recommendations']
                    for rec in recommendations:
                        rec['source_agent'] = agent_name
                        all_recommendations.append(rec)
            
            # Sort recommendations by priority and potential savings
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            all_recommendations.sort(
                key=lambda x: (
                    priority_order.get(x.get('priority', 'low'), 1),
                    x.get('estimated_monthly_savings', 0)
                ),
                reverse=True
            )
            
            synthesis['recommendations'] = all_recommendations[:10]  # Top 10 recommendations
            
            # Set cost impact
            synthesis['cost_impact'] = {
                'current_monthly_cost': total_current_cost,
                'potential_monthly_savings': total_potential_savings,
                'savings_percentage': (total_potential_savings / total_current_cost * 100) if total_current_cost > 0 else 0
            }
            
            # Generate next steps based on recommendations
            high_priority_recs = [r for r in all_recommendations if r.get('priority') == 'high']
            if high_priority_recs:
                synthesis['next_steps'].append(f"Address {len(high_priority_recs)} high-priority recommendations immediately")
            
            if total_potential_savings > 1000:
                synthesis['next_steps'].append("Schedule a detailed cost review meeting with stakeholders")
            
            synthesis['next_steps'].append("Set up automated monitoring for identified optimization opportunities")
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Error synthesizing results: {str(e)}")
            return {
                'error': 'Failed to synthesize agent results',
                'details': str(e),
                'raw_results': agent_results
            }
    
    def generate_natural_language_response(self, synthesis: Dict[str, Any]) -> str:
        """Generate a natural language response based on the synthesis"""
        try:
            query = synthesis.get('query', 'your request')
            agents_count = len(synthesis.get('agents_consulted', []))
            recommendations_count = len(synthesis.get('recommendations', []))
            cost_impact = synthesis.get('cost_impact', {})
            
            response_parts = []
            
            # Opening
            response_parts.append(f"I've analyzed {query} by consulting with {agents_count} specialized agents.")
            
            # Cost summary
            current_cost = cost_impact.get('current_monthly_cost', 0)
            potential_savings = cost_impact.get('potential_monthly_savings', 0)
            savings_percentage = cost_impact.get('savings_percentage', 0)
            
            if current_cost > 0:
                response_parts.append(f"Your current estimated monthly AWS cost is ${current_cost:,.2f}.")
            
            if potential_savings > 0:
                response_parts.append(f"I've identified potential monthly savings of ${potential_savings:,.2f} ({savings_percentage:.1f}% reduction).")
            
            # Recommendations summary
            if recommendations_count > 0:
                high_priority = len([r for r in synthesis['recommendations'] if r.get('priority') == 'high'])
                response_parts.append(f"I found {recommendations_count} optimization opportunities, with {high_priority} high-priority items.")
                
                # Highlight top recommendation
                top_rec = synthesis['recommendations'][0]
                response_parts.append(f"The top recommendation is: {top_rec.get('recommendation', 'N/A')}")
            
            # Next steps
            next_steps = synthesis.get('next_steps', [])
            if next_steps:
                response_parts.append("Recommended next steps:")
                for step in next_steps[:3]:  # Top 3 next steps
                    response_parts.append(f"• {step}")
            
            return " ".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error generating natural language response: {str(e)}")
            return f"I've completed the analysis but encountered an issue generating the summary. Please check the detailed results."

def lambda_handler(event, context):
    """AWS Lambda handler for the FinOps Orchestrator"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize orchestrator
        orchestrator = FinOpsOrchestrator()
        
        # Extract parameters
        user_query = event.get('query', 'Analyze my AWS costs')
        analysis_depth = event.get('depth', 'standard')
        days = event.get('days', 30)
        
        # Parse the user query to create analysis plan
        analysis_plan = orchestrator.parse_user_query(user_query)
        logger.info(f"Analysis plan: {analysis_plan}")
        
        # Prepare agent invocations
        agents_payload = []
        for agent in analysis_plan['agents_to_invoke']:
            payload = {
                'action': 'analyze_all',
                'days': days,
                'depth': analysis_depth
            }
            
            agents_payload.append({
                'agent': agent,
                'payload': payload
            })
        
        # Invoke agents in parallel
        logger.info(f"Invoking {len(agents_payload)} agents in parallel")
        agent_results = orchestrator.invoke_agents_parallel(agents_payload)
        
        # Synthesize results
        synthesis = orchestrator.synthesize_results(agent_results, user_query)
        
        # Generate natural language response
        natural_response = orchestrator.generate_natural_language_response(synthesis)
        
        # Prepare final response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'query': user_query,
                'natural_response': natural_response,
                'detailed_analysis': synthesis,
                'analysis_plan': analysis_plan,
                'agent_results': agent_results,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
        logger.info("Orchestrator analysis completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in orchestrator lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Orchestrator error',
                'details': str(e),
                'query': event.get('query', 'unknown')
            })
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'query': 'What are my biggest cost optimization opportunities?',
        'days': 30,
        'depth': 'detailed'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
