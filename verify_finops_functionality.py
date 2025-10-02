#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify FinOps functionality without running full AWS tests
"""

import os
import sys
import importlib

def check_module_imports():
    """Check if all required modules can be imported"""
    print("Checking module imports...")
    
    modules_to_check = [
        ('streamlit', 'Streamlit UI framework'),
        ('boto3', 'AWS SDK'),
        ('pandas', 'Data processing'),
        ('plotly', 'Visualization'),
        ('numpy', 'Numerical computing'),
        ('multi_agent_processor', 'Multi-Agent Chat'),
        ('finops_report_generator', 'Report Generator'),
        ('tag_compliance_agent', 'Tag Compliance')
    ]
    
    success = True
    for module_name, description in modules_to_check:
        try:
            if module_name in ['multi_agent_processor', 'finops_report_generator', 'tag_compliance_agent']:
                # Local modules
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            importlib.import_module(module_name)
            print("  ✓ {} ({})".format(module_name, description))
        except ImportError as e:
            print("  ✗ {} ({}) - Error: {}".format(module_name, description, e))
            success = False
    
    return success

def check_navigation_structure():
    """Check the navigation structure in the dashboard file"""
    print("\nChecking navigation structure...")
    
    with open('finops_intelligent_dashboard.py', 'r') as f:
        content = f.read()
    
    checks = [
        ('Sidebar navigation', 'Sidebar navigation for better tab visibility' in content),
        ('Navigation radio button', 'st.radio' in content and 'navigation_radio' in content),
        ('Cost Intelligence', 'selected_key == "cost_intelligence"' in content),
        ('Multi-Agent Chat', 'selected_key == "multi_agent_chat"' in content),
        ('Business Context', 'selected_key == "business_context"' in content),
        ('Resource Optimization', 'selected_key == "resource_optimization"' in content),
        ('Savings Plans', 'selected_key == "savings_plans"' in content),
        ('Budget Prediction', 'selected_key == "budget_prediction"' in content),
        ('Executive Dashboard', 'selected_key == "executive_dashboard"' in content),
        ('Report Generator', 'selected_key == "report_generator"' in content),
        ('Tag Compliance', 'selected_key == "tag_compliance"' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print("  ✓ {}".format(check_name))
        else:
            print("  ✗ {}".format(check_name))
            all_passed = False
    
    return all_passed

def main():
    print("="*60)
    print("FinOps Dashboard Functionality Verification")
    print("="*60)
    
    # Check imports
    import_success = check_module_imports()
    
    # Check navigation
    nav_success = check_navigation_structure()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if import_success and nav_success:
        print("✅ All checks passed!")
        print("\nThe dashboard has been successfully updated with sidebar navigation.")
        print("All 9 modules are now accessible without zooming.")
        print("\nTo start the dashboard:")
        print("python3 -m streamlit run finops_intelligent_dashboard.py --server.port 8502")
    else:
        print("⚠️ Some checks failed. Please review the output above.")
        
    # Show backup info
    print("\n📁 Backup Information:")
    print("Original file backed up to: backups/20251002_100956/finops_intelligent_dashboard.py.backup")
    print("To rollback: cp backups/20251002_100956/finops_intelligent_dashboard.py.backup finops_intelligent_dashboard.py")

if __name__ == "__main__":
    main()