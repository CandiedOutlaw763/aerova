import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo UI Interaction...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
        # Close any popups
        try:
            driver.execute_script("document.querySelectorAll('.close, button').forEach(el => { if(el.innerText && el.innerText.includes('Accept All')) el.click(); })")
            time.sleep(1)
        except:
            pass
            
        print("Clicking From...")
        # Find the From field and click it
        from_div = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__from')
        from_div.click()
        time.sleep(1)
        
        print("Typing DEL...")
        # The input inside the from_div
        from_input = from_div.find_element(By.CSS_SELECTOR, 'input')
        from_input.send_keys("DEL")
        time.sleep(2)
        from_input.send_keys(Keys.ENTER)
        time.sleep(2)
        
        print("Clicking To...")
        to_div = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to')
        to_div.click()
        time.sleep(1)
        
        print("Typing BOM...")
        to_input = to_div.find_element(By.CSS_SELECTOR, 'input')
        to_input.send_keys("BOM")
        time.sleep(2)
        to_input.send_keys(Keys.ENTER)
        time.sleep(2)
        
        # Close calendar or dropdown if open by clicking body
        ActionChains(driver).move_by_offset(10, 10).click().perform()
        time.sleep(1)
        
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
                                print("\nSUCCESSFULLY CAPTURED RESPONSE BODY!")
                                print(res['body'][:500])
                                success = True
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("indigo_ui_fail.png")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
