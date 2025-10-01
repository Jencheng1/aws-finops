#!/bin/bash
# Start the AI FinOps Platform

echo "========================================"
echo "Starting AI FinOps Platform"
echo "========================================"
echo ""
echo "Platform Features:"
echo "✅ Real AWS API Integration"
echo "✅ Human-in-the-Loop Feedback System"
echo "✅ AI Budget Prediction (ML Models)"
echo "✅ Resource Optimization Scanner"
echo "✅ Savings Plans Analyzer"
echo "✅ Cost Anomaly Detection"
echo "✅ DynamoDB Feedback Storage"
echo ""
echo "Starting Streamlit interface..."
echo "Access at: http://localhost:8501"
echo ""

# Start Streamlit with the enhanced dashboard
streamlit run enhanced_dashboard_with_feedback.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true