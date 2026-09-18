import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India - Full working flow...")
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
        
        print("Clicking 'One Way' radio button...")
        driver.execute_script("""
            let inputs = document.querySelectorAll('input[type="radio"]');
            for(let i of inputs) {
                if(i.value === 'one-way') { i.click(); break; }
            }
        """)
        time.sleep(0.5)
        
        print("Clicking FROM field...")
        driver.execute_script("document.querySelector('[aria-label=\"Select origin airport\"]').click();")
        time.sleep(1.5)
        
        print("Typing DEL...")
        driver.switch_to.active_element.send_keys("DEL")
        time.sleep(2)
        
        print("Clicking first mat-option for DEL...")
        # Material Design uses mat-option elements in an overlay
        clicked = driver.execute_script("""
            // Try mat-option first
            let opts = document.querySelectorAll('mat-option');
            if(opts.length > 0) { opts[0].click(); return 'mat-option'; }
            
            // Try mdc-list-item
            let listItems = document.querySelectorAll('.mdc-list-item');
            if(listItems.length > 0) { listItems[0].click(); return 'mdc-list-item'; }
            
            // Try any li with DEL
            let lis = document.querySelectorAll('li');
            for(let li of lis) {
                if(li.innerText.includes('DEL')) { li.click(); return 'li-DEL'; }
            }
            
            return 'none';
        """)
        print(f"DEL click method: {clicked}")
        time.sleep(1.5)
        
        driver.save_screenshot("ai_after_del.png")
        
        print("Clicking TO field...")
        driver.execute_script("document.querySelector('[aria-label=\"Select destination airport\"]').click();")
        time.sleep(1.5)
        
        print("Typing BOM...")
        driver.switch_to.active_element.send_keys("BOM")
        time.sleep(2)
        
        print("Clicking first mat-option for BOM...")
        clicked2 = driver.execute_script("""
            let opts = document.querySelectorAll('mat-option');
            if(opts.length > 0) { opts[0].click(); return 'mat-option'; }
            
            let listItems = document.querySelectorAll('.mdc-list-item');
            if(listItems.length > 0) { listItems[0].click(); return 'mdc-list-item'; }
            
            let lis = document.querySelectorAll('li');
            for(let li of lis) {
                if(li.innerText.includes('BOM') || li.innerText.includes('Mumbai')) { li.click(); return 'li-BOM'; }
            }
            
            return 'none';
        """)
        print(f"BOM click method: {clicked2}")
        time.sleep(1.5)
        
        driver.save_screenshot("ai_after_bom.png")
        
        print("Selecting Date...")
        # Click Depart date field
        try:
            driver.execute_script("""
                let btns = document.querySelectorAll('button, div');
                for(let b of btns) {
                    if(b.innerText && b.innerText.includes('Select Date') && b.innerText.includes('Depart')) {
                        b.click();
                        break;
                    }
                }
            """)
        except:
            pass
        time.sleep(1)
        
        # Try clicking "30" in the calendar
        driver.execute_script("""
            let cells = document.querySelectorAll('[role="gridcell"] button, .mat-calendar-body-cell, td.mat-calendar-body-cell');
            for(let c of cells) {
                if(c.innerText.trim() === '30' || c.getAttribute('aria-label') && c.getAttribute('aria-label').includes('30')) {
                    c.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        driver.save_screenshot("ai_after_date.png")
        
        print("Clicking Search...")
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.trim() === 'Search') b.click(); });")
        
        print("Waiting for API response...")
        start_time = time.time()
        success = False
        while time.time() - start_time < 25:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'flight' in url.lower() and ('search' in url.lower() or 'availability' in url.lower()):
                            req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                if res.get('body') and len(res['body']) > 100:
                                    print("\nSUCCESS!")
                                    print("URL:", url)
                                    print(res['body'][:800])
                                    success = True
                                    return
                            except:
                                pass
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("ai_final.png")
            print("Final URL:", driver.current_url)
            
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
