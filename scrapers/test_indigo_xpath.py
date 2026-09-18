import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo with XPath...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
        # Hide any fixed elements that might block clicks
        driver.execute_script("""
            document.querySelectorAll('*').forEach(el => {
                try {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.display = 'none';
                    }
                } catch(e) {}
            });
        """)
        time.sleep(1)
        
        print("Interacting with Origin...")
        from_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__from input')
        driver.execute_script("arguments[0].click();", from_input)
        time.sleep(1)
        from_input.send_keys(Keys.CONTROL, 'a')
        from_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "DEL":
            from_input.send_keys(char)
            time.sleep(0.1)
            
        print("Waiting for Origin list item...")
        start = time.time()
        while time.time() - start < 5:
            try:
                item = driver.find_element(By.XPATH, "//li[contains(., 'DEL')]")
                driver.execute_script("arguments[0].click();", item)
                print("Clicked Origin!")
                break
            except:
                time.sleep(0.5)
        
        time.sleep(1)
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        driver.execute_script("arguments[0].click();", to_input)
        time.sleep(1)
        to_input.send_keys(Keys.CONTROL, 'a')
        to_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "BOM":
            to_input.send_keys(char)
            time.sleep(0.1)
            
        print("Waiting for Destination list item...")
        start = time.time()
        while time.time() - start < 5:
            try:
                item = driver.find_element(By.XPATH, "//li[contains(., 'BOM')]")
                driver.execute_script("arguments[0].click();", item)
                print("Clicked Destination!")
                break
            except:
                time.sleep(0.5)
                
        time.sleep(1)
        
        driver.save_screenshot("indigo_xpath_check.png")
        
        print("Clicking Search...")
        search_btn = driver.find_element(By.CSS_SELECTOR, 'button.skyplus-button--filled')
        driver.execute_script("arguments[0].click();", search_btn)
        
        print("Waiting for API response...")
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
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
