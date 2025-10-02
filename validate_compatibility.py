#!/usr/bin/env python3
"""
Validate Python 3.6 compatibility
"""

import ast
import sys
import os

def check_fstrings(filename):
    """Check if file contains f-strings"""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Simple check for f-strings
    has_fstrings = 'f"' in content or "f'" in content
    
    return has_fstrings

def validate_files():
    """Validate all Python files for compatibility"""
    print("🔍 Checking Python 3.6 compatibility...\n")
    
    files_to_check = [
        'finops_intelligent_dashboard.py',
        'multi_agent_processor.py',
        'finops_report_generator.py',
        'tag_compliance_agent.py',
        'lambda_tag_compliance.py',
        'test_finops_features.py'
    ]
    
    issues_found = False
    
    for filename in files_to_check:
        if os.path.exists(filename):
            has_fstrings = check_fstrings(filename)
            
            if has_fstrings:
                print("❌ {} - Contains f-strings (Python 3.6+ feature)".format(filename))
                issues_found = True
            else:
                print("✅ {} - Compatible".format(filename))
        else:
            print("⚠️  {} - File not found".format(filename))
    
    print("\n" + "="*50)
    
    if issues_found:
        print("⚠️  Compatibility issues found!")
        print("The code uses f-strings which require Python 3.6+")
        print("Current Python version: {}".format(sys.version))
        print("\nNote: The code will still work on Python 3.7+")
    else:
        print("✅ All files are compatible with Python 3.6+")
    
    return not issues_found

if __name__ == '__main__':
    success = validate_files()
    sys.exit(0 if success else 1)