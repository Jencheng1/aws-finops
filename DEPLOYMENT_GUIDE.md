# AI-Powered FinOps System Deployment Guide

This guide provides step-by-step instructions for deploying, starting, and testing the complete AI-powered FinOps system with integrated chatbot functionality.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Deployment Steps](#detailed-deployment-steps)
4. [Starting the Services](#starting-the-services)
5. [Testing the System](#testing-the-system)
6. [Troubleshooting](#troubleshooting)
7. [Architecture Overview](#architecture-overview)

---

## Prerequisites

### Required Software
- Python 3.8 or higher
- AWS CLI configured with appropriate credentials
- Git
- pip or pipenv for package management

### Required AWS Permissions
Your AWS account/role needs the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetCostForecast",
                "ce:GetReservationUtilization",
                "ec2:DescribeInstances",
                "ec2:DescribeRegions",
                "cloudwatch:GetMetricStatistics",
                "lambda:CreateFunction",
                "lambda:InvokeFunction",
                "lambda:GetFunction",
                "lambda:UpdateFunctionCode",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:GetRole",
                "s3:CreateBucket",
                "s3:PutObject",
                "s3:GetObject",
                "bedrock:CreateAgent",
                "bedrock:InvokeAgent",
                "bedrock-agent:*",
                "budgets:ViewBudget",
                "rds:DescribeDBInstances",
                "rds:ListTagsForResource",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## Quick Start

For experienced users who want to get up and running quickly:

```bash
# 1. Clone the repository (if applicable)
git clone <your-repo-url>
cd aws-finops

# 2. Install dependencies
pip install -r requirements.txt

# 3. Deploy all AWS resources
python deploy_finops_system.py

# 4. Start the MCP server (in a separate terminal)
python mcp_appitio_integration.py

# 5. Run the Streamlit dashboard
streamlit run finops_dashboard_with_chatbot.py

# 6. Run tests
python test_chatbot_integration.py
```

---

## Detailed Deployment Steps

### Step 1: Environment Setup

1. **Create a Python virtual environment:**
   ```bash
   python -m venv finops-env
   source finops-env/bin/activate  # On Windows: finops-env\Scripts\activate
   ```

2. **Install required packages:**
   ```bash
   pip install boto3 streamlit pandas plotly websocket-client pytest
   ```

### Step 2: AWS Configuration

1. **Configure AWS CLI:**
   ```bash
   aws configure
   ```
   Enter your:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., us-east-1)
   - Default output format (json)

2. **Verify AWS access:**
   ```bash
   aws sts get-caller-identity
   ```

### Step 3: Deploy AWS Resources

1. **Run the deployment script:**
   ```bash
   python deploy_finops_system.py
   ```
   
   This script will:
   - Create IAM roles for Lambda and Bedrock
   - Deploy Lambda functions for cost analysis
   - Create S3 bucket for artifacts
   - Set up Bedrock agents (if available in your region)
   
   Expected output:
   ```
   Creating IAM roles...
   ✓ Created Bedrock Agent Role
   ✓ Created Lambda Role
   
   Creating S3 bucket...
   ✓ Created bucket: finops-bedrock-637423485585-1759229243
   
   Deploying Lambda functions...
   ✓ Deployed: finops-cost-analysis
   
   Setting up Bedrock agents...
   ✓ Created agent: S8AZOE6JRP
   
   Deployment complete!
   ```

2. **Save the configuration:**
   The script automatically saves a `finops_config.json` file with:
   - Agent IDs
   - S3 bucket names
   - Lambda ARNs

### Step 4: Configure the Dashboard

1. **Update configuration if needed:**
   Edit `finops_config.json` to match your deployment:
   ```json
   {
       "agents": [
           {
               "agent_id": "YOUR_AGENT_ID",
               "alias_id": "YOUR_ALIAS_ID"
           }
       ],
       "bucket": "your-s3-bucket-name",
       "lambda_functions": {
           "finops-cost-analysis": "arn:aws:lambda:..."
       }
   }
   ```

2. **Set environment variables (optional):**
   ```bash
   export AWS_DEFAULT_REGION=us-east-1
   export FINOPS_AGENT_ID=YOUR_AGENT_ID
   export FINOPS_AGENT_ALIAS=YOUR_ALIAS_ID
   ```

---

## Starting the Services

### 1. Start the MCP Server (Optional - for enhanced AI capabilities)

In a separate terminal:
```bash
# Activate virtual environment
source finops-env/bin/activate

# Start MCP server
python mcp_appitio_integration.py
```

Expected output:
```
Starting MCP server on ws://0.0.0.0:8765
Server started. Waiting for connections...
```

### 2. Start the Streamlit Dashboard

In the main terminal:
```bash
# Make sure virtual environment is active
source finops-env/bin/activate

# Run the dashboard
streamlit run finops_dashboard_with_chatbot.py
```

Expected output:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.100:8501
```

### 3. Access the Dashboard

1. Open your browser to `http://localhost:8501`
2. You should see the AI-Powered FinOps Dashboard with:
   - Cost Overview tab
   - Trends analysis
   - EC2 Analysis
   - Optimizations
   - AI Chat tab
   - Test Lambda tab

---

## Testing the System

### 1. Run Automated Tests

```bash
# Run comprehensive test suite
python test_chatbot_integration.py
```

Expected output:
```
============================================================
FINOPS CHATBOT INTEGRATION TEST SUITE
============================================================
Test Started: 2024-12-17 10:30:00
AWS Region: us-east-1
============================================================

--- Testing Cost Data Fetching ---
✓ Fetched cost data successfully
  Total cost for 7 days: $25.32

--- Testing Chatbot Session Initialization ---
✓ Session state initialized correctly

--- Testing Bedrock Agent Query ---
✓ Bedrock agent responded successfully
  Response length: 256 characters

--- Testing Lambda Function Invocation ---
✓ Lambda invoked successfully
  Total cost returned: $25.32

--- Testing Fallback Response Generator ---
✓ Generated fallback response for 'highest' prompt
✓ Generated fallback response for 'save' prompt
✓ Generated fallback response for 'trend' prompt
✓ Generated fallback response for 'general' prompt

--- Testing Export Functionality ---
✓ CSV export successful
✓ JSON export successful
✓ PDF summary generation successful

--- Testing MCP Integration ---
✓ MCP server is running
  Available tools: 3
✓ MCP tool invocation successful

--- Testing Chat Conversation Flow ---
✓ Conversation flow test successful
  Conversation turns: 4

--- Testing Enhanced Chat Mode ---
✓ Quick prompts validated
  Available quick prompts: 5
✓ Chat mode toggle test successful

--- Testing Error Handling ---
✓ Lambda error handling successful
✓ Cost Explorer error handling successful

============================================================
TEST SUMMARY
============================================================
Total Tests: 10
Passed: 10 ✓
Failed: 0 ✗
Skipped: 0 ⚠️
Success Rate: 100.0%
============================================================
```

### 2. Manual Testing Checklist

#### Dashboard Testing:
- [ ] Navigate to each tab and verify data loads
- [ ] Check that cost data displays correctly
- [ ] Verify EC2 instance analysis shows utilization
- [ ] Test optimization recommendations
- [ ] Confirm Lambda testing functionality works

#### Chatbot Testing:
- [ ] Navigate to AI Chat tab
- [ ] Ask: "What are my top 5 AWS services by cost?"
- [ ] Ask: "How can I reduce my EC2 costs?"
- [ ] Ask: "Show me cost trends for the last week"
- [ ] Test enhanced chat mode toggle
- [ ] Try quick prompt buttons

#### Export Testing:
- [ ] Export data as CSV
- [ ] Export data as JSON
- [ ] Generate PDF summary
- [ ] Verify exported data accuracy

### 3. Test Individual Components

#### Test Lambda Function:
```bash
# Test Lambda directly
aws lambda invoke \
  --function-name finops-cost-analysis \
  --payload '{"apiPath": "/getCostBreakdown", "parameters": [{"name": "days", "value": "7"}]}' \
  output.json

cat output.json
```

#### Test Bedrock Agent:
```python
# Python script to test Bedrock agent
import boto3
import uuid

bedrock_runtime = boto3.client('bedrock-agent-runtime')

response = bedrock_runtime.invoke_agent(
    agentId='YOUR_AGENT_ID',
    agentAliasId='YOUR_ALIAS_ID',
    sessionId=str(uuid.uuid4()),
    inputText='What are my highest AWS costs?'
)

for event in response.get('completion', []):
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode('utf-8'))
```

#### Test MCP Server:
```python
# Python script to test MCP
import websocket
import json

ws = websocket.create_connection("ws://localhost:8765")

# List tools
ws.send(json.dumps({"type": "list_tools"}))
print(ws.recv())

# Call a tool
ws.send(json.dumps({
    "type": "tool_call",
    "tool": "get_cost_analysis",
    "parameters": {"days": 7}
}))
print(ws.recv())

ws.close()
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Access Denied" errors
- **Solution:** Check IAM permissions
- Run: `aws sts get-caller-identity` to verify credentials
- Ensure your role has all required permissions listed above

#### 2. Lambda function not found
- **Solution:** Check deployment status
- Run: `aws lambda get-function --function-name finops-cost-analysis`
- Redeploy if necessary: `python deploy_finops_system.py`

#### 3. Bedrock agent not responding
- **Solution:** 
  - Verify agent is deployed: Check `finops_config.json`
  - Ensure Bedrock is available in your region
  - The chatbot will fall back to local responses if Bedrock is unavailable

#### 4. Cost data not showing
- **Solution:**
  - Verify Cost Explorer is enabled in AWS
  - Check you have cost data for the selected period
  - Try a longer time period (30 days)

#### 5. MCP server connection failed
- **Solution:**
  - Ensure MCP server is running
  - Check firewall/security group settings
  - The system works without MCP (optional component)

### Debug Mode

Enable debug logging in the dashboard:
```python
# Add to finops_dashboard_with_chatbot.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System Status

Use the sidebar in the dashboard to check:
- Lambda function status
- Bedrock agent configuration
- Current AWS credentials
- Cost data availability

---

## Architecture Overview

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

### Component Communication Flow:
1. User interacts with Streamlit UI
2. Dashboard queries AWS APIs directly for cost data
3. Chatbot queries can go to:
   - Bedrock agents for AI analysis
   - Lambda functions for specific computations
   - MCP server for external tool integration
   - Fallback to local processing if services unavailable

---

## Next Steps

1. **Customize the dashboard** for your specific needs
2. **Add more Lambda functions** for specialized analysis
3. **Train Bedrock agents** with your organization's data
4. **Set up automated alerts** using the system
5. **Integrate with your existing tools** via MCP

For more information, see:
- `AI_FinOps_Complete_Documentation.ipynb` - Detailed technical documentation
- `README.md` - Project overview
- `finops_dashboard_with_chatbot.py` - Source code with comments

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review test output for specific errors
3. Check AWS CloudWatch logs for Lambda errors
4. Verify all services are running in the correct region

Remember: The system is designed to gracefully degrade. If Bedrock or MCP are unavailable, the chatbot will still provide useful responses using cached cost data.