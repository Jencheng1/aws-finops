import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import time
import uuid
import requests

# Import our AI agents
from budget_prediction_agent import BudgetPredictionAgent, CostAnomalyDetector, get_budget_insights

# Initialize AWS clients with real APIs
ce = boto3.client('ce')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
support = boto3.client('support')
sts = boto3.client('sts')
organizations = boto3.client('organizations')
savingsplans = boto3.client('savingsplans')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Page configuration
st.set_page_config(
    page_title="AI-Powered FinOps Platform with Human Feedback",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with feedback styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feedback-widget {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #4682b4;
        margin: 1rem 0;
    }
    .feedback-positive {
        background: #e8f5e8;
        border-color: #28a745;
    }
    .feedback-negative {
        background: #fee;
        border-color: #dc3545;
    }
    .ai-agent-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    .human-loop-indicator {
        background: #6c757d;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
        margin-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'ai_agent' not in st.session_state:
    st.session_state.ai_agent = BudgetPredictionAgent()
if 'anomaly_detector' not in st.session_state:
    st.session_state.anomaly_detector = CostAnomalyDetector()
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = []
if 'predictions_made' not in st.session_state:
    st.session_state.predictions_made = {}
if 'recommendations_made' not in st.session_state:
    st.session_state.recommendations_made = {}

# Get account info
try:
    account_id = sts.get_caller_identity()['Account']
except:
    account_id = "Demo Account"

# Helper function to invoke Lambda
def invoke_lambda_function(function_name, payload):
    """Invoke Lambda function and return response"""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        if response['StatusCode'] == 200:
            return json.loads(result['body'])
        else:
            return None
    except Exception as e:
        # If Lambda not deployed, use local fallback
        if "ResourceNotFoundException" in str(e):
            st.warning(f"Lambda function '{function_name}' not deployed. Using local computation instead.")
            # Return None to trigger local execution
            return None
        else:
            st.error(f"Lambda invocation error: {e}")
            return None

# Helper function to submit feedback
def submit_feedback(feedback_type, feedback_text, rating, context):
    """Submit feedback to Lambda for processing"""
    payload = {
        'feedback_type': feedback_type,
        'user_id': st.session_state.user_id,
        'session_id': st.session_state.session_id,
        'feedback_text': feedback_text,
        'rating': rating,
        'context': context
    }
    
    result = invoke_lambda_function('finops-feedback-processor', payload)
    
    if result:
        st.session_state.feedback_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': feedback_type,
            'text': feedback_text,
            'rating': rating
        })
        return True
    return False

