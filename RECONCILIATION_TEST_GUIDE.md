# AWS to Apptio MCP Reconciliation Testing Guide

## 🧪 How to Test the Reconciliation Feature

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.7+ installed
- Required dependencies (boto3, streamlit, pandas, plotly)

### Test 1: Direct Module Test
```bash
# Test the reverse engineering functionality directly
python3 test_apptio_simple.py
```

**Expected Results:**
- Should show 27+ AWS services mapped
- Total expenses around $106 (based on your actual usage)
- TBM Tower allocation with Infrastructure ~97%
- 100% mapping accuracy
- Resource validation showing running instances

### Test 2: Streamlit Dashboard Test
```bash
# Start the Streamlit dashboard
streamlit run apptio_mcp_reconciliation.py --port 8504
```

**What to Test:**
1. **Real Data Loading**: Verify it shows "Using actual AWS expenses" not "Demo Mode"
2. **Service Breakdown**: Check AWS services pie chart shows real services
3. **TBM Mapping**: Verify Apptio categories reflect actual AWS usage
4. **Reconciliation Table**: Review detailed mapping from AWS to TBM towers
5. **Download Reports**: Test CSV and summary report downloads

### Test 3: Integrated Dashboard Test
```bash
# Test within main FinOps dashboard
streamlit run finops_intelligent_dashboard.py --port 8501
```

**Steps:**
1. Navigate to any tab with MCP integration
2. Look for Apptio MCP references
3. Test optimization scan (should work now)
4. Test budget prediction (should show realistic numbers)

### Test 4: Optimization Scan Fix Verification
```bash
# Direct test of optimization functionality
python3 -c "
from multi_agent_processor import MultiAgentProcessor
processor = MultiAgentProcessor()
context = {'user_id': 'test', 'session_id': 'test'}
response, data = processor.process_optimizer_query('Find idle resources', context)
print('SUCCESS: Optimization scan working')
print(f'Found {data[\"summary\"][\"orphaned_snapshots_count\"]} orphaned snapshots')
print(f'Total savings: \${data[\"total_monthly_savings\"]:.2f}/month')
"
```

### Test 5: Budget Prediction Fix Verification
```bash
# Test budget prediction with real data
python3 -c "
from multi_agent_processor import MultiAgentProcessor
processor = MultiAgentProcessor()
context = {'user_id': 'test', 'session_id': 'test'}
response, data = processor.process_prediction_query('Get budget recommendations', context)
print('SUCCESS: Budget prediction working')
print(f'Predicted cost: \${data[\"total\"]:.2f}')
"
```

## 🔍 What to Look For

### ✅ Success Indicators
- **Real AWS Data**: Shows actual service costs, not demo values
- **Accurate Mapping**: AWS services correctly categorized into TBM towers
- **Working Scans**: Optimization scan finds real opportunities (54 snapshots, $110/month)
- **Realistic Budgets**: Budget recommendations based on actual spend (~$127 with 20% buffer)
- **No Errors**: All functions complete without "Unable to perform" messages

### ❌ Failure Indicators
- Shows "Demo Mode" or "Using demo values"
- Hardcoded values like $40,000 budgets
- "Unable to perform optimization scan" errors
- Zero values where real data should exist
- API permission errors

## 📊 Expected Test Results

### Real Environment Data (Your AWS Account)
- **Total Monthly Spend**: ~$106.03
- **Primary Services**: EC2 (97.6%), CloudTrail (2.4%), S3 (0.1%)
- **TBM Infrastructure**: ~$103 (dominant category)
- **Optimization Opportunities**: 54 orphaned snapshots, $110/month savings
- **Budget Recommendation**: ~$127/month (with 20% buffer)

### Reconciliation Accuracy
- **Mapping Success**: 100% of AWS services categorized
- **Data Source**: AWS Cost Explorer API (real-time)
- **Business Context**: Services assigned to appropriate business units
- **Variance**: <1% between AWS actual and TBM allocated

## 🛠️ Troubleshooting

### Common Issues
1. **Permission Errors**: Ensure AWS CLI has Cost Explorer permissions
2. **No Cost Data**: For new accounts, fallback to resource-based estimation
3. **Module Import Errors**: Run `pip install -r requirements.txt`
4. **Port Conflicts**: Use different ports for multiple Streamlit instances

### Quick Fixes
```bash
# If permissions issues
aws sts get-caller-identity

# If module issues  
pip install boto3 streamlit pandas plotly

# If port conflicts
streamlit run app.py --port 8505
```

## 📋 Test Checklist

### Manual Testing Checklist
- [ ] Module test shows real AWS data
- [ ] Streamlit app loads without errors
- [ ] AWS services displayed correctly
- [ ] TBM towers show proper allocation
- [ ] Reconciliation table has business context
- [ ] Download functionality works
- [ ] Optimization scan finds opportunities
- [ ] Budget predictions are realistic
- [ ] No hardcoded demo values visible

### Automated Testing
```bash
# Run all reconciliation tests
python3 test_apptio_simple.py
python3 -c "from apptio_mcp_reconciliation import create_mcp_reconciliation_demo; print('Module loads successfully')"
```

## 📈 Success Metrics

### Performance Benchmarks
- **Load Time**: <5 seconds for reconciliation data
- **Accuracy**: >95% mapping accuracy
- **Coverage**: 100% of AWS services categorized
- **Real-time**: Data reflects last 30 days actual usage

### Business Value Validation
- Shows actual IT spend per employee
- Demonstrates cost allocation to business units
- Provides actionable optimization opportunities
- Enables accurate budget planning

---

**Note**: This reconciliation feature reverse engineers your actual AWS expenses into Apptio TBM categories, providing real business value for Technology Business Management and FinOps practices.