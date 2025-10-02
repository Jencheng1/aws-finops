#!/usr/bin/env python3
"""
Test script for Tag Compliance Integration with FinOps Platform
Tests Lambda function, report generation, and Streamlit UI
"""

import json
import boto3
import time
from datetime import datetime
import sys

def test_lambda_integration():
    """Test Lambda function integration"""
    print("\n=== Testing Lambda Function Integration ===")
    
    lambda_client = boto3.client('lambda')
    
    # Test 1: Basic scan
    print("\nTest 1: Running compliance scan...")
    test_event = {'action': 'scan'}
    
    try:
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print("✓ Scan successful:")
            print("  - Total resources: {}".format(body.get('total_resources', 0)))
            print("  - Compliant: {}".format(body.get('compliant_count', 0)))
            print("  - Non-compliant: {}".format(body.get('non_compliant_count', 0)))
            print("  - Compliance rate: {:.1f}%".format(body.get('compliance_rate', 0)))
        else:
            print("✗ Scan failed with status: {}".format(result.get('statusCode')))
            return False
            
    except Exception as e:
        print("✗ Lambda invocation failed: {}".format(str(e)))
        return False
    
    # Test 2: Get compliance report
    print("\nTest 2: Generating compliance report...")
    test_event = {
        'action': 'report',
        'report_type': 'summary'
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            print("✓ Report generation successful")
        else:
            print("✗ Report generation failed")
            return False
            
    except Exception as e:
        print("✗ Report generation failed: {}".format(str(e)))
        return False
    
    # Test 3: Check specific resource
    print("\nTest 3: Checking specific resource compliance...")
    # Use a known Lambda function ARN
    test_event = {
        'action': 'get_resource',
        'resource_arn': 'arn:aws:lambda:us-east-1:637423485585:function:tag-compliance-checker'
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print("✓ Resource check successful:")
            print("  - Resource: {}".format(body.get('resource_arn', 'Unknown')))
            print("  - Compliant: {}".format(body.get('compliant', False)))
            print("  - Missing tags: {}".format(body.get('missing_tags', [])))
        else:
            print("✗ Resource check failed")
            return False
            
    except Exception as e:
        print("✗ Resource check failed: {}".format(str(e)))
        return False
    
    print("\n✓ All Lambda integration tests passed!")
    return True

def test_report_generator():
    """Test report generator module"""
    print("\n=== Testing Report Generator Module ===")
    
    try:
        # Import the report generator
        sys.path.insert(0, '/home/ec2-user/finops/aws-finops')
        from finops_report_generator import FinOpsReportGenerator
        
        generator = FinOpsReportGenerator()
        
        # Test 1: Generate PDF report
        print("\nTest 1: Generating PDF report...")
        try:
            pdf_path = generator.generate_pdf_report('executive')
            if pdf_path:
                print("✓ PDF report generated: {}".format(pdf_path))
            else:
                print("✗ PDF generation failed")
                return False
        except Exception as e:
            print("✗ PDF generation error: {}".format(str(e)))
            return False
        
        # Test 2: Generate Excel report
        print("\nTest 2: Generating Excel report...")
        try:
            excel_path = generator.generate_excel_report()
            if excel_path:
                print("✓ Excel report generated: {}".format(excel_path))
            else:
                print("✗ Excel generation failed")
                return False
        except Exception as e:
            print("✗ Excel generation error: {}".format(str(e)))
            return False
        
        # Test 3: Generate JSON report
        print("\nTest 3: Generating JSON report...")
        try:
            json_path = generator.generate_json_report()
            if json_path:
                print("✓ JSON report generated: {}".format(json_path))
            else:
                print("✗ JSON generation failed")
                return False
        except Exception as e:
            print("✗ JSON generation error: {}".format(str(e)))
            return False
        
        print("\n✓ All report generation tests passed!")
        return True
        
    except ImportError as e:
        print("✗ Failed to import report generator: {}".format(str(e)))
        return False
    except Exception as e:
        print("✗ Report generator test failed: {}".format(str(e)))
        return False

def test_streamlit_endpoints():
    """Test Streamlit application endpoints"""
    print("\n=== Testing Streamlit Application Endpoints ===")
    
    import requests
    
    # Test main FinOps dashboard
    print("\nTest 1: Main FinOps Dashboard...")
    try:
        response = requests.get('http://localhost:8502', timeout=5)
        if response.status_code == 200:
            print("✓ Main dashboard is accessible")
        else:
            print("✗ Main dashboard returned status: {}".format(response.status_code))
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Main dashboard is not running on port 8502")
        return False
    except Exception as e:
        print("✗ Error accessing main dashboard: {}".format(str(e)))
        return False
    
    # Test Apptio reconciliation dashboard
    print("\nTest 2: Apptio Reconciliation Dashboard...")
    try:
        response = requests.get('http://localhost:8504', timeout=5)
        if response.status_code == 200:
            print("✓ Apptio dashboard is accessible")
        else:
            print("✗ Apptio dashboard returned status: {}".format(response.status_code))
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Apptio dashboard is not running on port 8504")
        return False
    except Exception as e:
        print("✗ Error accessing Apptio dashboard: {}".format(str(e)))
        return False
    
    print("\n✓ All Streamlit endpoints are accessible!")
    return True

def test_tag_compliance_agent():
    """Test tag compliance agent"""
    print("\n=== Testing Tag Compliance Agent ===")
    
    try:
        sys.path.insert(0, '/home/ec2-user/finops/aws-finops')
        from tag_compliance_agent import TagComplianceAgent
        
        agent = TagComplianceAgent()
        
        # Test 1: Get compliance status
        print("\nTest 1: Getting compliance status...")
        try:
            status = agent.get_compliance_status()
            if status:
                print("✓ Compliance status retrieved successfully")
                print("  - Compliance rate: {:.1f}%".format(status.get('compliance_rate', 0)))
            else:
                print("✗ Failed to get compliance status")
                return False
        except Exception as e:
            print("✗ Error getting compliance status: {}".format(str(e)))
            return False
        
        # Test 2: Get non-compliant resources
        print("\nTest 2: Getting non-compliant resources...")
        try:
            resources = agent.get_non_compliant_resources(limit=5)
            if resources:
                print("✓ Retrieved {} non-compliant resources".format(len(resources)))
            else:
                print("✓ No non-compliant resources found (or error)")
        except Exception as e:
            print("✗ Error getting non-compliant resources: {}".format(str(e)))
            return False
        
        print("\n✓ Tag compliance agent tests passed!")
        return True
        
    except ImportError as e:
        print("✗ Failed to import tag compliance agent: {}".format(str(e)))
        return False
    except Exception as e:
        print("✗ Tag compliance agent test failed: {}".format(str(e)))
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("FinOps Tag Compliance Integration Test Suite")
    print("Started at: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("=" * 60)
    
    # Track test results
    results = {
        'lambda_integration': False,
        'report_generator': False,
        'streamlit_endpoints': False,
        'tag_compliance_agent': False
    }
    
    # Run tests
    results['lambda_integration'] = test_lambda_integration()
    time.sleep(2)  # Brief pause between tests
    
    results['report_generator'] = test_report_generator()
    time.sleep(2)
    
    results['streamlit_endpoints'] = test_streamlit_endpoints()
    time.sleep(2)
    
    results['tag_compliance_agent'] = test_tag_compliance_agent()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print("{}: {}".format(test_name.replace('_', ' ').title(), status))
        if result:
            passed += 1
    
    print("\nTotal: {}/{} tests passed".format(passed, len(results)))
    
    if passed == len(results):
        print("\n✓ All tests passed! Tag compliance is fully integrated.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())