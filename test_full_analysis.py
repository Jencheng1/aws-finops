#!/usr/bin/env python3
"""
Test the full analysis functionality
"""

from budget_prediction_agent import get_budget_insights
import json

def test_full_analysis():
    """Test that full analysis works"""
    print("Testing Full Analysis functionality...")
    
    try:
        # Run the same analysis that the button would trigger
        insights = get_budget_insights(months_history=2, prediction_days=30)
        
        print("\n✅ Analysis completed successfully!")
        print(f"\nResults:")
        print(f"- Predictions: ${insights['predictions']['summary']['total_predicted_cost']:.2f} (30-day forecast)")
        print(f"- Anomalies: {insights['anomalies']['summary']['total_anomalies']} detected")
        print(f"- Savings: ${insights['trusted_advisor']['total_monthly_savings']:.2f}/month potential")
        print(f"- Recommendations: {len(insights['recommendations'])} generated")
        
        if insights['recommendations']:
            print("\nTop Recommendations:")
            for i, rec in enumerate(insights['recommendations'][:3], 1):
                print(f"  {i}. {rec['title']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_analysis()
    if success:
        print("\n✅ Full analysis function is working correctly!")
        print("The button in the UI should now trigger this analysis.")
    else:
        print("\n❌ Full analysis has issues that need fixing.")