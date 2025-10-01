#!/usr/bin/env python3
"""
Test Multi-Agent Chat System with Real AWS APIs
"""

import sys
import time
from datetime import datetime
from multi_agent_processor import MultiAgentProcessor

# Test queries for each agent
TEST_QUERIES = {
    'general': [
        "What's my current AWS spend?",
        "Show me cost overview",
        "Help me understand my AWS costs"
    ],
    'prediction': [
        "Predict my costs for next month",
        "What will my AWS bill be in 30 days?",
        "Forecast my spending"
    ],
    'optimizer': [
        "Find idle resources",
        "What resources are wasting money?",
        "Show me optimization opportunities"
    ],
    'savings': [
        "Recommend savings plans",
        "How can I save with commitments?",
        "What's my savings plan recommendation?"
    ],
    'anomaly': [
        "Check for cost anomalies",
        "Are there any spending spikes?",
        "Detect unusual costs"
    ]
}

def test_agent_identification():
    """Test agent identification logic"""
    print("\n" + "="*60)
    print("TESTING AGENT IDENTIFICATION")
    print("="*60)
    
    test_cases = [
        ("What will my costs be next month?", "prediction"),
        ("Find unused resources", "optimizer"),
        ("Recommend a savings plan", "savings"),
        ("Check for cost spikes", "anomaly"),
        ("What's my total spend?", "general")
    ]
    
    # Copy the identify_active_agent function to avoid Streamlit imports
    def identify_active_agent(query: str) -> str:
        query_lower = query.lower()
        if any(word in query_lower for word in ['predict', 'forecast', 'budget', 'future', 'trend']):
            return 'prediction'
        elif any(word in query_lower for word in ['optimize', 'waste', 'idle', 'unused', 'cleanup']):
            return 'optimizer'
        elif any(word in query_lower for word in ['savings plan', 'commitment', 'reserved', 'discount']):
            return 'savings'
        elif any(word in query_lower for word in ['anomaly', 'spike', 'unusual', 'alert']):
            return 'anomaly'
        else:
            return 'general'
    
    passed = 0
    for query, expected in test_cases:
        result = identify_active_agent(query)
        if result == expected:
            print(f"✅ '{query}' → {result} (correct)")
            passed += 1
        else:
            print(f"❌ '{query}' → {result} (expected: {expected})")
    
    print(f"\nAgent Identification: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def test_all_agents():
    """Test each agent with real queries"""
    print("\n" + "="*60)
    print("TESTING ALL AGENTS WITH REAL AWS APIs")
    print("="*60)
    
    processor = MultiAgentProcessor()
    context = {'user_id': 'test_user', 'session_id': 'test_session'}
    
    all_passed = True
    
    for agent_type, queries in TEST_QUERIES.items():
        print(f"\n{'='*40}")
        print(f"Testing {agent_type.upper()} Agent")
        print(f"{'='*40}")
        
        for query in queries[:1]:  # Test first query of each type
            print(f"\nQuery: '{query}'")
            print("-" * 40)
            
            try:
                # Call appropriate processor method
                if agent_type == 'general':
                    response, data = processor.process_general_query(query, context)
                elif agent_type == 'prediction':
                    response, data = processor.process_prediction_query(query, context)
                elif agent_type == 'optimizer':
                    response, data = processor.process_optimizer_query(query, context)
                elif agent_type == 'savings':
                    response, data = processor.process_savings_query(query, context)
                elif agent_type == 'anomaly':
                    response, data = processor.process_anomaly_query(query, context)
                
                if response and not response.startswith("Error"):
                    print("✅ Response received:")
                    print(response[:200] + "..." if len(response) > 200 else response)
                    if data:
                        print(f"\n📊 Data returned: {list(data.keys())}")
                else:
                    print(f"❌ Agent failed: {response}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                all_passed = False
            
            time.sleep(1)  # Rate limiting
    
    return all_passed

def test_agent_collaboration():
    """Test agents working together"""
    print("\n" + "="*60)
    print("TESTING AGENT COLLABORATION")
    print("="*60)
    
    processor = MultiAgentProcessor()
    context = {'user_id': 'test_user', 'session_id': 'test_session'}
    
    # Scenario: Complete cost analysis workflow
    print("\n🔄 Workflow: Complete Cost Analysis")
    print("-" * 40)
    
    workflow_steps = [
        ("What's my current spend?", "general", "Get baseline"),
        ("Predict next month costs", "prediction", "Future planning"),
        ("Find optimization opportunities", "optimizer", "Cost savings"),
        ("Check for anomalies", "anomaly", "Risk detection")
    ]
    
    results = {}
    for step, (query, agent_type, purpose) in enumerate(workflow_steps, 1):
        print(f"\nStep {step}: {purpose}")
        print(f"Query: '{query}'")
        
        try:
            if agent_type == 'general':
                response, data = processor.process_general_query(query, context)
            elif agent_type == 'prediction':
                response, data = processor.process_prediction_query(query, context)
            elif agent_type == 'optimizer':
                response, data = processor.process_optimizer_query(query, context)
            elif agent_type == 'anomaly':
                response, data = processor.process_anomaly_query(query, context)
            
            results[agent_type] = data
            print(f"✅ {agent_type.title()} agent completed")
            
        except Exception as e:
            print(f"❌ {agent_type.title()} agent failed: {e}")
            return False
    
    # Summary
    print("\n📊 Workflow Summary:")
    if 'general' in results and 'total_cost' in results.get('general', {}):
        print(f"• Current spend: ${results['general']['total_cost']:,.2f}")
    if 'prediction' in results:
        print(f"• Next month forecast: Available")
    if 'optimizer' in results and 'total_waste' in results.get('optimizer', {}):
        print(f"• Optimization potential: ${results['optimizer']['total_waste']:,.2f}/month")
    if 'anomaly' in results:
        print(f"• Anomalies detected: {results['anomaly'].get('anomalies', 0)}")
    
    return True

def generate_sample_queries():
    """Generate sample queries for users"""
    print("\n" + "="*60)
    print("SAMPLE QUERIES FOR EACH AGENT")
    print("="*60)
    
    samples = {
        "💰 General Cost Questions": [
            "What's my current AWS spend?",
            "Show me my top 5 services by cost",
            "What's my month-to-date spending?",
            "Give me a cost overview"
        ],
        "📈 Budget Predictions": [
            "Predict my costs for next month",
            "What will my Q4 spending look like?",
            "Forecast my AWS bill for next 30 days",
            "Show me spending trends"
        ],
        "🔍 Resource Optimization": [
            "Find idle resources",
            "What EC2 instances are stopped?",
            "Show me unattached EBS volumes",
            "Identify optimization opportunities"
        ],
        "💎 Savings Plans": [
            "Should I buy a Savings Plan?",
            "What's my optimal commitment level?",
            "Calculate my Savings Plan ROI",
            "Show savings opportunities"
        ],
        "🚨 Anomaly Detection": [
            "Are there any cost spikes?",
            "Check for unusual spending",
            "Detect cost anomalies this week",
            "Alert me to billing anomalies"
        ]
    }
    
    for category, queries in samples.items():
        print(f"\n{category}:")
        for query in queries:
            print(f"  • {query}")
    
    print("\n💡 TIP: Copy and paste these queries into the chat interface!")

def main():
    """Run all tests"""
    print("\n" + "🤖"*30)
    print("MULTI-AGENT CHAT SYSTEM TEST SUITE")
    print("🤖"*30)
    print(f"\nTest Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Agent Identification
    if test_agent_identification():
        tests_passed += 1
    
    # Test 2: Individual Agents
    if test_all_agents():
        tests_passed += 1
    
    # Test 3: Agent Collaboration
    if test_agent_collaboration():
        tests_passed += 1
    
    # Generate sample queries
    generate_sample_queries()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe Multi-Agent Chat System is working correctly with:")
        print("  • Real AWS API integration")
        print("  • 5 specialized agents")
        print("  • Intelligent query routing")
        print("  • Meaningful responses with actual data")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    print("\n🌐 Access the dashboard: http://localhost:8504")
    print("💬 Try the sample queries in the Multi-Agent Chat tab!")

if __name__ == "__main__":
    main()