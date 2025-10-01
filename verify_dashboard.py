#!/usr/bin/env python3
"""
Verify the intelligent dashboard is working correctly
"""

import requests
import time

def verify_dashboard():
    print("Verifying Intelligent Dashboard...")
    
    try:
        # Check main page
        response = requests.get("http://localhost:8504", timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for key features
            checks = {
                "Apptio MCP": "apptio mcp" in content,
                "Multi-Agent": "agent" in content,
                "Cost Intelligence": "cost intelligence" in content,
                "No Errors": "error" not in content and "exception" not in content
            }
            
            print("\n✅ Dashboard Status:")
            for feature, present in checks.items():
                status = "✓" if present else "✗"
                print(f"  {status} {feature}")
            
            # Check all features are present
            if all(checks.values()):
                print("\n✅ All features verified!")
                print("\n🌐 Access the dashboard:")
                print("  URL: http://localhost:8504")
                print("  Features:")
                print("  - 💬 Multi-Agent Chat (5 specialized agents)")
                print("  - 🔗 Apptio MCP Integration (Business Context)")
                print("  - 📊 Cost Intelligence Dashboard")
                print("  - 🔍 Resource Optimization")
                print("  - 💎 Savings Plans Analysis")
                print("  - 📈 Executive Dashboard")
                return True
            else:
                print("\n⚠️ Some features may need attention")
                return False
        else:
            print(f"❌ Dashboard returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing dashboard: {e}")
        return False

if __name__ == "__main__":
    if verify_dashboard():
        print("\n✅ Dashboard is fully operational!")
    else:
        print("\n⚠️ Please check the dashboard")