#!/usr/bin/env python3
"""
Use Case Tests for FinOps Tag Compliance Feature
Tests real-world scenarios for tag compliance functionality
"""

import json
import boto3
import time
import sys
from datetime import datetime

print("=" * 60)
print("FinOps Tag Compliance Use Case Tests")
print("Started at: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
print("=" * 60)

# Initialize clients
lambda_client = boto3.client('lambda')

def test_use_case_1_compliance_scan():
    """
    Use Case 1: Security team needs to identify all non-compliant resources
    """
    print("\n=== Use Case 1: Compliance Scan for Security Audit ===")
    print("Scenario: Security team needs a comprehensive list of resources missing required tags")
    
    try:
        # Invoke Lambda to scan resources
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'scan'})
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            print("\n✓ Compliance scan completed successfully:")
            print("  - Total resources scanned: {}".format(body['total_resources']))
            print("  - Compliant resources: {}".format(body['compliant_count']))
            print("  - Non-compliant resources: {}".format(body['non_compliant_count']))
            print("  - Compliance rate: {:.1f}%".format(body['compliance_rate']))
            
            print("\n  Missing Tags Summary:")
            for tag, count in body['missing_tags_summary'].items():
                print("    - {}: {} resources missing".format(tag, count))
            
            print("\n  Resources by Type:")
            for res_type, stats in list(body['resources_by_type'].items())[:5]:
                print("    - {}: {} total, {} compliant, {} non-compliant".format(
                    res_type, stats['total'], stats['compliant'], stats['non_compliant']
                ))
            
            return True
        else:
            print("✗ Scan failed with status: {}".format(result.get('statusCode')))
            return False
            
    except Exception as e:
        print("✗ Test failed: {}".format(str(e)))
        return False

def test_use_case_2_cost_allocation():
    """
    Use Case 2: Finance team needs to identify resources without CostCenter tags
    """
    print("\n=== Use Case 2: Cost Allocation Tag Audit ===")
    print("Scenario: Finance team needs to find all resources missing CostCenter tags for budget allocation")
    
    try:
        # First get the scan results
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'scan'})
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            # Find resources missing CostCenter
            missing_costcenter = body['missing_tags_summary'].get('CostCenter', 0)
            
            print("\n✓ Cost allocation audit completed:")
            print("  - Resources missing CostCenter tag: {}".format(missing_costcenter))
            print("  - Percentage of unallocated resources: {:.1f}%".format(
                (missing_costcenter / body['total_resources'] * 100) if body['total_resources'] > 0 else 0
            ))
            
            # Show some examples of non-compliant resources
            print("\n  Sample non-compliant resources:")
            count = 0
            for resource in body['non_compliant_resources']:
                if 'CostCenter' in resource.get('missing_tags', []):
                    print("    - Type: {}, ARN: {}...".format(
                        resource['resource_type'],
                        resource['resource_arn'][:60]
                    ))
                    count += 1
                    if count >= 3:
                        break
            
            # Estimate cost impact
            estimated_impact = body['summary']['cost_impact']
            print("\n  Estimated monthly cost impact: ${:,.2f}".format(estimated_impact))
            
            return True
        else:
            print("✗ Audit failed")
            return False
            
    except Exception as e:
        print("✗ Test failed: {}".format(str(e)))
        return False

def test_use_case_3_compliance_report():
    """
    Use Case 3: Management needs a compliance report for board meeting
    """
    print("\n=== Use Case 3: Executive Compliance Report ===")
    print("Scenario: CTO needs a summary report for board presentation")
    
    try:
        # Generate summary report
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'report',
                'report_type': 'summary'
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            print("\n✓ Executive report generated successfully:")
            print("  - Report type: {}".format(body.get('report_type', 'summary')))
            print("  - Generated at: {}".format(body.get('generated_at', 'N/A')))
            
            if 'latest_scan' in body:
                scan = body['latest_scan']
                print("\n  Latest Scan Results:")
                print("    - Scan time: {}".format(scan.get('timestamp', 'N/A')))
                print("    - Compliance rate: {:.1f}%".format(scan.get('compliance_rate', 0)))
                print("    - Total resources: {}".format(scan.get('total_resources', 0)))
                
            return True
        else:
            print("✗ Report generation failed")
            return False
            
    except Exception as e:
        print("✗ Test failed: {}".format(str(e)))
        return False