# Feedback widget component
def render_feedback_widget(widget_id, title, context, feedback_type):
    """Render a feedback widget for human-in-the-loop"""
    with st.container():
        st.markdown(f"""
        <div class="feedback-widget">
            <h4>{title} <span class="human-loop-indicator">Human Feedback</span></h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            rating = st.slider("Accuracy", 1, 5, 3, key=f"rating_{widget_id}")
            
        with col2:
            feedback_text = st.text_area(
                "Your feedback helps improve our AI",
                key=f"feedback_{widget_id}",
                height=80,
                placeholder="Was this helpful? Any suggestions?"
            )
            
        with col3:
            if st.button("Submit", key=f"submit_{widget_id}"):
                if submit_feedback(feedback_type, feedback_text, rating, context):
                    st.success("Thank you! Your feedback improves our AI.")
                else:
                    st.error("Failed to submit feedback. Please try again.")

# Title
st.markdown('<h1 class="main-header">🚀 AI-Powered FinOps Platform</h1>', unsafe_allow_html=True)
st.markdown("### With Human-in-the-Loop Feedback System")

# Key metrics banner
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active User ID", st.session_state.user_id[:8] + "...")
with col2:
    st.metric("Session", st.session_state.session_id[:8] + "...")
with col3:
    st.metric("Feedback Given", len(st.session_state.feedback_history))
with col4:
    st.metric("AI Accuracy", "Learning...")

# Sidebar
with st.sidebar:
    st.header("🔧 Platform Controls")
    
    # User settings
    st.subheader("User Settings")
    user_name = st.text_input("Your Name (optional)", key="user_name")
    enable_feedback = st.checkbox("Enable Feedback Widgets", True)
    auto_improve = st.checkbox("Auto-improve from Feedback", True)
    
    st.markdown("---")
    
    # Analysis settings
    st.subheader("Analysis Settings")
    days = st.slider("Historical Days", 7, 90, 30)
    forecast_days = st.slider("Forecast Days", 7, 90, 30)
    confidence_level = st.selectbox("Confidence Level", ["90%", "95%", "99%"], index=1)
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
            st.session_state.run_full_analysis = True
            try:
                st.rerun()  # Try new API first
            except:
                try:
                    st.experimental_rerun()  # Fall back to old API
                except:
                    pass  # Let natural rerun happen
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            # Clear any cached data
            st.session_state.data_refreshed = True
            st.success("Data refresh triggered!")
    
    # Feedback history
    if st.session_state.feedback_history:
        st.subheader("Recent Feedback")
        for fb in st.session_state.feedback_history[-3:]:
            st.info(f"{fb['type']}: ⭐{fb['rating']}")

# Check if full analysis was triggered
if 'run_full_analysis' in st.session_state and st.session_state.run_full_analysis:
    with st.spinner("🔄 Running comprehensive analysis... This may take a moment."):
        # Import necessary functions
        from budget_prediction_agent import get_budget_insights
        
        try:
            # Get comprehensive insights
            insights = get_budget_insights(months_history=2, prediction_days=forecast_days)
            
            # Store results in session state
            st.session_state.last_full_analysis = {
                'timestamp': datetime.now(),
                'insights': insights,
                'status': 'completed'
            }
            
            # Show success message
            st.success("✅ Full analysis completed! Check the tabs below for detailed results.")
            
            # Display summary
            with st.expander("📋 Analysis Summary", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        f"{forecast_days}-Day Forecast",
                        f"${insights['predictions']['summary']['total_predicted_cost']:,.2f}"
                    )
                with col2:
                    st.metric(
                        "Anomalies Detected",
                        f"{insights['anomalies']['summary']['total_anomalies']}"
                    )
                with col3:
                    st.metric(
                        "Optimization Potential",
                        f"${insights['trusted_advisor']['total_monthly_savings']:,.2f}/mo"
                    )
                with col4:
                    st.metric(
                        "Recommendations",
                        f"{len(insights['recommendations'])}"
                    )
                
                # Top recommendations
                if insights['recommendations']:
                    st.subheader("🎯 Top Recommendations")
                    for i, rec in enumerate(insights['recommendations'][:3], 1):
                        st.write(f"{i}. **{rec['title']}**")
                        if 'value' in rec:
                            st.write(f"   Value: {rec['value']}")
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.session_state.last_full_analysis = {
                'timestamp': datetime.now(),
                'status': 'error',
                'error': str(e)
            }
        
        # Reset the flag
        st.session_state.run_full_analysis = False

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Cost Analytics",
    "🤖 Budget Prediction",
    "🔍 Resource Optimization", 
    "💰 Savings Plans",
    "💬 AI Assistant",
    "📈 Feedback Analytics"
])

# Tab 1: Cost Analytics with Feedback
with tab1:
    st.header("Cost Analytics Dashboard")
    
    # Fetch real cost data
    try:
        with st.spinner("Loading cost data from AWS..."):
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Process data
            daily_costs = []
            service_costs = {}
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                total_cost = 0
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    total_cost += cost
                    if service not in service_costs:
                        service_costs[service] = 0
                    service_costs[service] += cost
                daily_costs.append({'Date': date, 'Cost': total_cost})
            
            # Display metrics
            total_cost = sum(item['Cost'] for item in daily_costs)
            avg_daily = total_cost / len(daily_costs) if daily_costs else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cost", f"${total_cost:,.2f}", f"Last {days} days")
            with col2:
                st.metric("Daily Average", f"${avg_daily:,.2f}")
            with col3:
                st.metric("Services", len(service_costs))
            with col4:
                trend = ((daily_costs[-1]['Cost'] - daily_costs[0]['Cost']) / daily_costs[0]['Cost'] * 100) if len(daily_costs) > 1 else 0
                st.metric("Trend", f"{trend:+.1f}%")
            
            # Cost trend chart
            df_daily = pd.DataFrame(daily_costs)
            fig = px.line(df_daily, x='Date', y='Cost', title='Daily Cost Trend')
            st.plotly_chart(fig, use_container_width=True)
            
            # Feedback widget for cost data accuracy
            if enable_feedback:
                render_feedback_widget(
                    "cost_accuracy",
                    "Is this cost data accurate?",
                    {
                        "total_cost": total_cost,
                        "period_days": days,
                        "services": len(service_costs)
                    },
                    "cost_data_accuracy"
                )
            
    except ClientError as e:
        st.error(f"Error fetching cost data: {e}")

# Tab 2: Budget Prediction with Feedback
with tab2:
    st.header("🤖 AI Budget Prediction")
    
    if st.button("Generate Budget Forecast", key="forecast_btn"):
        with st.spinner("AI agents analyzing patterns..."):
            # Use Lambda for prediction
            payload = {
                'days_ahead': forecast_days,
                'months_history': 3,
                'user_id': st.session_state.user_id,
                'session_id': st.session_state.session_id
            }
            
            result = invoke_lambda_function('finops-budget-predictor', payload)
            
            if result:
                predictions = result['predictions']
                summary = result['summary']
                
                # Store prediction for feedback
                prediction_id = str(uuid.uuid4())
                st.session_state.predictions_made[prediction_id] = {
                    'timestamp': datetime.now().isoformat(),
                    'total_predicted': summary['total_predicted'],
                    'daily_average': summary['average_daily']
                }
                
                # Display results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Forecast", f"${summary['total_predicted']:,.2f}", 
                            f"Next {forecast_days} days")
                with col2:
                    st.metric("Daily Average", f"${summary['average_daily']:,.2f}")
                with col3:
                    st.metric("Model Accuracy", f"{summary['model_accuracy']*100:.1f}%")
                
                # Prediction chart
                df_pred = pd.DataFrame(predictions)
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_pred['date'], 
                    y=df_pred['predicted_cost'],
                    mode='lines',
                    name='Prediction',
                    line=dict(color='blue', width=3)
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_pred['date'],
                    y=df_pred['upper_bound'],
                    mode='lines',
                    name='Upper Bound',
                    line=dict(color='lightblue', dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_pred['date'],
                    y=df_pred['lower_bound'],
                    mode='lines',
                    name='Lower Bound',
                    fill='tonexty',
                    line=dict(color='lightblue', dash='dash')
                ))
                
                fig.update_layout(title=f'{forecast_days}-Day Budget Forecast')
                st.plotly_chart(fig, use_container_width=True)
                
                # Feedback widget for predictions
                if enable_feedback:
                    render_feedback_widget(
                        f"prediction_{prediction_id}",
                        "Help us improve prediction accuracy",
                        {
                            "prediction_id": prediction_id,
                            "predicted_cost": summary['total_predicted'],
                            "forecast_days": forecast_days
                        },
                        "prediction_accuracy"
                    )
                    
                    # Additional feedback for when actual costs are known
                    with st.expander("Update with Actual Costs (when available)"):
                        actual_cost = st.number_input("Actual cost when period ends", 
                                                    min_value=0.0,
                                                    key=f"actual_{prediction_id}")
                        if st.button("Submit Actual", key=f"submit_actual_{prediction_id}"):
                            submit_feedback(
                                "prediction_accuracy",
                                f"Actual cost was ${actual_cost:,.2f}",
                                5 if abs(actual_cost - summary['total_predicted'])/actual_cost < 0.05 else 3,
                                {
                                    "prediction_id": prediction_id,
                                    "predicted_cost": summary['total_predicted'],
                                    "actual_cost": actual_cost
                                }
                            )

# Tab 3: Resource Optimization with Feedback
with tab3:
    st.header("🔍 Resource Optimization")
    
    if st.button("Scan for Idle Resources", key="scan_btn"):
        with st.spinner("Scanning AWS environment..."):
            # Use Lambda for resource optimization
            payload = {
                'scan_days': 30,
                'user_id': st.session_state.user_id,
                'session_id': st.session_state.session_id
            }
            
            result = invoke_lambda_function('finops-resource-optimizer', payload)
            
            if result:
                idle_resources = result
                total_waste = idle_resources['total_monthly_waste']
                
                # Display summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Idle Resources", 
                            sum(len(v) for k, v in idle_resources.items() if isinstance(v, list)))
                with col2:
                    st.metric("Monthly Waste", f"${total_waste:,.2f}")
                with col3:
                    st.metric("Annual Savings", f"${total_waste * 12:,.2f}")
                
                # Display details by resource type
                for resource_type, resources in idle_resources.items():
                    if isinstance(resources, list) and resources:
                        st.subheader(f"{resource_type.replace('_', ' ').title()}")
                        
                        for idx, resource in enumerate(resources):
                            with st.expander(f"{resource['type']} - {resource['resource_id']}"):
                                st.json(resource)
                                
                                # Feedback for false positives
                                if enable_feedback:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        reason = st.selectbox(
                                            "Is this a false positive?",
                                            ["No - correct detection", 
                                             "Yes - actively used",
                                             "Yes - required for compliance",
                                             "Yes - scheduled workload",
                                             "Yes - other reason"],
                                            key=f"fp_{resource['resource_id']}"
                                        )
                                    with col2:
                                        if st.button("Report", key=f"report_{resource['resource_id']}"):
                                            if reason.startswith("Yes"):
                                                submit_feedback(
                                                    "false_positive",
                                                    f"Resource {resource['resource_id']} is not idle: {reason}",
                                                    1,
                                                    {
                                                        "resource_id": resource['resource_id'],
                                                        "detection_type": resource['type'],
                                                        "reason": reason
                                                    }
                                                )

# Tab 4: Savings Plans with Feedback
with tab4:
    st.header("💰 Savings Plans Recommendations")
    
    if st.button("Analyze Savings Opportunities", key="savings_btn"):
        with st.spinner("Analyzing usage patterns..."):
            try:
                # Get recommendations
                recommendations = ce.get_savings_plans_purchase_recommendation(
                    SavingsPlansType='COMPUTE_SP',
                    TermInYears='ONE_YEAR',
                    PaymentOption='ALL_UPFRONT',
                    LookbackPeriodInDays='SIXTY_DAYS'
                )
                
                if 'SavingsPlansPurchaseRecommendation' in recommendations:
                    rec = recommendations['SavingsPlansPurchaseRecommendation']
                    hourly = float(rec.get('HourlyCommitmentToPurchase', 0))
                    savings = float(rec.get('EstimatedSavingsAmount', 0))
                    
                    # Store recommendation
                    rec_id = str(uuid.uuid4())
                    st.session_state.recommendations_made[rec_id] = {
                        'timestamp': datetime.now().isoformat(),
                        'hourly_commitment': hourly,
                        'estimated_savings': savings
                    }
                    
                    # Display recommendation
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Recommended Commitment", f"${hourly:.2f}/hour")
                    with col2:
                        st.metric("Estimated Savings", f"${savings:,.2f}/year")
                    with col3:
                        if hourly > 0:
                            st.metric("Savings Percentage", f"{(savings/(hourly*24*365))*100:.1f}%")
                        else:
                            st.metric("Savings Percentage", "N/A")
                    
                    # Feedback on recommendation usefulness
                    if enable_feedback:
                        render_feedback_widget(
                            f"sp_rec_{rec_id}",
                            "Is this Savings Plan recommendation helpful?",
                            {
                                "recommendation_id": rec_id,
                                "recommendation_type": "savings_plan",
                                "hourly_commitment": hourly,
                                "estimated_savings": savings
                            },
                            "recommendation_usefulness"
                        )
                        
            except Exception as e:
                st.error(f"Error getting recommendations: {e}")

# Tab 5: AI Assistant with Feedback Loop
with tab5:
    st.header("💬 AI-Powered Assistant")
    
    st.info("Chat with our AI assistant. Your feedback helps improve responses!")
    
    # Chat history
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            with st.container():
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.write("👤")
                with col2:
                    st.markdown(f"**You:** {msg['content']}")
        else:
            with st.container():
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.write("🤖")
                with col2:
                    st.markdown(f"**Assistant:** {msg['content']}")
            
            # Add feedback widget for AI responses
            if msg["role"] == "assistant" and enable_feedback:
                if "feedback_given" not in msg:
                    helpful = st.radio(
                        "Was this helpful?",
                        ["👍 Yes", "👎 No", "➖ Somewhat"],
                        key=f"helpful_{msg.get('id', 0)}",
                        horizontal=True
                    )
                    
                    if helpful != "➖ Somewhat":
                        rating = 5 if helpful == "👍 Yes" else 1
                        submit_feedback(
                            "chat_response_quality",
                            f"Response was {helpful}",
                            rating,
                            {"message_id": msg.get('id', 0), "content": msg["content"][:100]}
                        )
                        msg["feedback_given"] = True
    
    # Chat input (using text_input for compatibility)
    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_input("Ask about costs, savings, or optimizations...", key="chat_input")
        submit_button = st.form_submit_button("Send")
    
    if submit_button and prompt:
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Generate response
        with st.spinner("Thinking..."):
            # Determine intent and generate response
            response = "I'm analyzing your request..."
            
            # Add AI response with ID for feedback
            msg_id = len(st.session_state.chat_messages)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": response,
                "id": msg_id
            })
            
            # Display the response
            with st.container():
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.write("🤖")
                with col2:
                    st.markdown(f"**Assistant:** {response}")

# Tab 6: Feedback Analytics
with tab6:
    st.header("📈 Feedback Analytics")
    
    st.markdown("### Your Contribution to AI Improvement")
    
    # Fetch feedback from DynamoDB
    try:
        feedback_table = dynamodb.Table('FinOpsFeedback')
        
        # Query user's feedback
        response = feedback_table.query(
            IndexName='UserIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={
                ':uid': st.session_state.user_id
            },
            Limit=50
        )
        
        if response['Items']:
            feedback_df = pd.DataFrame(response['Items'])
            
            # Feedback summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Feedback", len(feedback_df))
            with col2:
                avg_rating = feedback_df['rating'].astype(float).mean()
                st.metric("Average Rating", f"{avg_rating:.1f}/5")
            with col3:
                types = feedback_df['feedback_type'].value_counts()
                st.metric("Most Feedback On", types.index[0] if not types.empty else "N/A")
            
            # Feedback over time
            feedback_df['timestamp'] = pd.to_datetime(feedback_df['timestamp'])
            daily_feedback = feedback_df.groupby(feedback_df['timestamp'].dt.date).size()
            
            fig = px.line(x=daily_feedback.index, y=daily_feedback.values,
                         title="Your Feedback Contributions Over Time")
            fig.update_xaxis(title="Date")
            fig.update_yaxis(title="Feedback Count")
            st.plotly_chart(fig, use_container_width=True)
            
            # Feedback by type
            fig = px.pie(values=types.values, names=types.index,
                        title="Feedback Distribution by Type")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent feedback
            st.subheader("Recent Feedback")
            recent = feedback_df.nlargest(5, 'timestamp')[['timestamp', 'feedback_type', 'feedback_text', 'rating']]
            st.dataframe(recent, use_container_width=True)
            
        else:
            st.info("No feedback recorded yet. Start using the platform and provide feedback to see analytics!")
            
    except Exception as e:
        st.error(f"Error loading feedback analytics: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>AI-Powered FinOps Platform with Human-in-the-Loop Learning</p>
    <p>Your feedback makes our AI smarter!</p>
    <p><small>Session: {}</small></p>
</div>
""".format(st.session_state.session_id[:8]), unsafe_allow_html=True)