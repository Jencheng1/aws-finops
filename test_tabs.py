#!/usr/bin/env python3
"""Test if tabs are properly defined in dashboard"""

# Read the dashboard file
with open('finops_intelligent_dashboard.py', 'r') as f:
    content = f.read()

# Check for tab definitions
print("Checking tab definitions...")

# Find the tabs line
import re
tabs_match = re.search(r'st\.tabs\(\[(.*?)\]\)', content, re.DOTALL)
if tabs_match:
    tabs_str = tabs_match.group(1)
    tabs = re.findall(r'"([^"]+)"', tabs_str)
    print(f"\nFound {len(tabs)} tabs:")
    for i, tab in enumerate(tabs, 1):
        print(f"{i}. {tab}")
else:
    print("ERROR: Could not find st.tabs definition")

# Check for tab implementations
print("\nChecking tab implementations:")
for i in range(1, 10):
    if f"with tab{i}:" in content:
        print(f"✓ tab{i} is implemented")
    else:
        print(f"✗ tab{i} is NOT implemented")

# Check specific content
print("\nChecking for specific content:")
checks = [
    ("Report Generator header", "st.header(\"📋 FinOps Report Generator\")"),
    ("Tag Compliance header", "st.header(\"🏷️ Resource Tag Compliance\")"),
    ("report_generator import", "from finops_report_generator import"),
    ("tag_compliance_agent import", "from tag_compliance_agent import")
]

for name, pattern in checks:
    if pattern in content:
        print(f"✓ Found: {name}")
    else:
        print(f"✗ Missing: {name}")