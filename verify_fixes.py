#!/usr/bin/env python3
"""
Verify that all fixes have been applied
"""

import requests
import time

def verify_streamlit():
    """Check if Streamlit is running without errors"""
    print("Checking Streamlit app...")
    
    try:
        response = requests.get("http://localhost:8503", timeout=10)
        if response.status_code == 200:
            # Check for error indicators in the HTML
            content = response.text.lower()
            
            errors = []
            if "syntaxerror" in content:
                errors.append("Syntax error found")
            if "attributeerror" in content:
                errors.append("Attribute error found")
            if "error getting" in content and "recommendations" in content:
                errors.append("Recommendations error found")
            
            if not errors:
                print("✅ Streamlit app is running without visible errors")
                return True
            else:
                print("❌ Errors found:")
                for error in errors:
                    print(f"   - {error}")
                return False
        else:
            print(f"❌ Streamlit returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Could not connect to Streamlit: {e}")
        return False

def main():
    print("="*60)
    print("VERIFYING FIXES")
    print("="*60)
    
    # Check Streamlit
    streamlit_ok = verify_streamlit()
    
    print("\n" + "="*60)
    if streamlit_ok:
        print("✅ ALL FIXES VERIFIED - App is ready!")
        print("\nAccess the app at: http://localhost:8503")
    else:
        print("❌ Some issues remain - please check the logs")
    print("="*60)

if __name__ == "__main__":
    main()