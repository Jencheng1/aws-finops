import json
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    
    # Get API path from event
    api_path = event.get('apiPath', '')
    
    # Parse parameters
    params = {}
    for param in event.get('parameters', []):
        params[param['name']] = param['value']
    
    # Route to appropriate function
    if '/getCostBreakdown' in api_path:
        result = get_cost_breakdown(params)
    elif '/analyzeTrends' in api_path:
        result = analyze_trends(params)
    elif '/getOptimizations' in api_path:
        result = get_optimizations(params)
    else:
        result = {'error': 'Unknown API path'}
    
    # Return Bedrock-formatted response
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

def get_cost_breakdown(params):
    days = int(params.get('days', '7'))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                costs[service] = costs.get(service, 0) + cost
        
        sorted_costs = sorted(costs.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_cost': round(sum(costs.values()), 2),
            'cost_by_service': {k: round(v, 2) for k, v in sorted_costs[:10]},
            'period': f'{days} days'
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_trends(params):
    days = int(params.get('days', '30'))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        daily_costs = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append({'date': date, 'cost': round(cost, 2)})
        
        # Calculate trend
        if len(daily_costs) > 7:
            first_week = sum(d['cost'] for d in daily_costs[:7]) / 7
            last_week = sum(d['cost'] for d in daily_costs[-7:]) / 7
            trend = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
        else:
            trend = 0
        
        return {
            'trend_percentage': round(trend, 2),
            'trend_direction': 'increasing' if trend > 0 else 'decreasing',
            'average_daily_cost': round(sum(d['cost'] for d in daily_costs) / len(daily_costs), 2),
            'period': f'{days} days'
        }
    except Exception as e:
        return {'error': str(e)}

def get_optimizations(params):
    # Simple optimization recommendations
    return {
        'recommendations': [
            {
                'type': 'Reserved Instances',
                'potential_savings': '20-40%',
                'description': 'Purchase RIs for consistently running instances'
            },
            {
                'type': 'Spot Instances',
                'potential_savings': 'Up to 90%',
                'description': 'Use Spot for fault-tolerant workloads'
            },
            {
                'type': 'Right-sizing',
                'potential_savings': '15-30%',
                'description': 'Adjust instance sizes based on utilization'
            }
        ]
    }
