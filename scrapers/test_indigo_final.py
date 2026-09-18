import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo Final Working Solution...")
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
            time.sleep(0.2)
            
        print("Waiting 3 seconds for list to update...")
        time.sleep(3)
        driver.execute_script("document.querySelectorAll('ul.MuiList-root li')[0].click();")
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
            time.sleep(0.2)
            
        print("Waiting 3 seconds for list to update...")
        time.sleep(3)
        driver.execute_script("document.querySelectorAll('ul.MuiList-root li')[0].click();")
        time.sleep(2)
        
        print("Interacting with Date...")
        # At this point the calendar should be automatically open!
        # Let's search for "30" in the active month view
        found = driver.execute_script("""
            let targetDay = "30";
            let cells = document.querySelectorAll('.react-datepicker__day, .DayPicker-Day, [role="gridcell"], td');
            let clicked = false;
            for(let i=0; i<cells.length; i++) {
                let cell = cells[i];
                if(cell.innerText.trim() === targetDay && !cell.classList.contains('outside-month') && !cell.classList.contains('react-datepicker__day--outside-month') && window.getComputedStyle(cell).display !== 'none') {
                    cell.click();
                    clicked = true;
                    break;
                }
            }
            return clicked;
        """)
        
        if found:
            print("Clicked date!")
        else:
            print("Could not click date!")
            driver.save_screenshot("indigo_calendar_not_found.png")
            
        time.sleep(1)
        
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
            driver.save_screenshot("indigo_final_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
