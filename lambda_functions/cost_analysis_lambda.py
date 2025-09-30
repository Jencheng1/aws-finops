import json
import boto3
from datetime import datetime, timedelta

ce_client = boto3.client('ce')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    # Parse parameters
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters to dict
    params = {}
    for param in parameters:
        params[param.get('name', '')] = param.get('value', '')
    
    try:
        if 'get_cost_breakdown' in api_path:
            result = get_cost_breakdown(params)
        elif 'analyze_cost_trends' in api_path:
            result = analyze_cost_trends(params)
        elif 'identify_cost_anomalies' in api_path:
            result = identify_cost_anomalies(params)
        else:
            result = {'error': f'Unknown path: {api_path}'}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }

def get_cost_breakdown(params):
    days = int(params.get('days', '7'))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        cost_by_service = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if service not in cost_by_service:
                    cost_by_service[service] = 0
                cost_by_service[service] += cost
        
        sorted_costs = sorted(
            cost_by_service.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'period': f'{days} days',
            'total_cost': round(sum(cost_by_service.values()), 2),
            'cost_by_service': {k: round(v, 2) for k, v in sorted_costs[:10]}
        }
    except Exception as e:
        return {'error': f'Failed to get cost breakdown: {str(e)}'}

def analyze_cost_trends(params):
    days = int(params.get('days', '30'))
    service = params.get('service', '')
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        query_params = {
            'TimePeriod': {
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            'Granularity': 'DAILY',
            'Metrics': ['UnblendedCost']
        }
        
        if service:
            query_params['Filter'] = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service]
                }
            }
        
        response = ce_client.get_cost_and_usage(**query_params)
        
        daily_costs = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append({
                'date': date,
                'cost': round(cost, 2)
            })
        
        # Calculate trend
        if len(daily_costs) > 7:
            first_week_avg = sum(d['cost'] for d in daily_costs[:7]) / 7
            last_week_avg = sum(d['cost'] for d in daily_costs[-7:]) / 7
            if first_week_avg > 0:
                trend_percentage = ((last_week_avg - first_week_avg) / first_week_avg) * 100
            else:
                trend_percentage = 0
        else:
            trend_percentage = 0
        
        return {
            'period': f'{days} days',
            'service': service or 'All Services',
            'trend': {
                'percentage': round(trend_percentage, 2),
                'direction': 'increasing' if trend_percentage > 0 else 'decreasing'
            },
            'average_daily_cost': round(sum(d['cost'] for d in daily_costs) / len(daily_costs) if daily_costs else 0, 2),
            'data_points': len(daily_costs)
        }
    except Exception as e:
        return {'error': f'Failed to analyze trends: {str(e)}'}

def identify_cost_anomalies(params):
    threshold = float(params.get('threshold', '20'))
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        daily_costs = []
        for result in response['ResultsByTime']:
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append(cost)
        
        if not daily_costs:
            return {'anomalies_found': 0, 'anomalies': []}
        
        avg_cost = sum(daily_costs) / len(daily_costs)
        
        anomalies = []
        for i, cost in enumerate(daily_costs):
            if avg_cost > 0:
                deviation = ((cost - avg_cost) / avg_cost) * 100
                if abs(deviation) > threshold:
                    anomalies.append({
                        'date': (start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                        'cost': round(cost, 2),
                        'deviation_percentage': round(deviation, 2),
                        'type': 'spike' if deviation > 0 else 'drop'
                    })
        
        return {
            'anomalies_found': len(anomalies),
            'threshold_used': threshold,
            'average_daily_cost': round(avg_cost, 2),
            'anomalies': anomalies[:10]
        }
    except Exception as e:
        return {'error': f'Failed to identify anomalies: {str(e)}'}
