import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India - Date selection fix...")
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
        driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
        time.sleep(1.5)
        
        print("Clicking TO field...")
        driver.execute_script("document.querySelector('[aria-label=\"Select destination airport\"]').click();")
        time.sleep(1.5)
        
        print("Typing BOM...")
        driver.switch_to.active_element.send_keys("BOM")
        time.sleep(2)
        
        print("Clicking first mat-option for BOM...")
        driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
        time.sleep(1.5)
        
        print("Clicking Depart date...")
        driver.execute_script("""
            // Click on the "Select Date" area for depart
            let el = document.querySelector('.ai-booking-widget__date-picker, .ai-date-picker, [aria-label*="date"], [aria-label*="Date"]');
            if(el) { el.click(); return; }
            
            // Try to find by text
            let spans = document.querySelectorAll('span, div, button');
            for(let s of spans) {
                if(s.innerText && s.innerText.includes('Select Date') && s.offsetWidth > 0) {
                    s.click(); break;
                }
            }
        """)
        time.sleep(1.5)
        driver.save_screenshot("ai_calendar_open.png")
        
        print("Checking for calendar...")
        cal_info = driver.execute_script("""
            let cells = document.querySelectorAll('.mat-calendar-body-cell, [role="gridcell"] button, mat-calendar-body-cell-content');
            return {
                count: cells.length,
                sample: cells.length > 0 ? cells[0].innerText.trim() : 'none',
                ariaLabels: Array.from(cells).slice(0, 5).map(c => c.getAttribute('aria-label') || c.innerText.trim())
            };
        """)
        print("Calendar cells:", json.dumps(cal_info))
        
        # Try to navigate to Sep 2026 if not there
        print("Navigating to October 2026...")
        for _ in range(14):  # Max 14 months forward
            month_title = driver.execute_script("""
                let title = document.querySelector('.mat-calendar-period-button, .mat-datepicker-header, .mat-calendar-header .mat-calendar-period-button');
                return title ? title.innerText : '';
            """)
            print(f"  Current month: {month_title}")
            if 'October 2026' in month_title or 'Sep' in month_title:
                break
            # Click next
            driver.execute_script("""
                let nextBtn = document.querySelector('.mat-calendar-next-button, [aria-label="Next month"]');
                if(nextBtn) nextBtn.click();
            """)
            time.sleep(0.5)
        
        print("Clicking day 30...")
        clicked_date = driver.execute_script("""
            let cells = document.querySelectorAll('.mat-calendar-body-cell');
            for(let c of cells) {
                if(c.innerText.trim() === '30') {
                    c.click();
                    return true;
                }
            }
            // Try buttons inside cells
            let btns = document.querySelectorAll('.mat-calendar-body-cell-content');
            for(let b of btns) {
                if(b.innerText.trim() === '30') {
                    b.click();
                    return true;
                }
            }
            return false;
        """)
        print("Date clicked:", clicked_date)
        time.sleep(1)
        
        driver.save_screenshot("ai_after_date.png")
        
        print("Clicking Search...")
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
                        if 'flight' in url.lower() and ('search' in url.lower() or 'availability' in url.lower()):
                            req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                if res.get('body') and len(res['body']) > 100:
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
            print("Failed to capture response.")
            driver.save_screenshot("ai_final.png")
            print("Final URL:", driver.current_url)
            
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        traceback.print_exc()
        driver.save_screenshot("ai_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
