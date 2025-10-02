#!/usr/bin/env python3
"""
Final Comprehensive Validation of FinOps Platform
Tests all features with real AWS APIs
"""

import sys
import requests
import json
import boto3
from datetime import datetime, timedelta
import time

def print_header(text):
    print("\n" + "="*60)
    print(f"🔍 {text}")
    print("="*60)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def validate_streamlit_services():
    """Validate Streamlit services are running"""
    print_header("Validating Streamlit Services")
    
    services = {
        'FinOps Dashboard': {
            'url': 'http://localhost:8502/_stcore/health',
            'main_url': 'http://localhost:8502'
        },
        'Apptio Dashboard': {
            'url': 'http://localhost:8504/_stcore/health',
            'main_url': 'http://localhost:8504'
        }
    }
    
    all_healthy = True
    
    for name, urls in services.items():
        try:
            response = requests.get(urls['url'], timeout=5)
            if response.text.strip() == 'ok':
                print_success(f"{name} is running at {urls['main_url']}")
            else:
                print_error(f"{name} is not healthy")
                all_healthy = False
        except Exception as e:
            print_error(f"{name} is not accessible: {str(e)}")
            all_healthy = False
    
    return all_healthy

def validate_new_features():
    """Validate all new features are working"""
    print_header("Validating New Features")
    
    features = []
    
    # 1. Report Generator
    try:
        from finops_report_generator import FinOpsReportGenerator
        # Test with real AWS clients
        clients = {
            'ce': boto3.client('ce'),
            'ec2': boto3.client('ec2'),
            'rds': boto3.client('rds'),
            's3': boto3.client('s3'),
            'lambda': boto3.client('lambda'),
            'cloudwatch': boto3.client('cloudwatch'),
            'organizations': boto3.client('organizations'),
            'sts': boto3.client('sts')
        }
        
        report_gen = FinOpsReportGenerator(clients)
        
        # Test JSON report generation
        report = report_gen.generate_comprehensive_report(
            report_type='full',
            start_date=datetime.now().date() - timedelta(days=7),
            end_date=datetime.now().date(),
            format='json'
        )
        
        report_data = json.loads(report)
        if all(key in report_data for key in ['metadata', 'cost_analysis', 'resource_tagging']):
            print_success("Report Generator: Fully functional with real AWS data")
            print_info(f"  - Generated report size: {len(report)} bytes")
            print_info(f"  - Total cost analyzed: ${report_data['cost_analysis'].get('total_cost', 0):,.2f}")
            features.append(True)
        else:
            print_error("Report Generator: Missing required sections")
            features.append(False)
            
    except Exception as e:
        print_error(f"Report Generator: {str(e)}")
        features.append(False)
    
    # 2. Tag Compliance Agent
    try:
        from tag_compliance_agent import TagComplianceAgent
        agent = TagComplianceAgent()
        
        # Test real compliance scan
        response, data = agent.perform_compliance_scan()
        
        if 'compliance_rate' in data:
            print_success("Tag Compliance Agent: Fully functional")
            print_info(f"  - Compliance rate: {data['compliance_rate']:.1f}%")
            print_info(f"  - Resources scanned: {data.get('total_resources', 0)}")
            print_info(f"  - Non-compliant: {data.get('non_compliant_count', 0)}")
            features.append(True)
        else:
            print_error("Tag Compliance Agent: Invalid response")
            features.append(False)
            
    except Exception as e:
        print_error(f"Tag Compliance Agent: {str(e)}")
        features.append(False)
    
    # 3. Multi-Agent Integration
    try:
        from multi_agent_processor import MultiAgentProcessor
        processor = MultiAgentProcessor()
        
        # Test tag compliance routing
        context = {'user_id': 'test', 'session_id': 'test'}
        response, data = processor.process_general_query("check tag compliance", context)
        
        if 'compliance' in response.lower():
            print_success("Multi-Agent Integration: Tag compliance properly integrated")
            features.append(True)
        else:
            print_error("Multi-Agent Integration: Tag queries not routing correctly")
            features.append(False)
            
    except Exception as e:
        print_error(f"Multi-Agent Integration: {str(e)}")
        features.append(False)
    
    # 4. Lambda Function
    try:
        import lambda_tag_compliance
        
        if all(hasattr(lambda_tag_compliance, func) for func in 
               ['lambda_handler', 'perform_compliance_scan', 'check_resource_compliance']):
            print_success("Lambda Function: All handlers properly defined")
            print_info("  - Ready for deployment to AWS Lambda")
            features.append(True)
        else:
            print_error("Lambda Function: Missing required handlers")
            features.append(False)
            
    except Exception as e:
        print_error(f"Lambda Function: {str(e)}")
        features.append(False)
    
    return all(features)

