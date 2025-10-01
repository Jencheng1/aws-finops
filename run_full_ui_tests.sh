#!/bin/bash
# Run full UI tests with Selenium

echo "========================================"
echo "Running Full UI Tests with Selenium"
echo "========================================"

# 1. Kill any existing Streamlit processes
echo "Cleaning up existing processes..."
pkill -f streamlit || true
sleep 2

# 2. Start Streamlit in background
echo "Starting Streamlit application..."
nohup streamlit run enhanced_dashboard_with_feedback.py \
    --server.headless true \
    --server.port 8501 \
    --server.address 0.0.0.0 > streamlit.log 2>&1 &

STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

# 3. Wait for Streamlit to start
echo "Waiting for Streamlit to start..."
for i in {1..30}; do
    if curl -s http://localhost:8501 > /dev/null; then
        echo "✓ Streamlit is running"
        break
    fi
    sleep 1
done

# 4. Run the UI tests
echo ""
echo "Running UI tests with Selenium..."
python3 test_streamlit_ui_complete.py

TEST_RESULT=$?

# 5. Cleanup
echo ""
echo "Cleaning up..."
kill $STREAMLIT_PID 2>/dev/null || true

echo ""
echo "========================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All UI tests passed!"
else
    echo "❌ Some tests failed. Check the output above."
fi
echo "========================================"

exit $TEST_RESULT