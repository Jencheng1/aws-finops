import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
comprehend = boto3.client('comprehend')

def lambda_handler(event, context):
    """
    Process human feedback and store context for AI improvement
    """
    try:
        # Extract feedback data
        feedback_type = event.get('feedback_type', 'general')
        user_id = event.get('user_id', 'anonymous')
        session_id = event.get('session_id', str(datetime.now().timestamp()))
        feedback_text = event.get('feedback_text', '')
        rating = event.get('rating', 0)
        context_data = event.get('context', {})
        
        # Generate unique feedback ID
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Analyze sentiment of feedback
        sentiment = 'NEUTRAL'
        sentiment_scores = {}
        
        if feedback_text:
            try:
                sentiment_response = comprehend.detect_sentiment(
                    Text=feedback_text,
                    LanguageCode='en'
                )
                sentiment = sentiment_response['Sentiment']
                sentiment_scores = sentiment_response['SentimentScore']
            except Exception as e:
                print(f"Error analyzing sentiment: {e}")
        
        # Process feedback based on type
        processed_feedback = {
            'feedback_id': feedback_id,
            'timestamp': timestamp,
            'user_id': user_id,
            'session_id': session_id,
            'feedback_type': feedback_type,
            'feedback_text': feedback_text,
            'rating': rating,
            'sentiment': sentiment,
            'sentiment_scores': sentiment_scores,
            'context': context_data
        }
        
        # Store in DynamoDB
        feedback_table = dynamodb.Table('FinOpsFeedback')
        
        # Convert float values to Decimal for DynamoDB
        processed_feedback = json.loads(json.dumps(processed_feedback), parse_float=Decimal)
        
        feedback_table.put_item(Item=processed_feedback)
        
        # Process specific feedback types
        if feedback_type == 'prediction_accuracy':
            process_prediction_feedback(processed_feedback)
        elif feedback_type == 'recommendation_usefulness':
            process_recommendation_feedback(processed_feedback)
        elif feedback_type == 'false_positive':
            process_false_positive_feedback(processed_feedback)
        elif feedback_type == 'missed_opportunity':
            process_missed_opportunity_feedback(processed_feedback)
        
        # Update AI context based on feedback
        update_ai_context(processed_feedback)
        
        # Generate response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'feedback_id': feedback_id,
                'message': 'Feedback processed successfully',
                'sentiment': sentiment,
                'improvements_planned': get_improvement_suggestions(feedback_type, sentiment)
            })
        }
        
        return response
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_prediction_feedback(feedback):
    """Process feedback about prediction accuracy"""
    context_table = dynamodb.Table('FinOpsAIContext')
    
    # Extract prediction details
    prediction_id = feedback['context'].get('prediction_id')
    actual_cost = feedback['context'].get('actual_cost')
    predicted_cost = feedback['context'].get('predicted_cost')
    
    if prediction_id and actual_cost and predicted_cost:
        # Calculate accuracy
        accuracy_error = abs(float(actual_cost) - float(predicted_cost)) / float(actual_cost) * 100
        
        # Store accuracy feedback
        context_table.put_item(
            Item={
                'context_id': f"accuracy_{prediction_id}",
                'feedback_id': feedback['feedback_id'],
                'prediction_id': prediction_id,
                'actual_cost': Decimal(str(actual_cost)),
                'predicted_cost': Decimal(str(predicted_cost)),
                'accuracy_error': Decimal(str(accuracy_error)),
                'user_feedback': feedback['feedback_text'],
                'timestamp': feedback['timestamp']
            }
        )

