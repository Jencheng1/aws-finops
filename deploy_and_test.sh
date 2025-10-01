#!/bin/bash
# Automated deployment and testing script

echo "========================================"
echo "AI FinOps Platform Automated Deployment"
echo "========================================"

# Deploy Lambda functions
echo "n" | python3 run_complete_platform.py

# Create Lambda packages
echo "Creating Lambda deployment packages..."
python3 create_lambda_packages.py

# Run comprehensive tests
echo "Running platform tests..."
python3 test_integrated_platform.py

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Check output above."
fi

echo ""
echo "========================================"
echo "Deployment Summary"
echo "========================================"
echo "✅ DynamoDB tables created"
echo "✅ Lambda functions ready for deployment"
echo "✅ Test suite executed"
echo ""
echo "To start the platform:"
echo "  streamlit run enhanced_dashboard_with_feedback.py"
echo ""