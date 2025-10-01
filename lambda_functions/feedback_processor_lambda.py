import json
import boto3
from datetime import datetime
import uuid

def lambda_handler(event, context):
    """
    Lambda function for processing user feedback
    """
    try:
        # Initialize clients
        dynamodb = boto3.resource('dynamodb')
        comprehend = boto3.client('comprehend')
        
        # Get feedback table
        feedback_table = dynamodb.Table('FinOpsFeedback')
        context_table = dynamodb.Table('FinOpsAIContext')
        
        # Extract feedback data
        feedback_type = event.get('feedback_type', 'general')
        feedback_text = event.get('feedback_text', '')
        rating = event.get('rating', 3)
        user_id = event.get('user_id', 'unknown')
        session_id = event.get('session_id', 'unknown')
        feedback_context = event.get('context', {})
        
        # Generate feedback ID
        feedback_id = f"fb_{str(uuid.uuid4())}"
        timestamp = datetime.now().isoformat()
        
        # Analyze sentiment (if feedback text provided)
        sentiment = 'NEUTRAL'
        sentiment_scores = {}
        
        if feedback_text and len(feedback_text) > 10:
            try:
                sentiment_response = comprehend.detect_sentiment(
                    Text=feedback_text,
                    LanguageCode='en'
                )
                sentiment = sentiment_response['Sentiment']
                sentiment_scores = sentiment_response['SentimentScore']
            except:
                # Fallback sentiment based on rating
                if rating >= 4:
                    sentiment = 'POSITIVE'
                elif rating <= 2:
                    sentiment = 'NEGATIVE'
                else:
                    sentiment = 'NEUTRAL'
        else:
            # Simple sentiment from rating
            if rating >= 4:
                sentiment = 'POSITIVE'
            elif rating <= 2:
                sentiment = 'NEGATIVE'
        
        # Store feedback in DynamoDB
        feedback_item = {
            'feedback_id': feedback_id,
            'timestamp': timestamp,
            'user_id': user_id,
            'session_id': session_id,
            'feedback_type': feedback_type,
            'feedback_text': feedback_text,
            'rating': rating,
            'sentiment': sentiment,
            'sentiment_scores': json.dumps(sentiment_scores) if sentiment_scores else '{}',
            'context': json.dumps(feedback_context)
        }
        
        feedback_table.put_item(Item=feedback_item)
        
        # Update AI context based on feedback
        if feedback_type in ['prediction_accuracy', 'recommendation_usefulness']:
            context_item = {
                'context_id': f"ctx_{str(uuid.uuid4())}",
                'timestamp': timestamp,
                'context_type': feedback_type,
                'user_id': user_id,
                'feedback_summary': {
                    'rating': rating,
                    'sentiment': sentiment,
                    'key_point': feedback_text[:100] if feedback_text else 'No text provided'
                },
                'original_context': json.dumps(feedback_context)
            }
            
            context_table.put_item(Item=context_item)
        
        # Prepare response
        result = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'feedback_id': feedback_id,
                'message': 'Feedback processed successfully',
                'sentiment': sentiment,
                'improvements': {
                    'immediate': 'Your feedback has been recorded',
                    'future': 'We will use this to improve our predictions and recommendations'
                }
            })
        }
        
    except Exception as e:
        result = {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to process feedback'
            })
        }
    
    return result