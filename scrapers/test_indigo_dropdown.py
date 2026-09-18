import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo UI with Dropdown Clicks...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(10)
        
        # Click Accept All on cookie banner to unblock UI
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click() })")
            time.sleep(1)
        except:
            pass
            
        print("Interacting with Origin...")
        driver.execute_script("document.querySelector('.search-widget-form-body__from').click()")
        time.sleep(1)
        # Assuming the input is focused, type DEL
        driver.execute_script("document.activeElement.value = 'DEL'; document.activeElement.dispatchEvent(new Event('input', {bubbles: true}));")
        time.sleep(2)
        
        # Find the dropdown option for DEL and click it
        try:
            driver.execute_script("document.querySelector('ul.MuiList-root li').click()")
            print("Clicked Origin dropdown")
        except:
            print("Origin dropdown not found")
            
        time.sleep(2)
        print("Interacting with Destination...")
        # Since clicking Origin dropdown might automatically focus Destination, let's just type BOM or click it first
        driver.execute_script("document.querySelector('.search-widget-form-body__to').click()")
        time.sleep(1)
        driver.execute_script("document.activeElement.value = 'BOM'; document.activeElement.dispatchEvent(new Event('input', {bubbles: true}));")
        time.sleep(2)
        
        # Find the dropdown option for BOM and click it
        try:
            driver.execute_script("document.querySelector('ul.MuiList-root li').click()")
            print("Clicked Destination dropdown")
        except:
            print("Destination dropdown not found")
            
        time.sleep(2)
        print("Clicking Search...")
        driver.execute_script("document.querySelector('button.skyplus-button--filled').click()")
        
        print("Waiting for response...")
        start_time = time.time()
        success = False
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'flight' in url.lower() and 'search' in url.lower() and 'v2' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body'):
                                print("\nSUCCESS!")
                                print(res['body'][:500])
                                success = True
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("indigo_dropdown_fail.png")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
