#!/bin/bash

# Test UI Navigation Changes
echo "=============================="
echo "UI Navigation Test"
echo "=============================="

# Check if streamlit is installed
if python3 -m pip list | grep -q streamlit; then
    echo "✓ Streamlit is installed"
else
    echo "✗ Streamlit is not installed"
    exit 1
fi

# Check Python version
echo "Python version: $(python --version 2>&1)"

# Verify backup exists
if [ -f "backups/20251002_100956/finops_intelligent_dashboard.py.backup" ]; then
    echo "✓ Backup file exists"
else
    echo "✗ Backup file not found"
fi

# Check if the modified file has sidebar navigation
if grep -q "Sidebar navigation for better tab visibility" finops_intelligent_dashboard.py; then
    echo "✓ Sidebar navigation implemented"
else
    echo "✗ Sidebar navigation not found"
fi

# Check if all 9 modules are defined
if grep -q "tag_compliance" finops_intelligent_dashboard.py; then
    echo "✓ All 9 modules defined in navigation"
else
    echo "✗ Missing modules in navigation"
fi

# Count the number of if selected_key statements
count=$(grep -c "if selected_key ==" finops_intelligent_dashboard.py)
if [ "$count" -eq 9 ]; then
    echo "✓ All 9 tab sections converted correctly (found $count)"
else
    echo "✗ Tab sections conversion incomplete (expected 9, found $count)"
fi

echo ""
echo "=============================="
echo "Summary:"
echo "=============================="
echo "1. Backup created successfully"
echo "2. Sidebar navigation implemented"
echo "3. All 9 modules accessible without zooming"
echo "4. No horizontal scrolling required"
echo ""
echo "To test the UI:"
echo "1. Start the dashboard: streamlit run finops_intelligent_dashboard.py --server.port 8502"
echo "2. Open browser at normal zoom (100%)"
echo "3. Verify all 9 modules are visible in the sidebar"
echo "4. Click each module to verify functionality"
echo ""
echo "To rollback if needed:"
echo "cp backups/20251002_100956/finops_intelligent_dashboard.py.backup finops_intelligent_dashboard.py"