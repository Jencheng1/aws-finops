# AWS FinOps AI Platform - User Guide

## 🚀 Quick Start

### Access the Platform
- **URL**: http://localhost:8503
- **Network URL**: http://10.0.1.56:8503

### Features Overview

## 📊 1. Cost Analytics Tab
- View real-time AWS costs with interactive charts
- Analyze spending by service
- Monitor daily cost trends
- **Try**: Change the "Historical Days" slider in the sidebar to adjust the time range

## 🤖 2. Budget Prediction Tab
- ML-powered cost forecasting
- **Click**: "Generate Budget Forecast" button to run predictions
- View 30-day forecast with confidence intervals
- See model accuracy metrics

## 🔍 3. Resource Optimization Tab
- Identify idle and underutilized resources
- **Click**: "Scan for Idle Resources" to find:
  - Stopped EC2 instances
  - Unattached EBS volumes
  - Unused Elastic IPs
- Calculate potential monthly savings

## 💰 4. Savings Plans Tab
- Get AWS Savings Plans recommendations
- **Click**: "Analyze Savings Opportunities"
- View recommended hourly commitment
- See estimated annual savings

## 💬 5. AI Assistant Tab
- Chat interface for cost-related questions
- **Type**: Your question in the text box
- **Click**: "Send" to get AI-powered insights
- Rate responses to improve accuracy

## 📈 6. Feedback Analytics Tab
- View feedback statistics
- Track system improvements
- Monitor user satisfaction

## 🎯 Quick Actions (Sidebar)

### 🚀 Run Full Analysis Button
**What it does**:
- Runs comprehensive analysis across all features
- Generates ML predictions
- Detects anomalies
- Calculates optimization opportunities
- Provides actionable recommendations

**How to use**:
1. Click "🚀 Run Full Analysis" in the sidebar
2. Wait for the spinner to complete (10-15 seconds)
3. View the summary that appears
4. Check individual tabs for detailed results

### 🔄 Refresh Data Button
- Updates all data from AWS APIs
- Clears any cached results
- Ensures you see the latest information

## 💡 Tips

1. **Feedback Widgets**: Throughout the interface, you'll see feedback options. Use them to help improve the system!

2. **Sliders**: Adjust the sidebar sliders to customize:
   - Historical days for analysis
   - Forecast period
   - Confidence levels

3. **Metrics**: Green/red indicators show positive/negative trends

4. **Error Handling**: If you see Lambda warnings, the system automatically falls back to local computation

## 🐛 Troubleshooting

### "Nothing happens when I click a button"
- The app may be processing. Look for:
  - Spinner indicators
  - Success/warning messages at the top
  - Updated data in the tabs

### "Lambda function not deployed" warnings
- This is normal if Lambda functions aren't deployed
- The app continues to work using local computation

### Page doesn't load
- Ensure Streamlit is running: `ps aux | grep streamlit`
- Restart if needed: `python3 -m streamlit run enhanced_dashboard_with_feedback.py --server.port 8503`

## 📞 Support
- Check logs: `tail -f ~/.streamlit/logs/*`
- Restart app: `pkill -f streamlit && python3 -m streamlit run enhanced_dashboard_with_feedback.py`