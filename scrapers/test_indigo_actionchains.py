import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo UI with pure ActionChains...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
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
        
        actions = ActionChains(driver)
        
        print("Interacting with Origin...")
        driver.execute_script("document.querySelector('.search-widget-form-body__from').click()")
        time.sleep(1)
        actions.send_keys("DEL").perform()
        time.sleep(2)
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(1)
        
        print("Interacting with Destination...")
        driver.execute_script("document.querySelector('.search-widget-form-body__to').click()")
        time.sleep(1)
        actions.send_keys("BOM").perform()
        time.sleep(2)
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(1)
        
        # Close calendar if it opens automatically
        print("Closing calendar...")
        actions.move_by_offset(10, 10).click().perform()
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
                                print("\nSUCCESS!")
                                print(res['body'][:500])
                                success = True
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("indigo_action_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
