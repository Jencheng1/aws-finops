import unittest
import requests
import json
import time
import os
import sys
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class TestFinOpsCopilotE2E(unittest.TestCase):
    """End-to-end tests for the FinOps Copilot system."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests."""
        # Get the API endpoint from environment variable or use default
        cls.api_endpoint = os.environ.get('FINOPS_COPILOT_API_ENDPOINT', 'http://localhost:8080')
        
        # Get the dashboard URL from environment variable or use default
        cls.dashboard_url = os.environ.get('FINOPS_COPILOT_DASHBOARD_URL', 'http://localhost:8501')
        
        # Set up Chrome options for headless browser testing
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize the WebDriver
        cls.driver = webdriver.Chrome(options=chrome_options)
        
        # Set implicit wait time
        cls.driver.implicitly_wait(10)
        
        # Set up API authentication
        cls.api_key = os.environ.get('FINOPS_COPILOT_API_KEY', 'test-api-key')
        cls.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {cls.api_key}'
        }
        
        # Wait for the API and dashboard to be ready
        cls._wait_for_api_ready()
        cls._wait_for_dashboard_ready()

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures that are used for all tests."""
        # Close the WebDriver
        cls.driver.quit()

    @classmethod
    def _wait_for_api_ready(cls):
        """Wait for the API to be ready."""
        max_retries = 30
        retry_interval = 2
        
        for i in range(max_retries):
            try:
                response = requests.get(f"{cls.api_endpoint}/health")
                if response.status_code == 200:
                    print("API is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            
            print(f"Waiting for API to be ready (attempt {i+1}/{max_retries})...")
            time.sleep(retry_interval)
        
        raise Exception("API is not ready after maximum retries")

    @classmethod
    def _wait_for_dashboard_ready(cls):
        """Wait for the dashboard to be ready."""
        max_retries = 30
        retry_interval = 2
        
        for i in range(max_retries):
            try:
                cls.driver.get(cls.dashboard_url)
                # Check if the dashboard title is present
                if "FinOps Copilot" in cls.driver.title:
                    print("Dashboard is ready")
                    return
            except Exception:
                pass
            
            print(f"Waiting for dashboard to be ready (attempt {i+1}/{max_retries})...")
            time.sleep(retry_interval)
        
        raise Exception("Dashboard is not ready after maximum retries")

    def test_01_dashboard_loads(self):
        """Test that the dashboard loads correctly."""
        # Navigate to the dashboard
        self.driver.get(self.dashboard_url)
        
        # Wait for the dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check that the dashboard title is present
        h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
        dashboard_title_present = False
        for h1 in h1_elements:
            if "FinOps Copilot" in h1.text:
                dashboard_title_present = True
                break
        
        self.assertTrue(dashboard_title_present, "Dashboard title not found")
        
        # Check that the navigation menu is present
        navigation_menu = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content")
        self.assertTrue(len(navigation_menu) > 0, "Navigation menu not found")

    def test_02_cost_analysis_page(self):
        """Test the cost analysis page functionality."""
        # Navigate to the dashboard
        self.driver.get(self.dashboard_url)
        
        # Wait for the dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Click on the Cost Analysis link in the navigation menu
        cost_analysis_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Cost Analysis')]")
        if len(cost_analysis_links) > 0:
            cost_analysis_links[0].click()
        else:
            # Try finding it in the sidebar
            sidebar_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content a")
            for link in sidebar_links:
                if "Cost Analysis" in link.text:
                    link.click()
                    break
        
        # Wait for the cost analysis page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Cost Analysis')]"))
        )
        
        # Check that the cost chart is present
        cost_charts = self.driver.find_elements(By.CSS_SELECTOR, ".js-plotly-plot")
        self.assertTrue(len(cost_charts) > 0, "Cost chart not found")
        
        # Check that the service breakdown is present
        service_breakdown = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Service Breakdown')]")
        self.assertTrue(len(service_breakdown) > 0, "Service breakdown not found")

    def test_03_recommendations_page(self):
        """Test the recommendations page functionality."""
        # Navigate to the dashboard
        self.driver.get(self.dashboard_url)
        
        # Wait for the dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Click on the Recommendations link in the navigation menu
        recommendations_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Recommendations')]")
        if len(recommendations_links) > 0:
            recommendations_links[0].click()
        else:
            # Try finding it in the sidebar
            sidebar_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content a")
            for link in sidebar_links:
                if "Recommendations" in link.text:
                    link.click()
                    break
        
        # Wait for the recommendations page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Recommendations')]"))
        )
        
        # Check that the recommendations are present
        recommendations = self.driver.find_elements(By.CSS_SELECTOR, ".stExpander")
        self.assertTrue(len(recommendations) > 0, "Recommendations not found")
        
        # Expand the first recommendation
        if len(recommendations) > 0:
            recommendations[0].click()
            
            # Wait for the recommendation details to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".stExpander .stExpanderContent"))
            )
            
            # Check that the recommendation details are present
            recommendation_details = self.driver.find_elements(By.CSS_SELECTOR, ".stExpander .stExpanderContent")
            self.assertTrue(len(recommendation_details) > 0, "Recommendation details not found")

    def test_04_api_health_check(self):
        """Test the API health check endpoint."""
        # Send a request to the health check endpoint
        response = requests.get(f"{self.api_endpoint}/health")
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")

    def test_05_api_cost_data(self):
        """Test the API cost data endpoint."""
        # Send a request to the cost data endpoint
        response = requests.get(
            f"{self.api_endpoint}/costs",
            headers=self.headers
        )
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("totalCost", data)
        self.assertIn("costByService", data)
        self.assertIn("costTrend", data)

    def test_06_api_recommendations(self):
        """Test the API recommendations endpoint."""
        # Send a request to the recommendations endpoint
        response = requests.get(
            f"{self.api_endpoint}/recommendations",
            headers=self.headers
        )
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertTrue(isinstance(data, list))
        
        # Check that each recommendation has the expected structure
        if len(data) > 0:
            recommendation = data[0]
            self.assertIn("id", recommendation)
            self.assertIn("title", recommendation)
            self.assertIn("service", recommendation)
            self.assertIn("estimatedSavings", recommendation)
            self.assertIn("impact", recommendation)
            self.assertIn("effort", recommendation)
            self.assertIn("description", recommendation)
            self.assertIn("implementationSteps", recommendation)

    def test_07_api_tagging_compliance(self):
        """Test the API tagging compliance endpoint."""
        # Send a request to the tagging compliance endpoint
        response = requests.get(
            f"{self.api_endpoint}/tagging/compliance",
            headers=self.headers
        )
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("complianceScore", data)
        self.assertIn("complianceByTag", data)
        self.assertIn("untaggedResources", data)

    def test_08_api_forecast(self):
        """Test the API forecast endpoint."""
        # Send a request to the forecast endpoint
        response = requests.get(
            f"{self.api_endpoint}/costs/forecast",
            headers=self.headers
        )
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("forecastData", data)
        self.assertTrue(isinstance(data["forecastData"], list))
        
        # Check that each forecast data point has the expected structure
        if len(data["forecastData"]) > 0:
            forecast_point = data["forecastData"][0]
            self.assertIn("date", forecast_point)
            self.assertIn("amount", forecast_point)
            self.assertIn("lowerBound", forecast_point)
            self.assertIn("upperBound", forecast_point)

    def test_09_end_to_end_workflow(self):
        """Test the complete end-to-end workflow."""
        # Navigate to the dashboard
        self.driver.get(self.dashboard_url)
        
        # Wait for the dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check the overview page
        overview_title = self.driver.find_elements(By.XPATH, "//h1[contains(text(), 'Overview')]")
        self.assertTrue(len(overview_title) > 0, "Overview title not found")
        
        # Navigate to the Cost Analysis page
        cost_analysis_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Cost Analysis')]")
        if len(cost_analysis_links) > 0:
            cost_analysis_links[0].click()
        else:
            # Try finding it in the sidebar
            sidebar_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content a")
            for link in sidebar_links:
                if "Cost Analysis" in link.text:
                    link.click()
                    break
        
        # Wait for the cost analysis page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Cost Analysis')]"))
        )
        
        # Check that the cost chart is present
        cost_charts = self.driver.find_elements(By.CSS_SELECTOR, ".js-plotly-plot")
        self.assertTrue(len(cost_charts) > 0, "Cost chart not found")
        
        # Navigate to the Recommendations page
        recommendations_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Recommendations')]")
        if len(recommendations_links) > 0:
            recommendations_links[0].click()
        else:
            # Try finding it in the sidebar
            sidebar_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content a")
            for link in sidebar_links:
                if "Recommendations" in link.text:
                    link.click()
                    break
        
        # Wait for the recommendations page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Recommendations')]"))
        )
        
        # Check that the recommendations are present
        recommendations = self.driver.find_elements(By.CSS_SELECTOR, ".stExpander")
        self.assertTrue(len(recommendations) > 0, "Recommendations not found")
        
        # Navigate to the Tagging Compliance page
        tagging_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Tagging')]")
        if len(tagging_links) > 0:
            tagging_links[0].click()
        else:
            # Try finding it in the sidebar
            sidebar_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content a")
            for link in sidebar_links:
                if "Tagging" in link.text:
                    link.click()
                    break
        
        # Wait for the tagging compliance page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Tagging Compliance')]"))
        )
        
        # Check that the compliance score is present
        compliance_score = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'Compliance Score')]")
        self.assertTrue(len(compliance_score) > 0, "Compliance score not found")
        
        # Navigate to the Forecasting page
        forecasting_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Forecasting')]")
        if len(forecasting_links) > 0:
            forecasting_links[0].click()
        else:
            # Try finding it in the sidebar
            sidebar_links = self.driver.find_elements(By.CSS_SELECTOR, ".sidebar .sidebar-content a")
            for link in sidebar_links:
                if "Forecasting" in link.text:
                    link.click()
                    break
        
        # Wait for the forecasting page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Cost Forecasting')]"))
        )
        
        # Check that the forecast chart is present
        forecast_charts = self.driver.find_elements(By.CSS_SELECTOR, ".js-plotly-plot")
        self.assertTrue(len(forecast_charts) > 0, "Forecast chart not found")

if __name__ == '__main__':
    unittest.main()
