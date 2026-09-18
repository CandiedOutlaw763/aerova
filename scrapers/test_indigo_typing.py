import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo standard UI typing...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
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
        
        # Clear it first
        from_input.send_keys(Keys.CONTROL, 'a')
        from_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        
        for char in "DEL":
            from_input.send_keys(char)
            time.sleep(0.3)
            
        time.sleep(2)
        driver.save_screenshot("indigo_del_typed.png")
        
        driver.execute_script("""
            let items = document.querySelectorAll('.city-selection__list-item, .city-selection__list-item--info, ul.MuiList-root li');
            for (let item of items) {
                if (item.innerText.includes('DEL')) {
                    item.click();
                    return true;
                }
            }
            if(items.length > 0) {
                items[0].click();
                return true;
            }
        """)
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
            time.sleep(0.3)
            
        time.sleep(2)
        driver.save_screenshot("indigo_bom_typed.png")
        
        driver.execute_script("""
            let items = document.querySelectorAll('.city-selection__list-item, .city-selection__list-item--info, ul.MuiList-root li');
            for (let item of items) {
                if (item.innerText.includes('BOM')) {
                    item.click();
                    return true;
                }
            }
            if(items.length > 0) {
                items[0].click();
                return true;
            }
        """)
        time.sleep(1)
        
        print("Interacting with Date...")
        date_inputs = driver.find_elements(By.CSS_SELECTOR, '.search-widget-form-body__date')
        if date_inputs:
            driver.execute_script("arguments[0].click();", date_inputs[0])
            time.sleep(1)
            
        print("Finding target date in calendar...")
        target_day = "30"
        
        driver.save_screenshot("indigo_calendar_open.png")
        
        found = driver.execute_script(f"""
            let targetDay = "{target_day}";
            let cells = document.querySelectorAll('.react-datepicker__day, .DayPicker-Day, [role="gridcell"], td, .custom-date-picker-calendar__day');
            let clicked = false;
            for(let i=0; i<cells.length; i++) {{
                let cell = cells[i];
                if(cell.innerText.trim() === targetDay && !cell.classList.contains('outside-month') && !cell.classList.contains('react-datepicker__day--outside-month') && !cell.classList.contains('custom-date-picker-calendar__day--outside-month')) {{
                    cell.click();
                    clicked = true;
                    break;
                }}
            }}
            return clicked;
        """)
        
        if found:
            print("Date clicked via generic script!")
        else:
            print("Could not find date easily. Searching deeper...")
            
        time.sleep(1)
        driver.save_screenshot("indigo_before_search.png")
        
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
                            if res.get('body') and len(res['body']) > 100:
                                print("\nSUCCESS!")
                                print("URL:", url)
                                print(res['body'][:500])
                                success = True
                                driver.save_screenshot("indigo_success.png")
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("indigo_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