def process_recommendation_feedback(feedback):
    """Process feedback about recommendation usefulness"""
    context_table = dynamodb.Table('FinOpsAIContext')
    
    recommendation_id = feedback['context'].get('recommendation_id')
    recommendation_type = feedback['context'].get('recommendation_type')
    was_implemented = feedback['context'].get('implemented', False)
    actual_savings = feedback['context'].get('actual_savings', 0)
    
    if recommendation_id:
        context_table.put_item(
            Item={
                'context_id': f"recommendation_{recommendation_id}",
                'feedback_id': feedback['feedback_id'],
                'recommendation_id': recommendation_id,
                'recommendation_type': recommendation_type,
                'was_implemented': was_implemented,
                'actual_savings': Decimal(str(actual_savings)),
                'usefulness_rating': feedback['rating'],
                'user_feedback': feedback['feedback_text'],
                'timestamp': feedback['timestamp']
            }
        )

def process_false_positive_feedback(feedback):
    """Process feedback about false positive detections"""
    context_table = dynamodb.Table('FinOpsAIContext')
    
    resource_id = feedback['context'].get('resource_id')
    detection_type = feedback['context'].get('detection_type')
    reason = feedback['context'].get('reason', 'Not specified')
    
    if resource_id:
        context_table.put_item(
            Item={
                'context_id': f"false_positive_{resource_id}_{feedback['timestamp']}",
                'feedback_id': feedback['feedback_id'],
                'resource_id': resource_id,
                'detection_type': detection_type,
                'false_positive_reason': reason,
                'user_explanation': feedback['feedback_text'],
                'timestamp': feedback['timestamp']
            }
        )

def process_missed_opportunity_feedback(feedback):
    """Process feedback about missed optimization opportunities"""
    context_table = dynamodb.Table('FinOpsAIContext')
    
    opportunity_type = feedback['context'].get('opportunity_type')
    estimated_savings = feedback['context'].get('estimated_savings', 0)
    
    context_table.put_item(
        Item={
            'context_id': f"missed_{feedback['feedback_id']}",
            'feedback_id': feedback['feedback_id'],
            'opportunity_type': opportunity_type,
            'estimated_savings': Decimal(str(estimated_savings)),
            'user_suggestion': feedback['feedback_text'],
            'timestamp': feedback['timestamp']
        }
    )

def update_ai_context(feedback):
    """Update general AI context based on feedback"""
    context_table = dynamodb.Table('FinOpsAIContext')
    
    # Store general feedback for model improvement
    context_table.put_item(
        Item={
            'context_id': f"general_feedback_{feedback['feedback_id']}",
            'feedback_id': feedback['feedback_id'],
            'user_id': feedback['user_id'],
            'feedback_type': feedback['feedback_type'],
            'sentiment': feedback['sentiment'],
            'rating': feedback['rating'],
            'feedback_text': feedback['feedback_text'],
            'timestamp': feedback['timestamp'],
            'ttl': int((datetime.now() + timedelta(days=90)).timestamp())  # 90-day retention
        }
    )

def get_improvement_suggestions(feedback_type, sentiment):
    """Generate improvement suggestions based on feedback"""
    suggestions = {
        'prediction_accuracy': {
            'NEGATIVE': 'We will retrain our models with your feedback to improve accuracy',
            'POSITIVE': 'Thank you! We will continue to refine our predictions',
            'NEUTRAL': 'Your feedback helps us calibrate our models'
        },
        'recommendation_usefulness': {
            'NEGATIVE': 'We will adjust our recommendation engine based on your input',
            'POSITIVE': 'Great! We will prioritize similar recommendations',
            'NEUTRAL': 'We will analyze this pattern for future improvements'
        },
        'false_positive': {
            'NEGATIVE': 'We will update our detection algorithms to reduce false positives',
            'POSITIVE': 'Thank you for confirming. We will adjust thresholds',
            'NEUTRAL': 'We will investigate this case to improve accuracy'
        },
        'missed_opportunity': {
            'NEGATIVE': 'We will enhance our scanning to catch more opportunities',
            'POSITIVE': 'Thank you! We will add this pattern to our detection',
            'NEUTRAL': 'We will analyze this for future detection'
        }
    }
    
    return suggestions.get(feedback_type, {}).get(sentiment, 'Thank you for your feedback')