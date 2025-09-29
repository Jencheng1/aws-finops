#!/usr/bin/env python3
"""
Run all FinOps Copilot tests with real AWS APIs
"""

import subprocess
import sys
import time
from datetime import datetime

def run_test_file(test_file, description):
    """Run a test file and return success status"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
    end_time = time.time()
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    duration = end_time - start_time
    print(f"\nTest duration: {duration:.2f} seconds")
    
    return result.returncode == 0

def main():
    """Run all test suites"""
    print(f"FinOps Copilot - Complete Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    test_suites = [
        ("tests/test_real_aws.py", "Real AWS Integration Tests"),
        ("tests/test_apptio_real.py", "Apptio Integration Tests"),
        ("tests/unit/test_s3_agent.py", "S3 Agent Unit Tests"),
        ("tests/test_cost_explorer_mcp_real.py", "Cost Explorer MCP Tests"),
    ]
    
    results = []
    total_start = time.time()
    
    for test_file, description in test_suites:
        success = run_test_file(test_file, description)
        results.append((description, success))
    
    total_duration = time.time() - total_start
    
    # Print final summary
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description}: {status}")
        if not success:
            all_passed = False
    
    print(f"\nTotal test duration: {total_duration:.2f} seconds")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())