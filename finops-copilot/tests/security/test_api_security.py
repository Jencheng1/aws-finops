import unittest
import requests
import json
import os
import sys
import time
import re
from datetime import datetime

class FinOpsCopilotAPISecurityTester(unittest.TestCase):
    """Security tests for the FinOps Copilot API."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests."""
        # Get the API endpoint from environment variable or use default
        cls.api_endpoint = os.environ.get('FINOPS_COPILOT_API_ENDPOINT', 'http://localhost:8080')
        
        # Set up API authentication
        cls.api_key = os.environ.get('FINOPS_COPILOT_API_KEY', 'test-api-key')
        cls.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {cls.api_key}'
        }
        
        # Define the endpoints to test
        cls.endpoints = [
            {'name': 'Health Check', 'path': '/health', 'method': 'GET', 'auth_required': False},
            {'name': 'Cost Data', 'path': '/costs', 'method': 'GET', 'auth_required': True},
            {'name': 'Cost Breakdown', 'path': '/costs/breakdown', 'method': 'GET', 'auth_required': True},
            {'name': 'Cost Trend', 'path': '/costs/trends', 'method': 'GET', 'auth_required': True},
            {'name': 'Recommendations', 'path': '/recommendations', 'method': 'GET', 'auth_required': True},
            {'name': 'Tagging Compliance', 'path': '/tagging/compliance', 'method': 'GET', 'auth_required': True},
            {'name': 'Cost Forecast', 'path': '/costs/forecast', 'method': 'GET', 'auth_required': True}
        ]
        
        # Create report directory if it doesn't exist
        cls.report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
        os.makedirs(cls.report_dir, exist_ok=True)
        
        # Generate timestamp for the report
        cls.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Initialize the report
        cls.report = {
            'api_endpoint': cls.api_endpoint,
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'warnings': 0,
                'critical_issues': 0
            }
        }

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures that are used for all tests."""
        # Generate the report
        cls._generate_report()

    @classmethod
    def _generate_report(cls):
        """Generate a security test report."""
        # Update summary
        cls.report['summary']['total_tests'] = len(cls.report['tests'])
        cls.report['summary']['passed_tests'] = sum(1 for test in cls.report['tests'].values() if test['status'] == 'PASS')
        cls.report['summary']['failed_tests'] = sum(1 for test in cls.report['tests'].values() if test['status'] == 'FAIL')
        cls.report['summary']['warnings'] = sum(1 for test in cls.report['tests'].values() if test['severity'] == 'WARNING')
        cls.report['summary']['critical_issues'] = sum(1 for test in cls.report['tests'].values() if test['severity'] == 'CRITICAL')
        
        # Generate JSON report
        json_report_path = os.path.join(cls.report_dir, f'security_report_{cls.timestamp}.json')
        with open(json_report_path, 'w') as f:
            json.dump(cls.report, f, indent=2)
        
        # Generate HTML report
        html_report_path = os.path.join(cls.report_dir, f'security_report_{cls.timestamp}.html')
        cls._generate_html_report(html_report_path)
        
        print(f"JSON report generated: {json_report_path}")
        print(f"HTML report generated: {html_report_path}")

    @classmethod
    def _generate_html_report(cls, file_path):
        """Generate an HTML security test report."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FinOps Copilot API Security Test Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                }
                h1, h2, h3 {
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
                .warning {
                    color: orange;
                    font-weight: bold;
                }
                .critical {
                    color: red;
                    font-weight: bold;
                }
                .recommendations {
                    margin-top: 30px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-left: 5px solid #007bff;
                }
            </style>
        </head>
        <body>
            <h1>FinOps Copilot API Security Test Report</h1>
            <div class="summary">
                <h2>Test Summary</h2>
                <p><strong>API Endpoint:</strong> {api_endpoint}</p>
                <p><strong>Test Date:</strong> {test_date}</p>
                <p><strong>Total Tests:</strong> {total_tests}</p>
                <p><strong>Passed Tests:</strong> <span class="pass">{passed_tests}</span></p>
                <p><strong>Failed Tests:</strong> <span class="fail">{failed_tests}</span></p>
                <p><strong>Warnings:</strong> <span class="warning">{warnings}</span></p>
                <p><strong>Critical Issues:</strong> <span class="critical">{critical_issues}</span></p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test ID</th>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Severity</th>
                    <th>Description</th>
                </tr>
        """.format(
            api_endpoint=cls.report['api_endpoint'],
            test_date=cls.report['test_date'],
            total_tests=cls.report['summary']['total_tests'],
            passed_tests=cls.report['summary']['passed_tests'],
            failed_tests=cls.report['summary']['failed_tests'],
            warnings=cls.report['summary']['warnings'],
            critical_issues=cls.report['summary']['critical_issues']
        )
        
        for test_id, test in cls.report['tests'].items():
            status_class = "pass" if test['status'] == 'PASS' else "fail"
            severity_class = "warning" if test['severity'] == 'WARNING' else "critical" if test['severity'] == 'CRITICAL' else ""
            
            html += """
                <tr>
                    <td>{test_id}</td>
                    <td>{test_name}</td>
                    <td class="{status_class}">{status}</td>
                    <td class="{severity_class}">{severity}</td>
                    <td>{description}</td>
                </tr>
            """.format(
                test_id=test_id,
                test_name=test['name'],
                status_class=status_class,
                status=test['status'],
                severity_class=severity_class,
                severity=test['severity'],
                description=test['description']
            )
        
        html += """
            </table>
            
            <div class="recommendations">
                <h2>Security Recommendations</h2>
                <ul>
        """
        
        # Add recommendations based on test results
        critical_issues = [test for test_id, test in cls.report['tests'].items() if test['status'] == 'FAIL' and test['severity'] == 'CRITICAL']
        warnings = [test for test_id, test in cls.report['tests'].items() if test['status'] == 'FAIL' and test['severity'] == 'WARNING']
        
        for issue in critical_issues:
            html += f"<li><strong class='critical'>CRITICAL:</strong> {issue['recommendation']}</li>"
        
        for issue in warnings:
            html += f"<li><strong class='warning'>WARNING:</strong> {issue['recommendation']}</li>"
        
        if not critical_issues and not warnings:
            html += "<li>No security issues found. Continue to monitor and regularly test the API security.</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        with open(file_path, 'w') as f:
            f.write(html)

    def _add_test_result(self, test_id, name, status, severity, description, recommendation=None):
        """Add a test result to the report."""
        self.report['tests'][test_id] = {
            'name': name,
            'status': status,
            'severity': severity,
            'description': description,
            'recommendation': recommendation or description
        }

    def test_01_authentication_required(self):
        """Test that authentication is required for protected endpoints."""
        test_id = 'SEC-AUTH-001'
        name = 'Authentication Required'
        
        # Test each endpoint that requires authentication
        auth_required_endpoints = [endpoint for endpoint in self.endpoints if endpoint['auth_required']]
        failures = []
        
        for endpoint in auth_required_endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            
            # Make request without authentication
            response = requests.get(url, headers={'Content-Type': 'application/json'})
            
            # Check if the request was rejected
            if response.status_code == 200:
                failures.append(endpoint['name'])
        
        if failures:
            status = 'FAIL'
            severity = 'CRITICAL'
            description = f"The following endpoints do not require authentication: {', '.join(failures)}"
            recommendation = "Implement authentication for all protected endpoints to prevent unauthorized access."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "All protected endpoints require authentication."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # Assert for unittest
        self.assertEqual(len(failures), 0, f"Authentication not required for: {', '.join(failures)}")

    def test_02_invalid_token_rejected(self):
        """Test that invalid authentication tokens are rejected."""
        test_id = 'SEC-AUTH-002'
        name = 'Invalid Token Rejected'
        
        # Test each endpoint that requires authentication
        auth_required_endpoints = [endpoint for endpoint in self.endpoints if endpoint['auth_required']]
        failures = []
        
        for endpoint in auth_required_endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            
            # Make request with invalid authentication
            invalid_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer invalid-token'
            }
            response = requests.get(url, headers=invalid_headers)
            
            # Check if the request was rejected
            if response.status_code == 200:
                failures.append(endpoint['name'])
        
        if failures:
            status = 'FAIL'
            severity = 'CRITICAL'
            description = f"The following endpoints accept invalid tokens: {', '.join(failures)}"
            recommendation = "Ensure all protected endpoints properly validate authentication tokens."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "All protected endpoints reject invalid authentication tokens."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # Assert for unittest
        self.assertEqual(len(failures), 0, f"Invalid tokens accepted for: {', '.join(failures)}")

    def test_03_sql_injection(self):
        """Test for SQL injection vulnerabilities."""
        test_id = 'SEC-INJ-001'
        name = 'SQL Injection Protection'
        
        # SQL injection payloads to test
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users; --",
            "1' OR '1' = '1",
            "1 OR 1=1"
        ]
        
        # Test each endpoint with SQL injection payloads
        failures = []
        
        for endpoint in self.endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            headers = self.headers if endpoint['auth_required'] else {'Content-Type': 'application/json'}
            
            for payload in sql_payloads:
                # Try to inject in query parameters
                params = {'q': payload, 'filter': payload, 'search': payload}
                response = requests.get(url, headers=headers, params=params)
                
                # Check for signs of SQL injection vulnerability
                if response.status_code == 500 or 'SQL syntax' in response.text or 'database error' in response.text.lower():
                    failures.append(f"{endpoint['name']} (query parameter)")
                    break
                
                # If endpoint supports POST, try to inject in body
                if endpoint['method'] == 'POST':
                    data = {'query': payload, 'filter': payload, 'search': payload}
                    response = requests.post(url, headers=headers, json=data)
                    
                    # Check for signs of SQL injection vulnerability
                    if response.status_code == 500 or 'SQL syntax' in response.text or 'database error' in response.text.lower():
                        failures.append(f"{endpoint['name']} (body)")
                        break
        
        if failures:
            status = 'FAIL'
            severity = 'CRITICAL'
            description = f"Potential SQL injection vulnerabilities found in: {', '.join(failures)}"
            recommendation = "Implement proper input validation and parameterized queries to prevent SQL injection attacks."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "No SQL injection vulnerabilities detected."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # Assert for unittest
        self.assertEqual(len(failures), 0, f"SQL injection vulnerabilities found in: {', '.join(failures)}")

    def test_04_xss_protection(self):
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        test_id = 'SEC-XSS-001'
        name = 'Cross-Site Scripting Protection'
        
        # XSS payloads to test
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(\"XSS\")'>",
            "<body onload='alert(\"XSS\")'>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>"
        ]
        
        # Test each endpoint with XSS payloads
        failures = []
        
        for endpoint in self.endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            headers = self.headers if endpoint['auth_required'] else {'Content-Type': 'application/json'}
            
            for payload in xss_payloads:
                # Try to inject in query parameters
                params = {'q': payload, 'filter': payload, 'search': payload}
                response = requests.get(url, headers=headers, params=params)
                
                # Check if the payload is reflected in the response
                if payload in response.text:
                    failures.append(f"{endpoint['name']} (query parameter)")
                    break
                
                # If endpoint supports POST, try to inject in body
                if endpoint['method'] == 'POST':
                    data = {'query': payload, 'filter': payload, 'search': payload}
                    response = requests.post(url, headers=headers, json=data)
                    
                    # Check if the payload is reflected in the response
                    if payload in response.text:
                        failures.append(f"{endpoint['name']} (body)")
                        break
        
        if failures:
            status = 'FAIL'
            severity = 'CRITICAL'
            description = f"Potential XSS vulnerabilities found in: {', '.join(failures)}"
            recommendation = "Implement proper output encoding and Content Security Policy (CSP) to prevent XSS attacks."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "No XSS vulnerabilities detected."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # Assert for unittest
        self.assertEqual(len(failures), 0, f"XSS vulnerabilities found in: {', '.join(failures)}")

    def test_05_rate_limiting(self):
        """Test for rate limiting protection."""
        test_id = 'SEC-RATE-001'
        name = 'Rate Limiting Protection'
        
        # Test each endpoint with multiple rapid requests
        failures = []
        
        for endpoint in self.endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            headers = self.headers if endpoint['auth_required'] else {'Content-Type': 'application/json'}
            
            # Send 20 requests in quick succession
            responses = []
            for _ in range(20):
                response = requests.get(url, headers=headers)
                responses.append(response)
            
            # Check if any requests were rate limited
            rate_limited = any(response.status_code == 429 for response in responses)
            
            if not rate_limited:
                failures.append(endpoint['name'])
        
        if failures:
            status = 'FAIL'
            severity = 'WARNING'
            description = f"The following endpoints do not have rate limiting: {', '.join(failures)}"
            recommendation = "Implement rate limiting to prevent abuse and denial of service attacks."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "All endpoints have rate limiting protection."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # This is a warning, not a critical failure, so we don't assert

    def test_06_secure_headers(self):
        """Test for secure HTTP headers."""
        test_id = 'SEC-HEAD-001'
        name = 'Secure HTTP Headers'
        
        # Required security headers
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'Content-Security-Policy': None,  # Any value is acceptable
            'Strict-Transport-Security': None,  # Any value is acceptable
            'X-XSS-Protection': '1; mode=block'
        }
        
        # Test the API for secure headers
        url = f"{self.api_endpoint}/health"  # Use a public endpoint
        response = requests.get(url)
        
        missing_headers = []
        incorrect_headers = []
        
        for header, expected_value in required_headers.items():
            if header not in response.headers:
                missing_headers.append(header)
            elif expected_value is not None:
                if isinstance(expected_value, list):
                    if response.headers[header] not in expected_value:
                        incorrect_headers.append(f"{header} (expected one of {expected_value}, got {response.headers[header]})")
                elif response.headers[header] != expected_value:
                    incorrect_headers.append(f"{header} (expected {expected_value}, got {response.headers[header]})")
        
        if missing_headers or incorrect_headers:
            status = 'FAIL'
            severity = 'WARNING'
            description = ""
            
            if missing_headers:
                description += f"Missing security headers: {', '.join(missing_headers)}. "
            
            if incorrect_headers:
                description += f"Incorrect security headers: {', '.join(incorrect_headers)}."
            
            recommendation = "Implement all recommended security headers to protect against common web vulnerabilities."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "All required security headers are present and correctly configured."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # This is a warning, not a critical failure, so we don't assert

    def test_07_ssl_tls_configuration(self):
        """Test for secure SSL/TLS configuration."""
        test_id = 'SEC-SSL-001'
        name = 'SSL/TLS Configuration'
        
        # Skip this test for localhost
        if 'localhost' in self.api_endpoint or '127.0.0.1' in self.api_endpoint:
            self._add_test_result(
                test_id, 
                name, 
                'SKIP', 
                'NONE', 
                "Test skipped for localhost.",
                "Ensure proper SSL/TLS configuration in production environment."
            )
            return
        
        # Check if the API uses HTTPS
        if not self.api_endpoint.startswith('https://'):
            status = 'FAIL'
            severity = 'CRITICAL'
            description = "The API does not use HTTPS."
            recommendation = "Configure the API to use HTTPS to encrypt data in transit."
            
            self._add_test_result(test_id, name, status, severity, description, recommendation)
            
            # Assert for unittest
            self.assertTrue(self.api_endpoint.startswith('https://'), "API does not use HTTPS")
            return
        
        # Test for secure SSL/TLS configuration
        try:
            response = requests.get(f"{self.api_endpoint}/health", verify=True)
            
            # Check for HSTS header
            if 'Strict-Transport-Security' not in response.headers:
                status = 'FAIL'
                severity = 'WARNING'
                description = "HTTPS is enabled, but HSTS header is missing."
                recommendation = "Implement HTTP Strict Transport Security (HSTS) to prevent downgrade attacks."
            else:
                status = 'PASS'
                severity = 'NONE'
                description = "HTTPS is enabled with proper configuration."
                recommendation = None
        except requests.exceptions.SSLError:
            status = 'FAIL'
            severity = 'CRITICAL'
            description = "SSL/TLS certificate validation failed."
            recommendation = "Ensure the API has a valid SSL/TLS certificate from a trusted certificate authority."
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # Assert for unittest if critical
        if severity == 'CRITICAL':
            self.fail(description)

    def test_08_cors_configuration(self):
        """Test for secure CORS configuration."""
        test_id = 'SEC-CORS-001'
        name = 'CORS Configuration'
        
        # Test the API for CORS headers
        url = f"{self.api_endpoint}/health"  # Use a public endpoint
        headers = {'Origin': 'https://example.com'}
        response = requests.options(url, headers=headers)
        
        # Check if CORS is enabled
        if 'Access-Control-Allow-Origin' in response.headers:
            # Check if CORS is too permissive
            if response.headers['Access-Control-Allow-Origin'] == '*':
                status = 'FAIL'
                severity = 'WARNING'
                description = "CORS is configured with a wildcard origin (*), which is too permissive."
                recommendation = "Configure CORS with specific allowed origins instead of using a wildcard."
            else:
                status = 'PASS'
                severity = 'NONE'
                description = "CORS is properly configured with specific allowed origins."
                recommendation = None
        else:
            # CORS not enabled, which is fine if the API is not meant to be accessed from browsers
            status = 'PASS'
            severity = 'NONE'
            description = "CORS is not enabled, which is appropriate if the API is not meant to be accessed directly from browsers."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # This is a warning, not a critical failure, so we don't assert

    def test_09_information_disclosure(self):
        """Test for information disclosure in error messages."""
        test_id = 'SEC-INFO-001'
        name = 'Information Disclosure'
        
        # Test each endpoint with invalid parameters
        failures = []
        
        for endpoint in self.endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            headers = self.headers if endpoint['auth_required'] else {'Content-Type': 'application/json'}
            
            # Send request with invalid parameters
            params = {'invalid_param': 'test', 'error': 'true'}
            response = requests.get(url, headers=headers, params=params)
            
            # Check for sensitive information in error messages
            sensitive_patterns = [
                r'stack trace',
                r'at [\w\.]+\([\w\.]+:\d+\)',  # Java/Node.js stack trace
                r'File "[\w/\.]+", line \d+',  # Python stack trace
                r'(SELECT|INSERT|UPDATE|DELETE).*FROM',  # SQL query
                r'(Exception|Error): .*',  # Exception details
                r'(username|password|secret|key|token)=[\w\-]+',  # Credentials
                r'(mongodb|mysql|postgresql|redis)://[\w\-\.]+',  # Database connection strings
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP addresses
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, response.text, re.IGNORECASE):
                    failures.append(endpoint['name'])
                    break
        
        if failures:
            status = 'FAIL'
            severity = 'WARNING'
            description = f"The following endpoints may leak sensitive information in error messages: {', '.join(failures)}"
            recommendation = "Implement proper error handling to prevent leaking sensitive information in error messages."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "No sensitive information disclosure detected in error messages."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # This is a warning, not a critical failure, so we don't assert

    def test_10_http_methods(self):
        """Test for unnecessary HTTP methods."""
        test_id = 'SEC-METH-001'
        name = 'HTTP Methods'
        
        # Test each endpoint with different HTTP methods
        failures = []
        
        for endpoint in self.endpoints:
            url = f"{self.api_endpoint}{endpoint['path']}"
            headers = self.headers if endpoint['auth_required'] else {'Content-Type': 'application/json'}
            
            # Test methods that should be rejected
            methods_to_test = ['PUT', 'DELETE', 'PATCH', 'TRACE']
            
            for method in methods_to_test:
                response = requests.request(method, url, headers=headers)
                
                # Check if the method is allowed (should return 405 Method Not Allowed)
                if response.status_code != 405:
                    failures.append(f"{endpoint['name']} ({method})")
        
        if failures:
            status = 'FAIL'
            severity = 'WARNING'
            description = f"The following endpoints allow unnecessary HTTP methods: {', '.join(failures)}"
            recommendation = "Disable unnecessary HTTP methods to reduce the attack surface."
        else:
            status = 'PASS'
            severity = 'NONE'
            description = "All endpoints properly restrict HTTP methods."
            recommendation = None
        
        self._add_test_result(test_id, name, status, severity, description, recommendation)
        
        # This is a warning, not a critical failure, so we don't assert

if __name__ == '__main__':
    unittest.main()
