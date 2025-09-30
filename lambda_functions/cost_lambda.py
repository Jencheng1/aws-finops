import json
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    
    api_path = event.get('apiPath', '')
    params = {}
    for p in event.get('parameters', []):
        params[p.get('name', '')] = p.get('value', '')
    
    if 'get_cost_breakdown' in api_path:
        days = int(params.get('days', '7'))
        end = datetime.now().date()
        start = end - timedelta(days=days)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        costs = {}
        for r in response['ResultsByTime']:
            for g in r['Groups']:
                svc = g['Keys'][0]
                cost = float(g['Metrics']['UnblendedCost']['Amount'])
                costs[svc] = costs.get(svc, 0) + cost
        
        sorted_costs = sorted(costs.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            'total_cost': sum(costs.values()),
            'top_services': dict(sorted_costs[:5])
        }
    else:
        result = {'message': 'Function called'}
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup', ''),
            'apiPath': api_path,
            'httpMethod': event.get('httpMethod', 'POST'),
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
        }
    }
