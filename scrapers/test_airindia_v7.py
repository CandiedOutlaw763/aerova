import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India - Capture air-bounds API response...")
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
        
        print("Clicking 'One Way'...")
        driver.execute_script("""
            let inputs = document.querySelectorAll('input[type="radio"]');
            for(let i of inputs) { if(i.value === 'one-way') { i.click(); break; } }
        """)
        time.sleep(0.5)
        
        print("Filling FROM = DEL...")
        driver.execute_script("document.querySelector('[aria-label=\"Select origin airport\"]').click();")
        time.sleep(1.5)
        driver.switch_to.active_element.send_keys("DEL")
        time.sleep(2)
        driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
        time.sleep(1.5)
        
        print("Filling TO = BOM...")
        driver.execute_script("document.querySelector('[aria-label=\"Select destination airport\"]').click();")
        time.sleep(1.5)
        driver.switch_to.active_element.send_keys("BOM")
        time.sleep(2)
        driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
        time.sleep(1.5)
        
        print("Opening date picker...")
        depart_el = driver.find_element(By.XPATH, "//*[contains(text(), 'Select Date')]")
        driver.execute_script("arguments[0].click();", depart_el)
        time.sleep(1.5)
        
        print("Clicking day 30...")
        driver.execute_script("""
            let contents = document.querySelectorAll('.mat-calendar-body-cell-content');
            for(let c of contents) {
                if(c.innerText.trim() === '30') { c.click(); return; }
            }
        """)
        time.sleep(1)
        
        print("Clicking Search button...")
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.trim() === 'Search') b.click(); });")
        
        print("Waiting for air-bounds API call...")
        start_time = time.time()
        success = False
        
        while time.time() - start_time < 35:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'air-bounds' in url or 'airbound' in url.lower():
                            req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                body = res.get('body', '')
                                if body and len(body) > 100:
                                    print("\n=== SUCCESS - air-bounds response ===")
                                    print("URL:", url)
                                    print("Body preview:")
                                    print(body[:2000])
                                    success = True
                                    driver.save_screenshot("ai_results.png")
                                    return
                            except Exception as e2:
                                print(f"Body fetch error: {e2}")
                except:
                    pass
            time.sleep(0.5)
            
        if not success:
            print("Did not capture air-bounds response in time.")
            driver.save_screenshot("ai_final.png")
            
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
