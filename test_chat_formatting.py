#!/usr/bin/env python3
"""
Test chatbot response formatting
"""

from multi_agent_processor import MultiAgentProcessor

# Test the specific query that was having issues
processor = MultiAgentProcessor()
context = {'user_id': 'test_user', 'session_id': 'test_session'}

# Test "Show me top spending services"
print("Testing query: 'Show me top spending services'")
print("=" * 60)

response, data = processor.process_general_query("Show me top spending services", context)

print("\nRaw Response:")
print("-" * 60)
print(response)

print("\n\nData returned:")
print("-" * 60)
print(data)

# Check for formatting issues
print("\n\nFormatting Check:")
print("-" * 60)

# Check for asterisk issues
if '**Month-to-Date' in response:
    print("✅ Bold formatting correct")
else:
    print("❌ Bold formatting issue found")

# Check for proper line breaks
if '\n' in response:
    print("✅ Line breaks present")
else:
    print("❌ Missing line breaks")

# Check data structure
if data and 'total_cost' in data:
    print(f"✅ Total cost: ${data['total_cost']:,.2f}")
else:
    print("❌ Missing total cost in data")

if data and 'top_services' in data:
    print(f"✅ Top services: {len(data['top_services'])} found")
    for service, cost in data['top_services'][:3]:
        print(f"   - {service}: ${cost:,.2f}")
else:
    print("❌ Missing top services in data")

print("\n" + "=" * 60)
print("If formatting looks correct above, the issue may be with Streamlit rendering.")