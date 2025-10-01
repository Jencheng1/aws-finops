import json
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import pickle
import base64

ce = boto3.client('ce')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function for budget prediction using ML models
    """
    try:
        # Extract parameters
        days_ahead = event.get('days_ahead', 30)
        months_history = event.get('months_history', 6)
        user_id = event.get('user_id', 'anonymous')
        session_id = event.get('session_id', str(datetime.now().timestamp()))
        
        # Fetch historical cost data
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
        
        # Process data
        costs = []
        for result in response['ResultsByTime']:
            costs.append({
                'date': result['TimePeriod']['Start'],
                'cost': float(result['Total']['UnblendedCost']['Amount'])
            })
        
        df = pd.DataFrame(costs)
        df['date'] = pd.to_datetime(df['date'])
        df['days_from_start'] = (df['date'] - df['date'].min()).dt.days
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        
        # Train model
        features = ['days_from_start', 'day_of_week', 'day_of_month', 'month']
        X = df[features]
        y = df['cost']
        
        # Random Forest model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Make predictions
        last_date = df['date'].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )
        
        future_df = pd.DataFrame({
            'date': future_dates,
            'days_from_start': range(
                df['days_from_start'].max() + 1,
                df['days_from_start'].max() + days_ahead + 1
            ),
            'day_of_week': future_dates.dayofweek,
            'day_of_month': future_dates.day,
            'month': future_dates.month
        })
        
        predictions = model.predict(future_df[features])
        
        # Calculate confidence intervals
        std_dev = np.std(y) * 0.1  # Simplified confidence interval
        
        # Prepare response
        prediction_results = {
            'predictions': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'predicted_cost': float(cost),
                    'lower_bound': float(max(0, cost - 1.96 * std_dev)),
                    'upper_bound': float(cost + 1.96 * std_dev)
                }
                for date, cost in zip(future_dates, predictions)
            ],
            'summary': {
                'total_predicted': float(predictions.sum()),
                'average_daily': float(predictions.mean()),
                'confidence_level': '95%',
                'model_accuracy': float(model.score(X, y))
            },
            'metadata': {
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Store feedback context in DynamoDB
        feedback_table = dynamodb.Table('FinOpsAIContext')
        feedback_table.put_item(
            Item={
                'context_id': f"prediction_{session_id}",
                'user_id': user_id,
                'prediction_results': json.dumps(prediction_results),
                'model_type': 'RandomForest',
                'features_used': features,
                'training_period': f"{start_date} to {end_date}",
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(prediction_results)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }