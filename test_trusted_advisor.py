#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to check AWS Trusted Advisor accessibility
"""
import boto3
import json
from botocore.exceptions import ClientError

def test_trusted_advisor_access():
    """Test if AWS Trusted Advisor is accessible"""
    print("Testing AWS Trusted Advisor access...")
    
    try:
        # Create Support client (only available in us-east-1)
        support_client = boto3.client('support', region_name='us-east-1')
        print("[OK] Successfully created Support API client")
        
        # Try to describe available Trusted Advisor checks
        print("\nAttempting to call describe_trusted_advisor_checks...")
        response = support_client.describe_trusted_advisor_checks(language='en')
        
        # If successful, show available checks
        checks = response.get('checks', [])
        print(f"\n[OK] Trusted Advisor is ACCESSIBLE!")
        print(f"Found {len(checks)} available checks")
        
        # Show a few example checks
        print("\nExample available checks:")
        for i, check in enumerate(checks[:5]):
            print(f"  {i+1}. {check['name']} (ID: {check['id']})")
        
        if len(checks) > 5:
            print(f"  ... and {len(checks) - 5} more checks")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"\n[FAIL] Trusted Advisor is NOT accessible")
        print(f"Error Code: {error_code}")
        print(f"Error Message: {error_message}")
        
        if error_code == 'SubscriptionRequiredException':
            print("\nExplanation: AWS Trusted Advisor requires a Business or Enterprise support plan.")
            print("The current AWS account does not have the required support plan.")
            print("\nRecommendation: Continue using direct API calls for cost optimization.")
        elif error_code == 'UnauthorizedOperation':
            print("\nExplanation: The IAM user/role lacks permissions to access the Support API.")
            print("Required permission: support:DescribeTrustedAdvisorChecks")
        
        return False
        
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AWS Trusted Advisor Access Test")
    print("=" * 60)
    
    # Test access
    has_access = test_trusted_advisor_access()
    
    print("\n" + "=" * 60)
    print("Test Result Summary")
    print("=" * 60)
    
    if has_access:
        print("[OK] AWS Trusted Advisor IS available for this account")
        print("  - Can use Trusted Advisor checks for cost optimization")
        print("  - Can access security, performance, and fault tolerance recommendations")
    else:
        print("[FAIL] AWS Trusted Advisor is NOT available for this account")
        print("  - Will need to use direct API calls for cost analysis")
        print("  - Consider upgrading to Business/Enterprise support plan for Trusted Advisor access")
    
    print("=" * 60)