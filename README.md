# AI-Powered FinOps System with Integrated Chatbot

A comprehensive AWS FinOps platform that combines real-time cost analysis, AI-powered insights, and an integrated chatbot interface for natural language interactions. Built on AWS Bedrock, Lambda functions, and Model Context Protocol (MCP) for seamless integration with external tools.

## 🚀 Features

### Core Functionality
- **Real-time Cost Analysis**: Monitor AWS costs across all services
- **AI-Powered Chatbot**: Natural language interface for cost queries
- **Bedrock Integration**: Advanced AI analysis using AWS Bedrock agents
- **Lambda Functions**: Serverless compute for cost processing
- **MCP Support**: External AI tool integration via Model Context Protocol
- **Export Capabilities**: CSV, JSON, and PDF report generation

### Dashboard Components
- **Cost Overview**: Service-by-service cost breakdown with visualizations
- **Trend Analysis**: Historical cost patterns and growth trends
- **EC2 Optimization**: Instance utilization analysis and recommendations
- **AI Chat Interface**: Interactive chatbot for cost insights
- **Lambda Testing**: Direct Lambda function invocation for debugging

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│          Streamlit Dashboard (UI)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │   Cost   │ │   EC2    │ │   AI Chat    │   │
│  │ Overview │ │ Analysis │ │  Interface   │   │
│  └──────────┘ └──────────┘ └──────────────┘   │
└────────────────────┬────────────────────────────┘
                     │
      ┌──────────────┼──────────────────┐
      │              │                  │
┌─────▼─────┐ ┌─────▼──────┐ ┌────────▼────────┐
│  AWS Cost │ │   Bedrock  │ │   MCP Server    │
│  Explorer │ │   Agents   │ │  (WebSocket)    │
└───────────┘ └─────┬──────┘ └─────────────────┘
                    │
             ┌──────▼──────┐
             │   Lambda    │
             │  Functions  │
             └─────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- AWS Account with appropriate permissions
- AWS CLI configured
- Active AWS Cost Explorer

## 🏃 Quick Start

### Automated Deployment
```bash
# Run the quick start script
./quickstart.sh
```

This will:
1. Set up Python environment
2. Deploy AWS resources
3. Start MCP server
4. Run tests
5. Launch the dashboard

### Manual Deployment
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed step-by-step instructions.

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing procedures
- **[AI_FinOps_Complete_Documentation.ipynb](AI_FinOps_Complete_Documentation.ipynb)** - Technical deep dive

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_chatbot_integration.py
```

For detailed testing instructions, see [TESTING_GUIDE.md](TESTING_GUIDE.md).

## 💬 Using the Chatbot

The integrated chatbot supports natural language queries:

### Example Questions
- "What are my top 5 AWS services by cost?"
- "How can I reduce my EC2 costs?"
- "Show me cost trends for the last week"
- "Which services are growing fastest?"
- "Forecast my costs for next month"

### Enhanced Chat Mode
Enable in the sidebar for a focused chat experience with:
- Quick prompt buttons
- Full cost data context
- Export chat history

## 📁 Project Structure

```
aws-finops/
├── finops_dashboard_with_chatbot.py  # Main dashboard with chatbot
├── deploy_finops_system.py           # AWS deployment script
├── mcp_appitio_integration.py        # MCP server implementation
├── lambda_functions/                  # Lambda function code
│   ├── cost_analysis_lambda.py
│   ├── optimization_lambda.py
│   └── forecasting_lambda.py
├── test_chatbot_integration.py       # Comprehensive test suite
├── finops_config.json               # Configuration file
├── requirements.txt                 # Python dependencies
├── quickstart.sh                   # Quick start script
├── DEPLOYMENT_GUIDE.md             # Deployment documentation
├── TESTING_GUIDE.md               # Testing documentation
└── README.md                      # This file
```

## 🔧 Configuration

The system uses `finops_config.json` for configuration:

```json
{
    "agents": [
        {
            "agent_id": "YOUR_AGENT_ID",
            "alias_id": "YOUR_ALIAS_ID"
        }
    ],
    "bucket": "finops-artifacts-bucket",
    "lambda_functions": {
        "finops-cost-analysis": "arn:aws:lambda:..."
    }
}
```

## 🚨 Troubleshooting

### Common Issues

1. **"Access Denied" errors**
   - Check IAM permissions
   - Ensure Cost Explorer is enabled

2. **Chatbot not responding**
   - Verify Bedrock agent deployment
   - Check fallback responses are working

3. **No cost data**
   - Confirm AWS usage in selected period
   - Try extending the time range

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for detailed troubleshooting.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_chatbot_integration.py`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- AWS Bedrock team for AI capabilities
- Streamlit for the dashboard framework
- The FinOps community for best practices

---

For detailed setup and usage instructions, please refer to the documentation files listed above.
