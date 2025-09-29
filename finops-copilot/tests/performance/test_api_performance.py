import os
import time
import json
import statistics
import matplotlib.pyplot as plt
import numpy as np
import requests
import concurrent.futures
from datetime import datetime

class FinOpsCopilotAPIPerformanceTester:
    """Performance tester for the FinOps Copilot API."""

    def __init__(self):
        """Initialize the performance tester."""
        # Get the API endpoint from environment variable or use default
        self.api_endpoint = os.environ.get('FINOPS_COPILOT_API_ENDPOINT', 'http://localhost:8080')
        
        # Set up API authentication
        self.api_key = os.environ.get('FINOPS_COPILOT_API_KEY', 'test-api-key')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Define the endpoints to test
        self.endpoints = [
            {'name': 'Health Check', 'path': '/health', 'method': 'GET', 'auth_required': False},
            {'name': 'Cost Data', 'path': '/costs', 'method': 'GET', 'auth_required': True},
            {'name': 'Cost Breakdown', 'path': '/costs/breakdown', 'method': 'GET', 'auth_required': True},
            {'name': 'Cost Trend', 'path': '/costs/trends', 'method': 'GET', 'auth_required': True},
            {'name': 'Recommendations', 'path': '/recommendations', 'method': 'GET', 'auth_required': True},
            {'name': 'Tagging Compliance', 'path': '/tagging/compliance', 'method': 'GET', 'auth_required': True},
            {'name': 'Cost Forecast', 'path': '/costs/forecast', 'method': 'GET', 'auth_required': True}
        ]
        
        # Define the test parameters
        self.num_requests = 50  # Number of requests per endpoint
        self.concurrency = 10   # Number of concurrent requests
        self.results = {}       # Dictionary to store test results

    def make_request(self, endpoint):
        """Make a request to the specified endpoint and measure the response time."""
        url = f"{self.api_endpoint}{endpoint['path']}"
        headers = self.headers if endpoint['auth_required'] else {'Content-Type': 'application/json'}
        
        start_time = time.time()
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(url, headers=headers)
            elif endpoint['method'] == 'POST':
                response = requests.post(url, headers=headers, json={})
            else:
                raise ValueError(f"Unsupported HTTP method: {endpoint['method']}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'status_code': response.status_code,
                'response_time': response_time
            }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'status_code': 0,
                'response_time': response_time,
                'error': str(e)
            }

    def run_test_for_endpoint(self, endpoint):
        """Run the performance test for a single endpoint."""
        print(f"Testing endpoint: {endpoint['name']} ({endpoint['path']})")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [executor.submit(self.make_request, endpoint) for _ in range(self.num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Calculate statistics
        response_times = [result['response_time'] for result in results]
        success_count = sum(1 for result in results if 200 <= result['status_code'] < 300)
        error_count = self.num_requests - success_count
        
        stats = {
            'min': min(response_times),
            'max': max(response_times),
            'mean': statistics.mean(response_times),
            'median': statistics.median(response_times),
            'p90': np.percentile(response_times, 90),
            'p95': np.percentile(response_times, 95),
            'p99': np.percentile(response_times, 99),
            'success_rate': (success_count / self.num_requests) * 100,
            'error_rate': (error_count / self.num_requests) * 100,
            'raw_results': results
        }
        
        print(f"  Min: {stats['min']:.2f} ms")
        print(f"  Max: {stats['max']:.2f} ms")
        print(f"  Mean: {stats['mean']:.2f} ms")
        print(f"  Median: {stats['median']:.2f} ms")
        print(f"  90th percentile: {stats['p90']:.2f} ms")
        print(f"  95th percentile: {stats['p95']:.2f} ms")
        print(f"  99th percentile: {stats['p99']:.2f} ms")
        print(f"  Success rate: {stats['success_rate']:.2f}%")
        print(f"  Error rate: {stats['error_rate']:.2f}%")
        print()
        
        return stats

    def run_tests(self):
        """Run performance tests for all endpoints."""
        print(f"Starting performance tests for {self.api_endpoint}")
        print(f"Number of requests per endpoint: {self.num_requests}")
        print(f"Concurrency level: {self.concurrency}")
        print()
        
        start_time = time.time()
        
        for endpoint in self.endpoints:
            self.results[endpoint['name']] = self.run_test_for_endpoint(endpoint)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"All tests completed in {total_time:.2f} seconds")
        
        return self.results

    def generate_report(self):
        """Generate a performance test report."""
        if not self.results:
            print("No test results available. Run tests first.")
            return
        
        # Create report directory if it doesn't exist
        report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate timestamp for the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate HTML report
        html_report_path = os.path.join(report_dir, f'performance_report_{timestamp}.html')
        self._generate_html_report(html_report_path)
        
        # Generate JSON report
        json_report_path = os.path.join(report_dir, f'performance_report_{timestamp}.json')
        self._generate_json_report(json_report_path)
        
        # Generate charts
        charts_dir = os.path.join(report_dir, f'charts_{timestamp}')
        os.makedirs(charts_dir, exist_ok=True)
        self._generate_charts(charts_dir)
        
        print(f"HTML report generated: {html_report_path}")
        print(f"JSON report generated: {json_report_path}")
        print(f"Charts generated in: {charts_dir}")

    def _generate_html_report(self, file_path):
        """Generate an HTML performance test report."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FinOps Copilot API Performance Test Report</title>
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
                .chart {
                    margin-bottom: 30px;
                }
            </style>
        </head>
        <body>
            <h1>FinOps Copilot API Performance Test Report</h1>
            <div class="summary">
                <h2>Test Summary</h2>
                <p><strong>API Endpoint:</strong> {api_endpoint}</p>
                <p><strong>Test Date:</strong> {test_date}</p>
                <p><strong>Requests per Endpoint:</strong> {num_requests}</p>
                <p><strong>Concurrency Level:</strong> {concurrency}</p>
            </div>
            
            <h2>Results by Endpoint</h2>
            <table>
                <tr>
                    <th>Endpoint</th>
                    <th>Min (ms)</th>
                    <th>Max (ms)</th>
                    <th>Mean (ms)</th>
                    <th>Median (ms)</th>
                    <th>90th %ile (ms)</th>
                    <th>95th %ile (ms)</th>
                    <th>99th %ile (ms)</th>
                    <th>Success Rate</th>
                </tr>
        """.format(
            api_endpoint=self.api_endpoint,
            test_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            num_requests=self.num_requests,
            concurrency=self.concurrency
        )
        
        for endpoint_name, stats in self.results.items():
            html += """
                <tr>
                    <td>{endpoint_name}</td>
                    <td>{min:.2f}</td>
                    <td>{max:.2f}</td>
                    <td>{mean:.2f}</td>
                    <td>{median:.2f}</td>
                    <td>{p90:.2f}</td>
                    <td>{p95:.2f}</td>
                    <td>{p99:.2f}</td>
                    <td>{success_rate:.2f}%</td>
                </tr>
            """.format(
                endpoint_name=endpoint_name,
                min=stats['min'],
                max=stats['max'],
                mean=stats['mean'],
                median=stats['median'],
                p90=stats['p90'],
                p95=stats['p95'],
                p99=stats['p99'],
                success_rate=stats['success_rate']
            )
        
        html += """
            </table>
            
            <h2>Recommendations</h2>
            <ul>
        """
        
        # Add recommendations based on test results
        slow_endpoints = []
        for endpoint_name, stats in self.results.items():
            if stats['p95'] > 1000:  # If 95th percentile is over 1000ms
                slow_endpoints.append((endpoint_name, stats['p95']))
        
        if slow_endpoints:
            html += "<li><strong>Optimize slow endpoints:</strong> The following endpoints have high response times (95th percentile):<ul>"
            for endpoint_name, p95 in sorted(slow_endpoints, key=lambda x: x[1], reverse=True):
                html += f"<li>{endpoint_name}: {p95:.2f} ms</li>"
            html += "</ul></li>"
        
        error_endpoints = []
        for endpoint_name, stats in self.results.items():
            if stats['error_rate'] > 0:
                error_endpoints.append((endpoint_name, stats['error_rate']))
        
        if error_endpoints:
            html += "<li><strong>Fix endpoints with errors:</strong> The following endpoints have errors:<ul>"
            for endpoint_name, error_rate in sorted(error_endpoints, key=lambda x: x[1], reverse=True):
                html += f"<li>{endpoint_name}: {error_rate:.2f}% error rate</li>"
            html += "</ul></li>"
        
        if not slow_endpoints and not error_endpoints:
            html += "<li>All endpoints are performing well.</li>"
        
        html += """
            </ul>
        </body>
        </html>
        """
        
        with open(file_path, 'w') as f:
            f.write(html)

    def _generate_json_report(self, file_path):
        """Generate a JSON performance test report."""
        report = {
            'api_endpoint': self.api_endpoint,
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'num_requests': self.num_requests,
            'concurrency': self.concurrency,
            'results': {}
        }
        
        for endpoint_name, stats in self.results.items():
            # Create a copy of stats without the raw_results to keep the JSON file smaller
            endpoint_stats = {k: v for k, v in stats.items() if k != 'raw_results'}
            report['results'][endpoint_name] = endpoint_stats
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)

    def _generate_charts(self, charts_dir):
        """Generate performance charts."""
        # Response time comparison chart
        self._generate_response_time_comparison_chart(charts_dir)
        
        # Response time distribution charts for each endpoint
        for endpoint_name, stats in self.results.items():
            self._generate_response_time_distribution_chart(endpoint_name, stats, charts_dir)
        
        # Success rate comparison chart
        self._generate_success_rate_chart(charts_dir)

    def _generate_response_time_comparison_chart(self, charts_dir):
        """Generate a chart comparing response times across endpoints."""
        plt.figure(figsize=(12, 8))
        
        endpoint_names = list(self.results.keys())
        means = [stats['mean'] for stats in self.results.values()]
        medians = [stats['median'] for stats in self.results.values()]
        p95s = [stats['p95'] for stats in self.results.values()]
        
        x = np.arange(len(endpoint_names))
        width = 0.25
        
        plt.bar(x - width, means, width, label='Mean')
        plt.bar(x, medians, width, label='Median')
        plt.bar(x + width, p95s, width, label='95th Percentile')
        
        plt.xlabel('Endpoint')
        plt.ylabel('Response Time (ms)')
        plt.title('Response Time Comparison by Endpoint')
        plt.xticks(x, endpoint_names, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'response_time_comparison.png'))
        plt.close()

    def _generate_response_time_distribution_chart(self, endpoint_name, stats, charts_dir):
        """Generate a response time distribution chart for an endpoint."""
        plt.figure(figsize=(10, 6))
        
        response_times = [result['response_time'] for result in stats['raw_results']]
        
        plt.hist(response_times, bins=20, alpha=0.7, color='blue')
        plt.axvline(stats['mean'], color='red', linestyle='dashed', linewidth=2, label=f"Mean: {stats['mean']:.2f} ms")
        plt.axvline(stats['median'], color='green', linestyle='dashed', linewidth=2, label=f"Median: {stats['median']:.2f} ms")
        plt.axvline(stats['p95'], color='orange', linestyle='dashed', linewidth=2, label=f"95th Percentile: {stats['p95']:.2f} ms")
        
        plt.xlabel('Response Time (ms)')
        plt.ylabel('Frequency')
        plt.title(f'Response Time Distribution - {endpoint_name}')
        plt.legend()
        plt.tight_layout()
        
        # Create a valid filename
        filename = f"distribution_{endpoint_name.lower().replace(' ', '_')}.png"
        plt.savefig(os.path.join(charts_dir, filename))
        plt.close()

    def _generate_success_rate_chart(self, charts_dir):
        """Generate a chart comparing success rates across endpoints."""
        plt.figure(figsize=(12, 8))
        
        endpoint_names = list(self.results.keys())
        success_rates = [stats['success_rate'] for stats in self.results.values()]
        error_rates = [stats['error_rate'] for stats in self.results.values()]
        
        x = np.arange(len(endpoint_names))
        width = 0.35
        
        plt.bar(x - width/2, success_rates, width, label='Success Rate')
        plt.bar(x + width/2, error_rates, width, label='Error Rate')
        
        plt.xlabel('Endpoint')
        plt.ylabel('Rate (%)')
        plt.title('Success and Error Rates by Endpoint')
        plt.xticks(x, endpoint_names, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'success_rate_comparison.png'))
        plt.close()

if __name__ == '__main__':
    # Create and run the performance tester
    tester = FinOpsCopilotAPIPerformanceTester()
    tester.run_tests()
    tester.generate_report()
