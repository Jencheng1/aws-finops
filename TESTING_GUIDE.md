# FinOps System Testing Guide

This guide provides comprehensive instructions for testing the AI-powered FinOps system with integrated chatbot functionality.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Automated Testing](#automated-testing)
3. [Manual Testing](#manual-testing)
4. [Performance Testing](#performance-testing)
5. [Integration Testing](#integration-testing)
6. [Troubleshooting Test Failures](#troubleshooting-test-failures)

---

## Testing Overview

The FinOps system includes several types of tests:

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Verify system responsiveness
- **Manual Tests**: Validate user experience

### Test Coverage Areas

1. **AWS API Integration**
   - Cost Explorer data retrieval
   - EC2 instance analysis
   - CloudWatch metrics

2. **AI Components**
   - Bedrock agent responses
   - Fallback response generation
   - Context management

3. **Lambda Functions**
   - Cost analysis functions
   - Optimization recommendations
   - Forecasting calculations

4. **Chatbot Functionality**
   - Natural language understanding
   - Multi-turn conversations
   - Export capabilities

5. **MCP Integration**
   - WebSocket connectivity
   - Tool invocation
   - Response handling

---

## Automated Testing

### Running the Complete Test Suite

```bash
# Activate virtual environment
source finops-env/bin/activate

# Run all tests
python test_chatbot_integration.py
```

### Running Specific Test Categories

```python
# Run only cost data tests
pytest test_chatbot_integration.py::TestFinOpsChatbot::test_cost_data_fetching -v

# Run only chatbot tests
pytest test_chatbot_integration.py -k "chatbot" -v

# Run only integration tests
pytest test_chatbot_integration.py -k "integration" -v
```

### Test Output Interpretation

#### Successful Test Run:
```
✓ Fetched cost data successfully
  Total cost for 7 days: $25.32
✓ Session state initialized correctly
✓ Bedrock agent responded successfully
  Response length: 256 characters
```

#### Failed Test:
```
✗ test_bedrock_agent_query failed: ResourceNotFoundException
```

#### Skipped Test:
```
⚠️ MCP integration test skipped: Connection refused
```

---

## Manual Testing

### 1. Dashboard Functionality Testing

#### Cost Overview Tab
1. Navigate to http://localhost:8501
2. Verify the Cost Overview tab displays:
   - [ ] Total cost metric
   - [ ] Daily average metric
   - [ ] Number of services
   - [ ] Cost trend percentage
   - [ ] Service breakdown chart
   - [ ] Daily cost trend line chart

3. Test interactions:
   - [ ] Hover over charts for tooltips
   - [ ] Click legend items to filter
   - [ ] Verify data updates with refresh

#### Trends Tab
1. Switch to Trends tab
2. Test controls:
   - [ ] Change trend period (7, 14, 30, 60, 90 days)
   - [ ] Change granularity (Daily, Weekly, Monthly)
   - [ ] Click "Analyze Trends" button

3. Verify output:
   - [ ] Trend chart displays
   - [ ] Top 5 services shown
   - [ ] Trend summary table appears

#### EC2 Analysis Tab
1. Navigate to EC2 Analysis
2. Verify displays:
   - [ ] Total running instances count
   - [ ] Low utilization count with warning
   - [ ] Medium utilization count
   - [ ] Instance utilization table
   - [ ] CPU utilization histogram
   - [ ] Instance type distribution pie chart

3. Check recommendations:
   - [ ] Low utilization warnings appear
   - [ ] Potential savings calculated
   - [ ] Specific instance IDs listed

### 2. Chatbot Testing

#### Basic Conversation Flow
1. Navigate to AI Chat tab
2. Test these prompts sequentially:

```
User: What are my top 5 AWS services by cost?
Expected: List of top 5 services with costs

User: Tell me more about EC2 costs
Expected: Detailed EC2 cost breakdown

User: How can I reduce these costs?
Expected: Specific optimization recommendations
```

#### Advanced Queries
Test complex queries:

1. **Cost Analysis**
   ```
   "What percentage of my total costs is from EC2?"
   "Show me cost trends for S3 over the last week"
   "Which services have grown the most?"
   ```

2. **Optimization**
   ```
   "Find all idle resources"
   "What are quick wins for cost reduction?"
   "Should I use Reserved Instances?"
   ```

3. **Forecasting**
   ```
   "What will my costs be next month?"
   "Project my annual AWS spend"
   "Alert me if costs exceed $1000/month"
   ```

#### Enhanced Chat Mode
1. Enable Enhanced Chat Mode in sidebar
2. Verify:
   - [ ] Chat interface becomes primary focus
   - [ ] Quick prompts appear in sidebar
   - [ ] Context indicator shows "enabled"
   - [ ] Chat history persists

3. Test quick prompts:
   - [ ] Click each quick prompt button
   - [ ] Verify prompt appears in chat
   - [ ] Confirm appropriate response

### 3. Export Functionality Testing

#### CSV Export
1. Click Export Data → CSV
2. Verify file contains:
   - [ ] Headers: Metric, Value
   - [ ] Total Cost row
   - [ ] Daily Average row
   - [ ] Service Count row
   - [ ] Proper formatting

#### JSON Export
1. Click Export Data → JSON
2. Verify file contains:
   - [ ] Valid JSON structure
   - [ ] All cost data fields
   - [ ] Chat history (if any)
   - [ ] Timestamp

#### PDF Summary
1. Click Export Data → PDF Summary
2. Verify preview shows:
   - [ ] Executive summary
   - [ ] Top services list
   - [ ] Recommendations
   - [ ] Proper formatting

### 4. Lambda Function Testing

1. Navigate to Test Lambda tab
2. Test each function:

#### getCostBreakdown
- [ ] Select function
- [ ] Set days to 7
- [ ] Click Test
- [ ] Verify response shows cost data
- [ ] Check visualization appears

#### analyzeTrends
- [ ] Select function
- [ ] Click Test
- [ ] Verify trend analysis returned

#### getOptimizations
- [ ] Select function
- [ ] Click Test
- [ ] Verify recommendations returned

---

## Performance Testing

### Response Time Benchmarks

Expected response times:
- Cost data fetch: < 2 seconds
- Chatbot response: < 3 seconds
- Lambda invocation: < 1 second
- Export generation: < 1 second

### Load Testing

```python
# Simple load test script
import time
import concurrent.futures
import requests

def test_endpoint(url):
    start = time.time()
    response = requests.get(url)
    return time.time() - start

# Test concurrent users
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_endpoint, "http://localhost:8501") 
               for _ in range(10)]
    
    response_times = [f.result() for f in futures]
    avg_response = sum(response_times) / len(response_times)
    
    print(f"Average response time: {avg_response:.2f}s")
```

---

## Integration Testing

### 1. End-to-End Workflow Test

Test complete user journey:

1. **Start System**
   ```bash
   ./quickstart.sh
   ```

2. **Cost Analysis Flow**
   - Open dashboard
   - View cost overview
   - Navigate to trends
   - Ask chatbot about specific service
   - Export report

3. **Optimization Flow**
   - View EC2 analysis
   - Ask chatbot for recommendations
   - Test Lambda optimization function
   - Export recommendations

### 2. Component Integration Tests

#### AWS Services Integration
```python
# Test script for AWS integration
import boto3

def test_aws_integration():
    # Test Cost Explorer
    ce = boto3.client('ce')
    response = ce.get_cost_and_usage(
        TimePeriod={'Start': '2024-12-01', 'End': '2024-12-07'},
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )
    assert 'ResultsByTime' in response
    
    # Test EC2
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances()
    assert 'Reservations' in response
    
    print("✓ AWS integration test passed")

test_aws_integration()
```

#### Bedrock Agent Integration
```python
# Test Bedrock agent
def test_bedrock_integration():
    import json
    with open('finops_config.json') as f:
        config = json.load(f)
    
    if 'agents' in config:
        agent_id = config['agents'][0]['agent_id']
        # Test agent exists
        bedrock = boto3.client('bedrock-agent')
        response = bedrock.get_agent(agentId=agent_id)
        assert response['agent']['agentStatus'] == 'PREPARED'
        print("✓ Bedrock agent test passed")

test_bedrock_integration()
```

---

## Troubleshooting Test Failures

### Common Test Failures and Solutions

#### 1. AWS Credentials Error
```
Error: Unable to locate credentials
```
**Solution:**
- Run `aws configure`
- Check ~/.aws/credentials file
- Ensure IAM role has correct permissions

#### 2. Lambda Not Found
```
Error: Function not found: finops-cost-analysis
```
**Solution:**
- Run deployment script: `python deploy_finops_system.py`
- Check AWS region matches configuration
- Verify Lambda was created successfully

#### 3. Bedrock Agent Timeout
```
Error: Bedrock agent timeout after 30s
```
**Solution:**
- Check agent is in PREPARED state
- Verify agent has correct permissions
- Test will fall back to local responses

#### 4. MCP Connection Refused
```
Error: [Errno 111] Connection refused
```
**Solution:**
- Start MCP server: `python mcp_appitio_integration.py`
- Check port 8765 is not blocked
- MCP is optional - tests will skip if unavailable

#### 5. Cost Data Not Available
```
Error: No cost data for specified period
```
**Solution:**
- Ensure Cost Explorer is enabled
- Try a longer time period (30 days)
- Check you have AWS usage in the period

### Debug Mode

Enable detailed logging for troubleshooting:

```python
# Add to test script
import logging
logging.basicConfig(level=logging.DEBUG)

# Run tests with pytest verbose mode
pytest test_chatbot_integration.py -vv -s
```

### Test Environment Variables

Set these for testing:
```bash
export AWS_DEFAULT_REGION=us-east-1
export FINOPS_TEST_MODE=true
export FINOPS_LOG_LEVEL=DEBUG
```

---

## Continuous Testing

### Setting Up Automated Testing

1. **Create test script** (`run_tests.sh`):
   ```bash
   #!/bin/bash
   source finops-env/bin/activate
   python test_chatbot_integration.py
   
   if [ $? -eq 0 ]; then
       echo "All tests passed!"
   else
       echo "Tests failed!"
       exit 1
   fi
   ```

2. **Schedule regular tests** (crontab):
   ```
   0 */4 * * * /path/to/run_tests.sh >> /var/log/finops_tests.log 2>&1
   ```

### Test Reports

Generate detailed test reports:

```bash
# Install pytest-html
pip install pytest-html

# Run tests with HTML report
pytest test_chatbot_integration.py --html=test_report.html --self-contained-html
```

---

## Summary

Regular testing ensures:
- All AWS integrations work correctly
- AI components respond appropriately
- Cost data is accurate and current
- User experience is smooth
- System performs within expectations

Run tests:
- After any code changes
- Before deploying updates
- When AWS services change
- Periodically (daily/weekly)

For questions or issues, check:
- CloudWatch logs for Lambda errors
- Streamlit console for UI errors
- MCP server logs for integration issues
- AWS service health dashboard