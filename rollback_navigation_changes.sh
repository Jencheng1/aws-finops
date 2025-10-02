#!/bin/bash

# Rollback Navigation Changes Script

echo "=============================="
echo "Rollback Navigation Changes"
echo "=============================="

# Check if backup exists
BACKUP_FILE="backups/20251002_100956/finops_intelligent_dashboard.py.backup"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Found backup file: $BACKUP_FILE"
echo ""
echo "This will restore the original tab-based navigation."
echo "Are you sure you want to rollback? (yes/no)"
read -r response

if [ "$response" = "yes" ]; then
    # Create a backup of current version before rollback
    CURRENT_BACKUP="backups/$(date +%Y%m%d_%H%M%S)_before_rollback"
    mkdir -p "$CURRENT_BACKUP"
    cp finops_intelligent_dashboard.py "$CURRENT_BACKUP/finops_intelligent_dashboard.py"
    echo "✓ Created backup of current version in: $CURRENT_BACKUP"
    
    # Perform rollback
    cp "$BACKUP_FILE" finops_intelligent_dashboard.py
    echo "✓ Rollback completed successfully"
    echo ""
    echo "The dashboard has been restored to use tab-based navigation."
    echo "You may need to zoom out to see all 9 tabs."
    echo ""
    echo "To restart the dashboard:"
    echo "python3 -m streamlit run finops_intelligent_dashboard.py --server.port 8502"
else
    echo "Rollback cancelled."
fi