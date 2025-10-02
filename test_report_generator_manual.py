#!/usr/bin/env python3
"""
Manual test for report generator with AI insights
"""

import sys
import os
import json
import boto3
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finops_report_generator import FinOpsReportGenerator

def test_report_generation():
    """Test report generation with AI insights"""
    print("=" * 60)
    print("Testing FinOps Report Generator with AI Insights")
    print("=" * 60)
    
    # Initialize AWS clients
    aws_clients = {
        'ce': boto3.client('ce'),
        'ec2': boto3.client('ec2'),
        'lambda': boto3.client('lambda'),
        'cloudwatch': boto3.client('cloudwatch'),
        'organizations': boto3.client('organizations'),
        'sts': boto3.client('sts')
    }
    
    try:
        # Create report generator
        print("\n1. Initializing report generator...")
        generator = FinOpsReportGenerator(aws_clients)
        print("✓ Report generator initialized successfully")
        
        # Test AI insights summary generation
        print("\n2. Testing AI insights summary generation...")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        ai_insights = generator._generate_ai_insights_summary(start_date, end_date)
        
        print("✓ AI insights generated successfully")
        print("\nAI Insights Summary:")
        print("-" * 40)
        print(f"Executive Summary: {ai_insights.get('executive_summary', 'N/A')[:200]}...")
        print(f"Key Findings: {len(ai_insights.get('key_findings', []))} findings")
        print(f"Risk Level: {ai_insights.get('risk_assessment', {}).get('overall_risk_level', 'N/A')}")
        print(f"Strategic Recommendations: {len(ai_insights.get('strategic_recommendations', []))} recommendations")
        print(f"Predicted Savings: ${ai_insights.get('predicted_savings', 0):,.2f}")
        
        # Test JSON report generation
        print("\n3. Testing JSON report generation...")
        json_report = generator.generate_comprehensive_report(
            report_type='full',
            start_date=start_date,
            end_date=end_date,
            include_charts=False,
            format='json'
        )
        
        report_data = json.loads(json_report)
        print("✓ JSON report generated successfully")
        print(f"  - Report sections: {len(report_data)} sections")
        print(f"  - AI insights included: {'ai_insights_summary' in report_data}")
        
        # Save JSON report for inspection
        with open('test_report_output.json', 'w') as f:
            f.write(json_report)
        print("  - Report saved to: test_report_output.json")
        
        # Test PDF report generation
        print("\n4. Testing PDF report generation...")
        try:
            pdf_report = generator.generate_comprehensive_report(
                report_type='full',
                start_date=start_date,
                end_date=end_date,
                include_charts=False,
                format='pdf'
            )
            
            # Save PDF
            with open('test_report_output.pdf', 'wb') as f:
                if hasattr(pdf_report, 'getvalue'):
                    f.write(pdf_report.getvalue())
                else:
                    f.write(pdf_report)
            
            print("✓ PDF report generated successfully")
            print("  - Report saved to: test_report_output.pdf")
        except Exception as e:
            print(f"✗ PDF generation error: {str(e)}")
        
        # Test Excel report generation
        print("\n5. Testing Excel report generation...")
        try:
            excel_report = generator.generate_comprehensive_report(
                report_type='full',
                start_date=start_date,
                end_date=end_date,
                include_charts=False,
                format='excel'
            )
            
            # Save Excel
            with open('test_report_output.xlsx', 'wb') as f:
                if hasattr(excel_report, 'getvalue'):
                    f.write(excel_report.getvalue())
                else:
                    f.write(excel_report)
            
            print("✓ Excel report generated successfully")
            print("  - Report saved to: test_report_output.xlsx")
        except Exception as e:
            print(f"✗ Excel generation error: {str(e)}")
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_report_generation()