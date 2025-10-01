#!/usr/bin/env python3
"""
Simplified UI test that assumes Streamlit is already running
"""

import unittest
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import sys

class TestStreamlitUI(unittest.TestCase):
    """Test Streamlit UI with Selenium"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver"""
        print("\n=== Setting up Selenium WebDriver ===")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize driver
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.set_page_load_timeout(30)
        
        # Load Streamlit app
        print("Connecting to Streamlit app...")
        cls.driver.get("http://localhost:8501")
        
        # Wait for app to load
        cls.wait = WebDriverWait(cls.driver, 30)
        time.sleep(5)  # Extra wait for full load
        
        print("✓ Connected to Streamlit")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        cls.driver.quit()
        print("✓ Browser closed")
    
    def wait_and_find(self, by, value, timeout=10):
        """Wait for element and return it"""
        return self.wait.until(EC.presence_of_element_located((by, value)))
    
    def safe_click(self, element):
        """Click element safely"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        self.driver.execute_script("arguments[0].click();", element)
    
    def test_01_main_page_elements(self):
        """Test main page loads correctly"""
        print("\n=== Test 1: Main Page Elements ===")
        
        # Check title
        try:
            title = self.driver.find_element(By.TAG_NAME, "h1")
            print(f"✓ Page title: {title.text[:50]}...")
        except:
            print("⚠ Title not found")
        
        # Check for metrics
        metrics = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='metric-container']")
        print(f"✓ Found {len(metrics)} metric containers")
        
        # Check for tabs
        tabs = self.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")
        if not tabs:
            tabs = self.driver.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
        print(f"✓ Found {len(tabs)} tabs")
        
        self.assertGreater(len(tabs), 0, "No tabs found")
    
    def test_02_cost_analytics_tab(self):
        """Test Cost Analytics functionality"""
        print("\n=== Test 2: Cost Analytics Tab ===")
        
        # Already on first tab by default
        time.sleep(3)
        
        # Look for cost charts
        charts = self.driver.find_elements(By.CSS_SELECTOR, ".js-plotly-plot")
        print(f"✓ Found {len(charts)} charts")
        
        # Look for cost metrics
        metrics = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='metric-container']")
        cost_metrics = 0
        for metric in metrics[:5]:
            try:
                text = metric.text
                if "$" in text:
                    cost_metrics += 1
                    print(f"✓ Cost metric: {text.split()[0]}")
            except:
                pass
        
        self.assertGreater(cost_metrics, 0, "No cost metrics found")
    
    def test_03_navigate_tabs(self):
        """Test tab navigation"""
        print("\n=== Test 3: Tab Navigation ===")
        
        # Find all tabs
        tabs = self.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")
        if not tabs:
            tabs = self.driver.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
        
        # Try to click through first 3 tabs
        for i in range(min(3, len(tabs))):
            try:
                tab = tabs[i]
                tab_text = tab.text
                self.safe_click(tab)
                time.sleep(2)
                print(f"✓ Navigated to tab {i+1}: {tab_text}")
                
                # Re-find tabs as DOM might change
                tabs = self.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")
                if not tabs:
                    tabs = self.driver.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
                    
            except Exception as e:
                print(f"⚠ Tab {i+1} navigation: {str(e)[:50]}")
    
    def test_04_button_interactions(self):
        """Test button clicks"""
        print("\n=== Test 4: Button Interactions ===")
        
        # Find all buttons
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"✓ Found {len(buttons)} buttons")
        
        # Look for specific action buttons
        action_keywords = ["Generate", "Analyze", "Scan", "Refresh"]
        
        for keyword in action_keywords:
            try:
                button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{keyword}')]")
                print(f"✓ Found '{keyword}' button")
            except:
                pass
    
    def test_05_feedback_widgets(self):
        """Test feedback system presence"""
        print("\n=== Test 5: Feedback Widgets ===")
        
        # Look for feedback elements
        feedback_found = False
        
        # Check for feedback text areas
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        if textareas:
            print(f"✓ Found {len(textareas)} feedback text areas")
            feedback_found = True
        
        # Check for rating sliders
        sliders = self.driver.find_elements(By.CSS_SELECTOR, "[role='slider']")
        if sliders:
            print(f"✓ Found {len(sliders)} rating sliders")
            feedback_found = True
        
        # Check for submit buttons
        submit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit')]")
        if submit_buttons:
            print(f"✓ Found {len(submit_buttons)} submit buttons")
            feedback_found = True
        
        if feedback_found:
            print("✓ Feedback system is present")
        else:
            print("⚠ No feedback widgets found")
    
    def test_06_sidebar_controls(self):
        """Test sidebar functionality"""
        print("\n=== Test 6: Sidebar Controls ===")
        
        # Check if sidebar exists
        sidebar = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSidebar']")
        if sidebar:
            print("✓ Sidebar found")
            
            # Look for sliders in sidebar
            sliders = sidebar[0].find_elements(By.CSS_SELECTOR, "[role='slider']")
            print(f"✓ Found {len(sliders)} sliders in sidebar")
            
            # Look for checkboxes
            checkboxes = sidebar[0].find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            print(f"✓ Found {len(checkboxes)} checkboxes in sidebar")
        else:
            print("⚠ Sidebar not found")
    
    def test_07_data_displays(self):
        """Test that data is being displayed"""
        print("\n=== Test 7: Data Display ===")
        
        # Check for dataframes
        dataframes = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stDataFrame']")
        if dataframes:
            print(f"✓ Found {len(dataframes)} data tables")
        
        # Check for expandable sections
        expanders = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stExpander']")
        if expanders:
            print(f"✓ Found {len(expanders)} expandable sections")
        
        # Check for any error messages
        errors = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stAlert']")
        error_count = 0
        for error in errors:
            if "error" in error.get_attribute("class").lower():
                error_count += 1
        
        if error_count > 0:
            print(f"⚠ Found {error_count} error messages")
        else:
            print("✓ No error messages found")

def main():
    """Run UI tests"""
    print("\n" + "="*60)
    print("STREAMLIT UI TEST WITH SELENIUM")
    print("="*60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if Streamlit is running
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code != 200:
            print("❌ Streamlit is not running properly")
            return False
    except:
        print("❌ Streamlit is not running. Start it first with:")
        print("   streamlit run enhanced_dashboard_with_feedback.py")
        return False
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamlitUI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)