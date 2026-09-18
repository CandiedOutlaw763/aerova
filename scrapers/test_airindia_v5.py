import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India - Complete flow with date...")
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
        
        print(f"Calendar cells: {driver.execute_script('return document.querySelectorAll(\".mat-calendar-body-cell\").length;')}")
        
        # Navigate to September 2026 or October 2026
        print("Navigating to September 2026...")
        for _ in range(14):
            month_text = driver.execute_script("""
                let header = document.querySelector('.mat-calendar-period-button, .ai-date-picker__month-year, mat-calendar-header button');
                return header ? header.innerText : '';
            """)
            print(f"  Month: '{month_text}'")
            if 'September 2026' in month_text or 'Sep 2026' in month_text:
                break
            # Click next month
            driver.execute_script("""
                let nextBtns = document.querySelectorAll('[aria-label="Next month"], .mat-calendar-next-button, button.mat-icon-button:last-child');
                if(nextBtns.length > 0) nextBtns[nextBtns.length-1].click();
            """)
            time.sleep(0.5)
        
        driver.save_screenshot("ai_calendar_sep.png")
        
        print("Clicking day 30...")
        clicked = driver.execute_script("""
            let cells = document.querySelectorAll('.mat-calendar-body-cell');
            for(let c of cells) {
                if(c.innerText.trim() === '30' && !c.classList.contains('mat-calendar-body-disabled')) {
                    c.click();
                    return 'clicked: ' + c.innerText.trim();
                }
            }
            // Fallback: content elements
            let contents = document.querySelectorAll('.mat-calendar-body-cell-content');
            for(let c of contents) {
                if(c.innerText.trim() === '30') {
                    c.click();
                    return 'content-clicked';
                }
            }
            return 'not-found';
        """)
        print("Date click result:", clicked)
        time.sleep(1)
        
        driver.save_screenshot("ai_after_date.png")
        
        print("Clicking Search button...")
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.trim() === 'Search') b.click(); });")
        
        print("Waiting for API response...")
        start_time = time.time()
        success = False
        while time.time() - start_time < 30:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if ('flight' in url.lower() or 'availability' in url.lower()) and 'search' in url.lower():
                            req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                if res.get('body') and len(res['body']) > 200:
                                    print("\nSUCCESS!")
                                    print("URL:", url)
                                    print(res['body'][:800])
                                    success = True
                                    driver.save_screenshot("ai_results.png")
                                    return
                            except:
                                pass
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture API response.")
            driver.save_screenshot("ai_final.png")
            print("Final URL:", driver.current_url)
            
            # Print all XHR URLs seen
            print("\nAll network URLs seen:")
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'airindia' in url.lower() or 'api' in url.lower():
                            print(" -", url[:120])
                except:
                    pass
            
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        traceback.print_exc()
        try:
            driver.save_screenshot("ai_error.png")
        except:
            pass
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
