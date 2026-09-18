import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo UI with Ultimate Approach...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
        print("Hiding fixed elements...")
        # Hide any fixed elements that might block clicks (like headers/footers/cookie banners)
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
        from_input.click()
        time.sleep(0.5)
        # Clear it
        from_input.send_keys(Keys.CONTROL, 'a')
        from_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        from_input.send_keys("DEL")
        time.sleep(2)
        from_input.send_keys(Keys.ENTER)
        time.sleep(1)
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        to_input.click()
        time.sleep(0.5)
        to_input.send_keys("BOM")
        time.sleep(2)
        to_input.send_keys(Keys.ENTER)
        time.sleep(1)
        
        # Close calendar if it opens automatically
        print("Closing calendar...")
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        print("Clicking Search...")
        search_btn = driver.find_element(By.CSS_SELECTOR, 'button.skyplus-button--filled')
        search_btn.click()
        
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
            driver.save_screenshot("indigo_ultimate_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
        driver.save_screenshot("indigo_ultimate_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
