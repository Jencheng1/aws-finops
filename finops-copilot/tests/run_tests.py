#!/usr/bin/env python3

import os
import sys
import argparse
import unittest
import time
import json
from datetime import datetime

def run_unit_tests():
    """Run all unit tests."""
    print("Running unit tests...")
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run all integration tests."""
    print("Running integration tests...")
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integration')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_e2e_tests():
    """Run all end-to-end tests."""
    print("Running end-to-end tests...")
    
    # Discover and run e2e tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e2e')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_performance_tests():
    """Run all performance tests."""
    print("Running performance tests...")
    
    # Import and run the performance tester
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'performance'))
    from test_api_performance import FinOpsCopilotAPIPerformanceTester
    
    # Create and run the performance tester
    tester = FinOpsCopilotAPIPerformanceTester()
    tester.run_tests()
    tester.generate_report()
    
    return True  # Performance tests don't have pass/fail criteria

def run_security_tests():
    """Run all security tests."""
    print("Running security tests...")
    
    # Discover and run security tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'security')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def generate_report(results):
    """Generate a test report."""
    # Create report directory if it doesn't exist
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate JSON report
    json_report_path = os.path.join(report_dir, f'test_report_{timestamp}.json')
    with open(json_report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate HTML report
    html_report_path = os.path.join(report_dir, f'test_report_{timestamp}.html')
    generate_html_report(html_report_path, results)
    
    print(f"JSON report generated: {json_report_path}")
    print(f"HTML report generated: {html_report_path}")

def generate_html_report(file_path, results):
    """Generate an HTML test report."""
    # Calculate overall success
    all_success = all(results[test_type]['success'] for test_type in results if test_type != 'timestamp')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FinOps Copilot Test Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1, h2 {
                color: #333;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .summary {
                margin-bottom: 30px;
            }
            .pass {
                color: green;
                font-weight: bold;
            }
            .fail {
                color: red;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>FinOps Copilot Test Report</h1>
        <div class="summary">
            <h2>Test Summary</h2>
            <p><strong>Test Date:</strong> {timestamp}</p>
            <p><strong>Overall Result:</strong> <span class="{overall_class}">{overall_result}</span></p>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test Type</th>
                <th>Result</th>
                <th>Duration</th>
                <th>Details</th>
            </tr>
    """.format(
        timestamp=results['timestamp'],
        overall_class="pass" if all_success else "fail",
        overall_result="PASS" if all_success else "FAIL"
    )
    
    for test_type, test_results in results.items():
        if test_type == 'timestamp':
            continue
        
        result_class = "pass" if test_results['success'] else "fail"
        result_text = "PASS" if test_results['success'] else "FAIL"
        
        html += """
            <tr>
                <td>{test_type}</td>
                <td class="{result_class}">{result_text}</td>
                <td>{duration:.2f} seconds</td>
                <td>{details}</td>
            </tr>
        """.format(
            test_type=test_type,
            result_class=result_class,
            result_text=result_text,
            duration=test_results['duration'],
            details=test_results.get('details', '')
        )
    
    html += """
        </table>
    </body>
    </html>
    """
    
    with open(file_path, 'w') as f:
        f.write(html)

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Run FinOps Copilot tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--security', action='store_true', help='Run security tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # If no arguments are provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Initialize results dictionary
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Run unit tests
    if args.unit or args.all:
        start_time = time.time()
        unit_success = run_unit_tests()
        end_time = time.time()
        results['unit'] = {
            'success': unit_success,
            'duration': end_time - start_time
        }
    
    # Run integration tests
    if args.integration or args.all:
        start_time = time.time()
        integration_success = run_integration_tests()
        end_time = time.time()
        results['integration'] = {
            'success': integration_success,
            'duration': end_time - start_time
        }
    
    # Run end-to-end tests
    if args.e2e or args.all:
        start_time = time.time()
        e2e_success = run_e2e_tests()
        end_time = time.time()
        results['e2e'] = {
            'success': e2e_success,
            'duration': end_time - start_time
        }
    
    # Run performance tests
    if args.performance or args.all:
        start_time = time.time()
        performance_success = run_performance_tests()
        end_time = time.time()
        results['performance'] = {
            'success': performance_success,
            'duration': end_time - start_time
        }
    
    # Run security tests
    if args.security or args.all:
        start_time = time.time()
        security_success = run_security_tests()
        end_time = time.time()
        results['security'] = {
            'success': security_success,
            'duration': end_time - start_time
        }
    
    # Generate report
    generate_report(results)
    
    # Return success status
    return all(results[test_type]['success'] for test_type in results if test_type != 'timestamp')

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
