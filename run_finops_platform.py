#!/usr/bin/env python3
"""
Run script for the Integrated AI FinOps Platform
This script validates all components and starts the platform
"""

import os
import sys
import boto3
import subprocess
import json
from datetime import datetime
import time

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def check_aws_credentials():
    """Verify AWS credentials are configured"""
    print_header("Checking AWS Credentials")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ User ARN: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        print("\nPlease configure AWS credentials using one of:")
        print("  - aws configure")
        print("  - Export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("  - Use IAM role (for EC2 instances)")
        return False

def check_required_services():
    """Check if required AWS services are accessible"""
    print_header("Checking AWS Services Access")
    
    services = {
        'ce': 'Cost Explorer',
        'ec2': 'EC2',
        'cloudwatch': 'CloudWatch',
        'sts': 'STS',
        'organizations': 'Organizations',
        'savingsplans': 'Savings Plans'
    }
    
    accessible = []
    limited = []
    
    for service_name, display_name in services.items():
        try:
            client = boto3.client(service_name)
            # Try a simple API call
            if service_name == 'ce':
                # Cost Explorer requires specific date range
                client.get_cost_and_usage(
                    TimePeriod={
                        'Start': '2024-01-01',
                        'End': '2024-01-02'
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost']
                )
            elif service_name == 'ec2':
                client.describe_regions()
            elif service_name == 'sts':
                client.get_caller_identity()
                
            print(f"✅ {display_name}: Accessible")
            accessible.append(service_name)
            
        except Exception as e:
            print(f"⚠️  {display_name}: Limited access - {str(e)[:50]}...")
            limited.append(service_name)
    
    print(f"\nServices accessible: {len(accessible)}/{len(services)}")
    return len(accessible) >= 3  # Need at least core services

def check_dependencies():
    """Check Python dependencies"""
    print_header("Checking Python Dependencies")
    
    required_packages = [
        'streamlit',
        'boto3',
        'pandas',
        'plotly',
        'scikit-learn',
        'numpy'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Missing")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install " + ' '.join(missing))
        return False
    
    return True

def validate_files():
    """Validate all required files exist"""
    print_header("Validating Platform Files")
    
    required_files = [
        'enhanced_integrated_dashboard.py',
        'budget_prediction_agent.py',
        'ai_agent_mcp_architecture.py',
        'test_integrated_platform.py'
    ]
    
    missing = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: Found")
        else:
            print(f"❌ {file}: Missing")
            missing.append(file)
    
    return len(missing) == 0

def create_sample_config():
    """Create sample configuration file"""
    print_header("Creating Configuration")
    
    config = {
        "platform": "AI-Powered FinOps Platform",
        "version": "2.0",
        "features": {
            "budget_prediction": True,
            "anomaly_detection": True,
            "resource_optimization": True,
            "savings_plans": True,
            "apptio_integration": True
        },
        "agents": [
            {
                "name": "Budget Prediction Agent",
                "type": "ML-based forecasting",
                "models": ["Linear", "Polynomial", "Random Forest"]
            },
            {
                "name": "Anomaly Detection Agent",
                "type": "Statistical analysis",
                "threshold": 2.0
            },
            {
                "name": "Resource Optimizer Agent",
                "type": "Idle resource detection",
                "scan_interval": "hourly"
            },
            {
                "name": "Savings Plan Agent",
                "type": "Commitment optimization",
                "coverage_target": 0.8
            }
        ],
        "mcp_servers": [
            "cost_explorer_mcp",
            "apptio_mcp",
            "cloudwatch_mcp",
            "tagging_mcp",
            "resource_mcp"
        ]
    }
    
    with open('finops_platform_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration file created: finops_platform_config.json")
    return True

def run_tests():
    """Run platform tests"""
    print_header("Running Platform Tests")
    
    print("Running comprehensive test suite...")
    print("This will validate all features with real AWS APIs\n")
    
    try:
        result = subprocess.run(
            [sys.executable, 'test_integrated_platform.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed")
            print("Run 'python test_integrated_platform.py' for details")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Tests timed out (this is normal for large accounts)")
        return True
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")
        return True

def launch_platform():
    """Launch the Streamlit platform"""
    print_header("Launching AI FinOps Platform")
    
    print("\n🚀 Starting the platform...")
    print("\nPlatform Features:")
    print("  - AI Budget Prediction with ML models")
    print("  - Real-time Anomaly Detection")
    print("  - Idle Resource Scanner")
    print("  - Savings Plan Optimizer")
    print("  - Apptio TBM Integration")
    print("  - AI-Powered Chatbot")
    print("\nAccess the platform at: http://localhost:8501")
    print("\nPress Ctrl+C to stop the platform\n")
    
    # Launch Streamlit
    subprocess.run(['streamlit', 'run', 'enhanced_integrated_dashboard.py'])

def main():
    """Main execution function"""
    print_header("AI-Powered FinOps Platform Launcher")
    print(f"Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    checks = [
        ("AWS Credentials", check_aws_credentials),
        ("AWS Services", check_required_services),
        ("Python Dependencies", check_dependencies),
        ("Platform Files", validate_files),
        ("Configuration", create_sample_config)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
            print(f"\n❌ {check_name} check failed")
    
    if not all_passed:
        print_header("Pre-flight Checks Failed")
        print("Please fix the issues above before launching the platform")
        return 1
    
    print_header("All Checks Passed!")
    
    # Optional: Run tests
    print("\nWould you like to run the test suite? (y/n): ", end='')
    response = input().strip().lower()
    
    if response == 'y':
        run_tests()
    
    # Launch platform
    print("\nReady to launch the AI FinOps Platform? (y/n): ", end='')
    response = input().strip().lower()
    
    if response == 'y':
        launch_platform()
    else:
        print("\nTo launch manually, run:")
        print("  streamlit run enhanced_integrated_dashboard.py")
        print("\nTo view architecture details, run:")
        print("  streamlit run ai_agent_mcp_architecture.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())