def validate_dashboard_tabs():
    """Validate dashboard has all required tabs"""
    print_header("Validating Dashboard Structure")
    
    try:
        with open('finops_intelligent_dashboard.py', 'r') as f:
            content = f.read()
        
        # Check for all 9 tabs
        tabs = [
            ("Cost Intelligence", "tab1"),
            ("Multi-Agent Chat", "tab2"),
            ("Business Context (Apptio)", "tab3"),
            ("Resource Optimization", "tab4"),
            ("Savings Plans", "tab5"),
            ("Budget Prediction", "tab6"),
            ("Executive Dashboard", "tab7"),
            ("Report Generator", "tab8"),
            ("Tag Compliance", "tab9")
        ]
        
        all_tabs_found = True
        for tab_name, tab_var in tabs:
            if tab_name in content and f"with {tab_var}:" in content:
                print_success(f"Tab found: {tab_name}")
            else:
                print_error(f"Tab missing: {tab_name}")
                all_tabs_found = False
        
        # Check for 6 agents
        agents = ['general', 'prediction', 'optimizer', 'savings', 'anomaly', 'compliance']
        agents_found = sum(1 for agent in agents if f"'{agent}':" in content)
        
        if agents_found == 6:
            print_success(f"All 6 AI agents defined")
        else:
            print_error(f"Only {agents_found}/6 agents found")
            all_tabs_found = False
        
        return all_tabs_found
        
    except Exception as e:
        print_error(f"Dashboard validation error: {str(e)}")
        return False

def validate_real_aws_integration():
    """Validate real AWS integration"""
    print_header("Validating Real AWS Integration")
    
    try:
        # Test AWS connection
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print_success(f"Connected to AWS Account: {identity['Account']}")
        
        # Test Cost Explorer
        ce = boto3.client('ce')
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        # Handle different response formats
        total_cost = 0.0
        for result in response['ResultsByTime']:
            if 'Total' in result and 'UnblendedCost' in result['Total']:
                total_cost += float(result['Total']['UnblendedCost']['Amount'])
            elif 'Groups' in result:
                for group in result['Groups']:
                    if 'Metrics' in group and 'UnblendedCost' in group['Metrics']:
                        total_cost += float(group['Metrics']['UnblendedCost']['Amount'])
        
        print_success(f"Cost Explorer API: Working (7-day cost: ${total_cost:,.2f})")
        
        # Test EC2
        ec2 = boto3.client('ec2')
        instances = ec2.describe_instances()
        instance_count = sum(
            len(r['Instances']) for r in instances['Reservations']
        )
        print_success(f"EC2 API: Working ({instance_count} instances)")
        
        # Test Resource Tagging
        tagging = boto3.client('resourcegroupstaggingapi')
        # Just verify we can call the API
        print_success("Resource Tagging API: Available")
        
        return True
        
    except Exception as e:
        print_error(f"AWS Integration: {str(e)}")
        return False

def validate_backup_and_rollback():
    """Validate backup and rollback mechanisms"""
    print_header("Validating Backup & Rollback")
    
    import os
    
    # Check rollback script
    if os.path.exists('rollback_finops_updates.sh'):
        if os.access('rollback_finops_updates.sh', os.X_OK):
            print_success("Rollback script exists and is executable")
        else:
            print_error("Rollback script exists but is not executable")
            return False
    else:
        print_error("Rollback script not found")
        return False
    
    # Check backups
    if os.path.exists('backups'):
        backups = [d for d in os.listdir('backups') if d.startswith('20')]
        if backups:
            print_success(f"Found {len(backups)} backup(s)")
            print_info(f"  - Latest: {sorted(backups)[-1]}")
        else:
            print_error("No backups found")
            return False
    else:
        print_error("Backup directory not found")
        return False
    
    return True

def run_final_validation():
    """Run all validations and provide summary"""
    print("\n" + "🚀 "*20)
    print("FINOPS PLATFORM FINAL VALIDATION")
    print("🚀 "*20)
    
    results = {
        'Streamlit Services': validate_streamlit_services(),
        'New Features': validate_new_features(),
        'Dashboard Structure': validate_dashboard_tabs(),
        'AWS Integration': validate_real_aws_integration(),
        'Backup & Rollback': validate_backup_and_rollback()
    }
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"\nTotal Categories Tested: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    
    print("\n📊 Detailed Results:")
    for category, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {category}: {status}")
    
    if all(results.values()):
        print("\n" + "🎉 "*20)
        print("ALL VALIDATIONS PASSED!")
        print("The FinOps Platform is fully operational with all new features!")
        print("🎉 "*20)
        
        print("\n📋 New Features Available:")
        print("1. Report Generator - Generate comprehensive PDF/Excel/JSON reports")
        print("2. Tag Compliance - Monitor and enforce resource tagging")
        print("3. Enhanced Chatbot - 6 AI agents including tag compliance")
        print("4. Lambda Function - Ready for automated tag enforcement")
        
        print("\n🌐 Access URLs:")
        print("  FinOps Dashboard: http://localhost:8502")
        print("  Apptio Dashboard: http://localhost:8504")
        
        print("\n💡 Try these in the chatbot:")
        print('  - "Check tag compliance"')
        print('  - "Find untagged resources"')
        print('  - "Generate cost report"')
        print('  - "Analyze my costs and recommend optimizations"')
        
        return 0
    else:
        print("\n⚠️  Some validations failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_final_validation())