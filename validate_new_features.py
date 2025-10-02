#!/usr/bin/env python3
"""
Validate new FinOps features
"""

import requests
import json
import time

def check_streamlit_health():
    """Check if Streamlit apps are running"""
    services = {
        'FinOps Dashboard': 'http://localhost:8502/_stcore/health',
        'Apptio Dashboard': 'http://localhost:8504/_stcore/health'
    }
    
    print("🔍 Checking Streamlit Services Health...")
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.text.strip() == 'ok':
                print(f"✅ {name}: Running")
            else:
                print(f"❌ {name}: Not healthy")
        except Exception as e:
            print(f"❌ {name}: Not accessible - {str(e)}")
    print()

def validate_features():
    """Validate new features are available"""
    print("📋 Validating New Features...")
    
    # Check if modules can be imported
    features_status = []
    
    # 1. Report Generator
    try:
        import finops_report_generator
        features_status.append(("Report Generator Module", True, "Module imports successfully"))
    except Exception as e:
        features_status.append(("Report Generator Module", False, str(e)))
    
    # 2. Tag Compliance Agent
    try:
        from tag_compliance_agent import TagComplianceAgent
        agent = TagComplianceAgent()
        features_status.append(("Tag Compliance Agent", True, "Agent initialized successfully"))
    except Exception as e:
        features_status.append(("Tag Compliance Agent", False, str(e)))
    
    # 3. Lambda Function
    try:
        import lambda_tag_compliance
        features_status.append(("Lambda Tag Compliance", True, "Lambda module imports successfully"))
    except Exception as e:
        features_status.append(("Lambda Tag Compliance", False, str(e)))
    
    # 4. Multi-Agent Integration
    try:
        from multi_agent_processor import MultiAgentProcessor
        processor = MultiAgentProcessor()
        has_tag_agent = hasattr(processor, 'tag_compliance_agent')
        if has_tag_agent:
            features_status.append(("Multi-Agent Integration", True, "Tag compliance agent integrated"))
        else:
            features_status.append(("Multi-Agent Integration", False, "Tag compliance agent not found"))
    except Exception as e:
        features_status.append(("Multi-Agent Integration", False, str(e)))
    
    # 5. Test Suite
    try:
        import test_finops_features
        features_status.append(("Test Suite", True, "Test module imports successfully"))
    except Exception as e:
        features_status.append(("Test Suite", False, str(e)))
    
    # Display results
    for feature, status, message in features_status:
        if status:
            print(f"✅ {feature}: {message}")
        else:
            print(f"❌ {feature}: {message}")
    
    print()
    return all(status for _, status, _ in features_status)

def check_aws_resources():
    """Check AWS resources and permissions"""
    print("🔍 Checking AWS Resources...")
    
    try:
        import boto3
        
        # Check AWS credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ AWS User/Role: {identity['Arn']}")
        
        # Check key services
        services_to_check = ['ec2', 'ce', 'rds', 's3', 'lambda']
        for service in services_to_check:
            try:
                client = boto3.client(service)
                print(f"✅ {service.upper()} client: Available")
            except Exception as e:
                print(f"❌ {service.upper()} client: {str(e)}")
    
    except Exception as e:
        print(f"❌ AWS SDK Error: {str(e)}")
    
    print()

def main():
    """Run all validations"""
    print("="*50)
    print("🚀 FinOps Platform Validation")
    print("="*50)
    print()
    
    # 1. Check Streamlit services
    check_streamlit_health()
    
    # 2. Validate new features
    features_ok = validate_features()
    
    # 3. Check AWS resources
    check_aws_resources()
    
    # Summary
    print("="*50)
    print("📊 Validation Summary")
    print("="*50)
    
    if features_ok:
        print("✅ All new features are properly installed")
        print("\n🎯 Next Steps:")
        print("1. Access FinOps Dashboard: http://localhost:8502")
        print("2. Navigate to 'Report Generator' tab")
        print("3. Navigate to 'Tag Compliance' tab")
        print("4. Test the multi-agent chatbot with tag compliance queries")
        print("\n💡 Example queries to test:")
        print("- 'Check tag compliance'")
        print("- 'Find untagged resources'")
        print("- 'Generate cost report'")
    else:
        print("❌ Some features have issues - check the errors above")
        print("\n🔧 Troubleshooting:")
        print("- Check Python version (should be 3.7+)")
        print("- Install missing dependencies: pip3 install reportlab xlsxwriter matplotlib")
        print("- Review error messages for specific issues")

if __name__ == '__main__':
    main()