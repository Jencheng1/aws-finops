#!/usr/bin/env python3
"""
Debug script to capture Streamlit page content
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_page():
    # Find active port
    port = None
    for p in [8503, 8502, 8501]:
        try:
            response = requests.get(f"http://localhost:{p}", timeout=5)
            if response.status_code == 200:
                port = p
                break
        except:
            continue
    
    if not port:
        print("No Streamlit app found")
        return
    
    print(f"Found Streamlit on port {port}")
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load page
        driver.get(f"http://localhost:{port}")
        print("Waiting for page to load...")
        time.sleep(15)  # Extra wait time
        
        # Save screenshot
        driver.save_screenshot("debug_page.png")
        print("Screenshot saved as debug_page.png")
        
        # Get page info
        print("\n=== Page Title ===")
        print(driver.title)
        
        print("\n=== All Text Content (first 500 chars) ===")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(body_text[:500])
        
        print("\n=== Headers (h1-h6) ===")
        headers = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        for i, h in enumerate(headers[:5]):
            print(f"{h.tag_name}: {h.text}")
        
        print("\n=== Buttons ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons[:10]):
            if btn.text:
                print(f"Button {i+1}: {btn.text}")
        
        print("\n=== All divs with data-testid ===")
        testid_divs = driver.find_elements(By.CSS_SELECTOR, "[data-testid]")
        unique_testids = set()
        for div in testid_divs:
            testid = div.get_attribute("data-testid")
            if testid:
                unique_testids.add(testid)
        
        for testid in sorted(unique_testids)[:20]:
            print(f"  - {testid}")
        
        print("\n=== Metrics ===")
        # Try different metric selectors
        metric_selectors = [
            "[data-testid='metric-container']",
            "[data-testid='stMetric']",
            ".metric-container",
            "div[class*='metric']"
        ]
        
        for selector in metric_selectors:
            metrics = driver.find_elements(By.CSS_SELECTOR, selector)
            if metrics:
                print(f"Found {len(metrics)} metrics with selector: {selector}")
                for m in metrics[:3]:
                    print(f"  - {m.text[:50]}")
                break
        
        print("\n=== Page HTML Structure (first 1000 chars) ===")
        html = driver.page_source
        print(html[:1000])
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_page()