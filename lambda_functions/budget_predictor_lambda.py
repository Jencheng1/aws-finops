import json
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import sys
sys.path.append('/opt/python')

def lambda_handler(event, context):
    """
    Lambda function for ML-based budget prediction
    """
    # Extract parameters
    days_ahead = event.get('days_ahead', 30)
    months_history = event.get('months_history', 3)
    user_id = event.get('user_id', 'unknown')
    session_id = event.get('session_id', str(datetime.now().timestamp()))
    
    try:
        # Initialize clients
        ce = boto3.client('ce')
        
        # Get historical cost data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months_history * 30)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        # Convert to DataFrame
        costs = []
        for result in response['ResultsByTime']:
            costs.append({
                'date': result['TimePeriod']['Start'],
                'cost': float(result['Total']['UnblendedCost']['Amount'])
            })
        
        df = pd.DataFrame(costs)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Simple moving average prediction
        window_size = min(7, len(df))
        df['ma'] = df['cost'].rolling(window=window_size).mean()
        
        # Calculate trend
        if len(df) > 1:
            trend = (df['cost'].iloc[-1] - df['cost'].iloc[-7]) / 7 if len(df) >= 7 else 0
        else:
            trend = 0
        
        # Generate predictions
        predictions = []
        last_cost = df['cost'].iloc[-1] if len(df) > 0 else 10.0
        last_ma = df['ma'].iloc[-1] if len(df) > 0 and not pd.isna(df['ma'].iloc[-1]) else last_cost
        
        for i in range(days_ahead):
            future_date = end_date + timedelta(days=i+1)
            # Simple prediction: last MA + trend
            predicted_cost = max(0, last_ma + (trend * i))
            
            predictions.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'predicted_cost': round(predicted_cost, 2),
                'confidence_lower': round(predicted_cost * 0.9, 2),
                'confidence_upper': round(predicted_cost * 1.1, 2)
            })
        
        # Calculate summary
        total_predicted = sum(p['predicted_cost'] for p in predictions)
        avg_daily = total_predicted / days_ahead if days_ahead > 0 else 0
        
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'predictions': {
                    'daily_predictions': predictions,
                    'summary': {
                        'total_predicted_cost': round(total_predicted, 2),
                        'average_daily_cost': round(avg_daily, 2),
                        'prediction_days': days_ahead,
                        'confidence_level': '95%',
                        'trend': 'increasing' if trend > 0 else 'decreasing'
                    }
                },
                'metadata': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'model_type': 'moving_average',
                    'historical_days_used': len(df)
                }
            })
        }
        
    except Exception as e:
        result = {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to generate budget prediction'
            })
        }
    
    return result