def test_use_case_4_specific_resource_check():
    """
    Use Case 4: Developer needs to check if their Lambda function is compliant
    """
    print("\n=== Use Case 4: Developer Resource Compliance Check ===")
    print("Scenario: Developer wants to verify their Lambda function has all required tags")
    
    try:
        # Check our tag-compliance-checker function itself
        resource_arn = 'arn:aws:lambda:us-east-1:637423485585:function:tag-compliance-checker'
        
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_resource',
                'resource_arn': resource_arn
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            print("\n✓ Resource compliance check completed:")
            print("  - Resource: {}".format(body.get('resource_type', 'Unknown')))
            print("  - ARN: {}...".format(body.get('resource_arn', '')[:60]))
            print("  - Compliance status: {}".format(
                "COMPLIANT" if body.get('compliant') else "NON-COMPLIANT"
            ))
            
            if body.get('compliant'):
                print("\n  All required tags present:")
                for tag in body.get('required_tags', []):
                    tag_value = body.get('existing_tags', {}).get(tag, 'N/A')
                    print("    - {}: {}".format(tag, tag_value))
            else:
                print("\n  Missing required tags:")
                for tag in body.get('missing_tags', []):
                    print("    - {}".format(tag))
                print("\n  Existing tags:")
                for tag, value in body.get('existing_tags', {}).items():
                    print("    - {}: {}".format(tag, value))
            
            return True
        else:
            print("✗ Resource check failed")
            return False
            
    except Exception as e:
        print("✗ Test failed: {}".format(str(e)))
        return False

def test_use_case_5_high_risk_resources():
    """
    Use Case 5: Security team needs to identify high-risk non-compliant resources
    """
    print("\n=== Use Case 5: High-Risk Resource Identification ===")
    print("Scenario: Security team prioritizing remediation for critical resources")
    
    try:
        # Get scan results with high-risk analysis
        response = lambda_client.invoke(
            FunctionName='tag-compliance-checker',
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'scan'})
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            high_risk_count = len(body['summary']['high_risk_resources'])
            
            print("\n✓ High-risk analysis completed:")
            print("  - High-risk resources identified: {}".format(high_risk_count))
            print("  - Criteria: EC2/RDS/S3 resources missing critical tags")
            
            if high_risk_count > 0:
                print("\n  Sample high-risk resources:")
                for resource in body['summary']['high_risk_resources'][:3]:
                    print("    - Type: {}".format(resource['resource_type']))
                    print("      Missing: {}".format(', '.join(resource['missing_tags'])))
                    print("      ARN: {}...".format(resource['resource_arn'][:50]))
            
            return True
        else:
            print("✗ High-risk analysis failed")
            return False
            
    except Exception as e:
        print("✗ Test failed: {}".format(str(e)))
        return False

# Run all use case tests
print("\nRunning use case tests...")

results = {
    "Compliance Scan": test_use_case_1_compliance_scan(),
    "Cost Allocation": test_use_case_2_cost_allocation(),
    "Executive Report": test_use_case_3_compliance_report(),
    "Resource Check": test_use_case_4_specific_resource_check(),
    "High-Risk Analysis": test_use_case_5_high_risk_resources()
}

# Summary
print("\n" + "=" * 60)
print("USE CASE TEST SUMMARY")
print("=" * 60)

passed = sum(1 for result in results.values() if result)
total = len(results)

for test_name, result in results.items():
    status = "✓ PASSED" if result else "✗ FAILED"
    print("{}: {}".format(test_name, status))

print("\nTotal: {}/{} use cases passed".format(passed, total))

if passed == total:
    print("\n✓ All use cases passed! Tag compliance feature is working correctly.")
    sys.exit(0)
else:
    print("\n✗ Some use cases failed. Please check the errors above.")
    sys.exit(1)