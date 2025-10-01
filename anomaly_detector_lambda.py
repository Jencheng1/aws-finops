import json
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ce = boto3.client('ce')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda function for cost anomaly detection
    """
    try:
        # Extract parameters
        lookback_days = event.get('lookback_days', 30)
        user_id = event.get('user_id', 'anonymous')
        session_id = event.get('session_id', str(datetime.now().timestamp()))
        anomaly_threshold = event.get('threshold', 2.0)
        
        # Fetch historical cost data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=lookback_days)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        # Process data
        daily_costs = []
        service_data = {}
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            total_daily_cost = 0
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                total_daily_cost += cost
                
                if service not in service_data:
                    service_data[service] = []
                service_data[service].append(cost)
            
            daily_costs.append({
                'date': date,
                'cost': total_daily_cost
            })
        
        # Detect daily anomalies
        costs = [d['cost'] for d in daily_costs]
        mean_cost = np.mean(costs)
        std_cost = np.std(costs)
        
        anomalies = []
        for i, daily in enumerate(daily_costs):
            if std_cost > 0:
                z_score = (daily['cost'] - mean_cost) / std_cost
                if abs(z_score) > anomaly_threshold:
                    anomalies.append({
                        'date': daily['date'],
                        'cost': daily['cost'],
                        'expected_cost': mean_cost,
                        'z_score': z_score,
                        'severity': 'high' if abs(z_score) > 3 else 'medium'
                    })
        
        # Detect service-level anomalies
        service_anomalies = []
        for service, costs in service_data.items():
            if len(costs) > 1:
                service_mean = np.mean(costs)
                service_std = np.std(costs)
                
                if service_std > 0:
                    recent_cost = costs[-1]
                    z_score = (recent_cost - service_mean) / service_std
                    
                    if abs(z_score) > anomaly_threshold:
                        service_anomalies.append({
                            'service': service,
                            'recent_cost': recent_cost,
                            'expected_cost': service_mean,
                            'z_score': z_score
                        })
        
        # Prepare results
        results = {
            'daily_anomalies': anomalies,
            'service_anomalies': sorted(service_anomalies, 
                                      key=lambda x: abs(x['z_score']), 
                                      reverse=True)[:10],
            'summary': {
                'total_anomalies': len(anomalies),
                'anomaly_rate': (len(anomalies) / len(daily_costs) * 100) if daily_costs else 0,
                'highest_z_score': max([abs(a['z_score']) for a in anomalies]) if anomalies else 0
            },
            'metadata': {
                'user_id': user_id,
                'session_id': session_id,
                'lookback_days': lookback_days,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Store results in DynamoDB
        context_table = dynamodb.Table('FinOpsAIContext')
        context_table.put_item(
            Item={
                'context_id': f"anomaly_{session_id}",
                'user_id': user_id,
                'anomaly_results': json.dumps(results, default=str),
                'detection_method': 'z-score',
                'threshold': anomaly_threshold,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }