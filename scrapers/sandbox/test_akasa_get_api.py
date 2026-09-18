import time
import json
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import re

def run():
    options = uc.ChromeOptions()
    driver = uc.Chrome(version_main=152, options=options)
    
    url = "https://prod-bl.qp.akasaair.com/api/ibe/availability/v2/search?origin=DEL&destination=BOM&startDate=2026-09-30T00%3A00%3A00%2B05%3A30&numberOfPassengers=1&channel=WEB&currencyCode=INR"
    
    try:
        print(f"Navigating to API URL: {url}")
        driver.get(url)
        time.sleep(5)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # usually JSON in browser is inside a <pre> tag
        pre_tag = soup.find('pre')
        if pre_tag:
            try:
                data = json.loads(pre_tag.text)
                print("Successfully extracted JSON!")
                print(json.dumps(data, indent=2)[:500])
                
                # Check for price
                if 'data' in data and len(data['data']) > 0:
                    print("\nFirst day price:", data['data'][0].get('price'))
            except Exception as e:
                print(f"JSON parsing error: {e}")
        else:
            print("No <pre> tag found. Raw HTML:")
            print(page_source[:500])
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
