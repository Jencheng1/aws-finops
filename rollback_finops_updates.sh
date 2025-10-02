#!/bin/bash
#
# FinOps Platform Rollback Script
# Use this script to rollback to previous version if any issues occur
#

echo "🔄 FinOps Platform Rollback Script"
echo "=================================="

# Get the backup directory
BACKUP_DIR=$(ls -td backups/20* 2>/dev/null | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Error: No backup directory found!"
    echo "Cannot proceed with rollback."
    exit 1
fi

echo "📁 Found backup directory: $BACKUP_DIR"
echo ""

# Confirmation prompt
read -p "⚠️  Are you sure you want to rollback to the backup from $BACKUP_DIR? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled."
    exit 0
fi

echo ""
echo "🚀 Starting rollback process..."

# Create a pre-rollback backup just in case
PRE_ROLLBACK_DIR="backups/pre_rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$PRE_ROLLBACK_DIR"

echo "📦 Creating pre-rollback backup..."
cp finops_intelligent_dashboard.py "$PRE_ROLLBACK_DIR/" 2>/dev/null
cp multi_agent_processor.py "$PRE_ROLLBACK_DIR/" 2>/dev/null
cp finops_report_generator.py "$PRE_ROLLBACK_DIR/" 2>/dev/null
cp tag_compliance_agent.py "$PRE_ROLLBACK_DIR/" 2>/dev/null
cp lambda_tag_compliance.py "$PRE_ROLLBACK_DIR/" 2>/dev/null

# Perform rollback
echo "🔄 Rolling back files..."

if [ -f "$BACKUP_DIR/finops_intelligent_dashboard.py" ]; then
    cp "$BACKUP_DIR/finops_intelligent_dashboard.py" ./
    echo "✅ Restored: finops_intelligent_dashboard.py"
else
    echo "⚠️  Warning: finops_intelligent_dashboard.py not found in backup"
fi

if [ -f "$BACKUP_DIR/apptio_mcp_reconciliation.py" ]; then
    cp "$BACKUP_DIR/apptio_mcp_reconciliation.py" ./
    echo "✅ Restored: apptio_mcp_reconciliation.py"
else
    echo "⚠️  Warning: apptio_mcp_reconciliation.py not found in backup"
fi

# Remove new files that weren't in the original version
echo ""
echo "🗑️  Removing new feature files..."
NEW_FILES=(
    "finops_report_generator.py"
    "tag_compliance_agent.py"
    "lambda_tag_compliance.py"
    "test_finops_features.py"
)

for file in "${NEW_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "✅ Removed: $file"
    fi
done

# Check if we need to restore the original multi_agent_processor.py
if [ -f "multi_agent_processor.py.backup" ]; then
    cp multi_agent_processor.py.backup multi_agent_processor.py
    echo "✅ Restored: multi_agent_processor.py from backup"
fi

echo ""
echo "🔍 Checking services status..."

# Check if services are running
DASHBOARD_PID=$(pgrep -f "streamlit.*finops_intelligent_dashboard.py")
APPTIO_PID=$(pgrep -f "streamlit.*apptio_mcp_reconciliation.py")

if [ ! -z "$DASHBOARD_PID" ] || [ ! -z "$APPTIO_PID" ]; then
    echo "⚠️  Services are currently running. They need to be restarted."
    echo ""
    read -p "Do you want to restart the services now? (yes/no): " restart_confirm
    
    if [ "$restart_confirm" == "yes" ]; then
        echo "🛑 Stopping services..."
        
        # Kill services
        if [ ! -z "$DASHBOARD_PID" ]; then
            kill $DASHBOARD_PID
            echo "✅ Stopped FinOps Dashboard"
        fi
        
        if [ ! -z "$APPTIO_PID" ]; then
            kill $APPTIO_PID
            echo "✅ Stopped Apptio Dashboard"
        fi
        
        sleep 2
        
        echo ""
        echo "🚀 Starting services with rolled back version..."
        
        # Start services
        nohup streamlit run finops_intelligent_dashboard.py --server.port 8502 > finops_dashboard.log 2>&1 &
        echo "✅ Started FinOps Dashboard on port 8502"
        
        nohup streamlit run apptio_mcp_reconciliation.py --server.port 8504 > apptio_dashboard.log 2>&1 &
        echo "✅ Started Apptio Dashboard on port 8504"
        
        echo ""
        echo "⏳ Waiting for services to start..."
        sleep 5
        
        # Check if services started successfully
        NEW_DASHBOARD_PID=$(pgrep -f "streamlit.*finops_intelligent_dashboard.py")
        NEW_APPTIO_PID=$(pgrep -f "streamlit.*apptio_mcp_reconciliation.py")
        
        if [ ! -z "$NEW_DASHBOARD_PID" ] && [ ! -z "$NEW_APPTIO_PID" ]; then
            echo "✅ Services restarted successfully!"
        else
            echo "❌ Error: Services failed to start. Check logs for details."
        fi
    fi
else
    echo "ℹ️  No services currently running."
fi

echo ""
echo "✅ Rollback completed!"
echo ""
echo "📋 Summary:"
echo "- Pre-rollback backup saved to: $PRE_ROLLBACK_DIR"
echo "- Rolled back to version from: $BACKUP_DIR"
echo "- New feature files have been removed"
echo ""
echo "🔍 Next steps:"
echo "1. Test the rolled back version to ensure it's working correctly"
echo "2. Check the application URLs:"
echo "   - FinOps Dashboard: http://localhost:8502"
echo "   - Apptio Dashboard: http://localhost:8504"
echo "3. If you need to restore the new features, they are backed up in: $PRE_ROLLBACK_DIR"
echo ""
echo "💡 To re-apply the updates later, you can restore from: $PRE_ROLLBACK_DIR"