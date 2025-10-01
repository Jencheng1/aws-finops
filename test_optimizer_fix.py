#!/usr/bin/env python3
"""
Test the optimizer agent with orphaned snapshots
"""

from multi_agent_processor import MultiAgentProcessor

print("Testing Resource Optimizer with Orphaned Snapshots")
print("=" * 60)

processor = MultiAgentProcessor()
context = {'user_id': 'test_user', 'session_id': 'test_session'}

# Test queries
test_queries = [
    "Find idle resources",
    "Analyze my costs and recommend optimizations",
    "What resources are wasting money?"
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    print("-" * 40)
    
    try:
        response, data = processor.process_optimizer_query(query, context)
        
        print("Response preview:")
        print(response[:300] + "...")
        
        if 'summary' in data:
            print("\n📊 Resource Summary:")
            summary = data['summary']
            print(f"  - Stopped Instances: {summary.get('stopped_instances_count', 0)}")
            print(f"  - Unattached Volumes: {summary.get('unattached_volumes_count', 0)}")
            print(f"  - Unused EIPs: {summary.get('unused_eips_count', 0)}")
            print(f"  - Underutilized Instances: {summary.get('underutilized_instances_count', 0)}")
            print(f"  - Orphaned Snapshots: {summary.get('orphaned_snapshots_count', 0)}")
            
            if 'orphaned_snapshots' in data and len(data['orphaned_snapshots']) > 0:
                print(f"\n📸 Found {len(data['orphaned_snapshots'])} orphaned snapshots!")
                total_size = sum(s['size_gb'] for s in data['orphaned_snapshots'])
                total_cost = sum(s['monthly_cost'] for s in data['orphaned_snapshots'])
                print(f"  Total Size: {total_size} GB")
                print(f"  Monthly Cost: ${total_cost:.2f}")
                
        if 'total_monthly_savings' in data:
            print(f"\n💰 Total Savings Potential: ${data['total_monthly_savings']:.2f}/month")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("Note: The optimizer correctly shows 0 unattached volumes and EIPs")
print("because all volumes are attached and all EIPs are associated.")
print("However, it should now find orphaned snapshots!")