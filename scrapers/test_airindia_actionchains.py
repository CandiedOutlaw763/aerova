import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India ActionChains...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        
        print("Navigating to Air India...")
        driver.get("https://www.airindia.com/")
        time.sleep(8)
        
        print("Accepting cookies...")
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); });")
        except:
            pass
            
        time.sleep(1)
        
        print("Clicking From...")
        driver.execute_script("""
            let spans = document.querySelectorAll('span');
            for(let s of spans) {
                if(s.innerText.trim() === 'From' || s.innerText.includes('Origin')) {
                    s.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        ActionChains(driver).send_keys("DEL").perform()
        time.sleep(2)
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        time.sleep(1)
        
        print("Clicking To...")
        driver.execute_script("""
            let spans = document.querySelectorAll('span');
            for(let s of spans) {
                if(s.innerText.trim() === 'To' || s.innerText.includes('Destination')) {
                    s.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        ActionChains(driver).send_keys("BOM").perform()
        time.sleep(2)
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        time.sleep(1)
        
        driver.save_screenshot("airindia_before_search.png")
        
        print("Clicking Search...")
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Search Flight') || b.innerText.includes('Show Flights') || b.innerText.includes('Search')) b.click(); });")
        except:
            print("Could not click search")
                
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
                        if 'flight' in url.lower() and 'search' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body'):
                                print("\nSUCCESS!")
                                print(url)
                                print(res['body'][:500])
                                success = True
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("airindia_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
