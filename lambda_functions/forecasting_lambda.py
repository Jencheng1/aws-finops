import json
import boto3
from datetime import datetime, timedelta
import statistics

ce_client = boto3.client('ce')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    
    params = {}
    for param in parameters:
        params[param.get('name', '')] = param.get('value', '')
    
    try:
        if 'forecast_costs' in api_path:
            result = forecast_costs(params)
        elif 'analyze_growth_trends' in api_path:
            result = analyze_growth_trends(params)
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

def forecast_costs(params):
    months_to_forecast = int(params.get('months', '3'))
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        monthly_costs = []
        for result in response['ResultsByTime']:
            cost = float(result['Total']['UnblendedCost']['Amount'])
            monthly_costs.append(cost)
        
        if len(monthly_costs) >= 2:
            growth_rates = []
            for i in range(1, len(monthly_costs)):
                if monthly_costs[i-1] > 0:
                    rate = (monthly_costs[i] - monthly_costs[i-1]) / monthly_costs[i-1]
                    growth_rates.append(rate)
            
            avg_growth_rate = statistics.mean(growth_rates) if growth_rates else 0
        else:
            avg_growth_rate = 0
        
        current_cost = monthly_costs[-1] if monthly_costs else 0
        forecasts = []
        
        for month in range(1, months_to_forecast + 1):
            forecasted_cost = current_cost * ((1 + avg_growth_rate) ** month)
            
            if len(monthly_costs) > 2:
                cost_variance = statistics.stdev(monthly_costs) / statistics.mean(monthly_costs)
                confidence = max(0.5, 1 - (cost_variance * month * 0.1))
            else:
                confidence = 0.7
            
            forecasts.append({
                'month': month,
                'predicted_cost': round(forecasted_cost, 2),
                'confidence': round(confidence, 2),
                'date': (end_date + timedelta(days=30*month)).strftime('%Y-%m')
            })
        
        return {
            'forecast_period': f'{months_to_forecast} months',
            'current_monthly_cost': round(current_cost, 2),
            'average_growth_rate': f'{avg_growth_rate*100:.1f}%',
            'forecasts': forecasts,
            'historical_data_points': len(monthly_costs)
        }
    except Exception as e:
        return {'error': f'Failed to forecast costs: {str(e)}'}

def analyze_growth_trends(params):
    service = params.get('service', '')
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    try:
        query_params = {
            'TimePeriod': {
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            'Granularity': 'MONTHLY',
            'Metrics': ['UnblendedCost'],
            'GroupBy': [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        }
        
        response = ce_client.get_cost_and_usage(**query_params)
        
        service_trends = {}
        
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                svc = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if svc not in service_trends:
                    service_trends[svc] = []
                service_trends[svc].append(cost)
        
        growth_analysis = []
        for svc, costs in service_trends.items():
            if len(costs) >= 2 and costs[0] > 0:
                growth_rate = ((costs[-1] - costs[0]) / costs[0]) * 100
                growth_analysis.append({
                    'service': svc,
                    'initial_cost': round(costs[0], 2),
                    'current_cost': round(costs[-1], 2),
                    'growth_percentage': round(growth_rate, 1),
                    'trend': 'increasing' if growth_rate > 0 else 'decreasing'
                })
        
        growth_analysis.sort(key=lambda x: x['growth_percentage'], reverse=True)
        
        return {
            'analysis_period': '3 months',
            'top_growing_services': growth_analysis[:5],
            'declining_services': [s for s in growth_analysis if s['growth_percentage'] < 0][:5]
        }
    except Exception as e:
        return {'error': f'Failed to analyze growth trends: {str(e)}'}
