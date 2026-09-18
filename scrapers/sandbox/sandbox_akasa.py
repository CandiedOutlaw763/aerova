import sys
import os
import json
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = uc.Chrome(version_main=152, options=options)
    
    try:
        print("Navigating to Akasa...")
        driver.get("https://www.akasaair.com/")
        time.sleep(8)
        
        # Accept cookies
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(el => { if(el.innerText.includes('Accept')) el.click() })")
            time.sleep(2)
        except:
            pass
            
        print("Applying React Setters...")
        react_setter_script = """
        const [originVal, destVal] = arguments;
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        
        const inputs = Array.from(document.querySelectorAll('input'));
        let fromInput, toInput;
        for (let inp of inputs) {
            if (inp.placeholder && inp.placeholder.includes('From')) fromInput = inp;
            if (inp.placeholder && inp.placeholder.includes('To')) toInput = inp;
        }
        
        if (fromInput) {
            nativeSetter.call(fromInput, originVal);
            fromInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        if (toInput) {
            nativeSetter.call(toInput, destVal);
            toInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        """
        driver.execute_script(react_setter_script, "DEL", "BOM")
        time.sleep(3)
        
        print("Finding Date Input to click...")
        # To make sure we select a date so the search is valid
        # In Akasa, usually picking today/tomorrow is default, but let's just trigger the dropdown by clicking the Date field
        try:
            date_input = None
            inputs = driver.find_elements(By.CSS_SELECTOR, "input")
            for inp in inputs:
                if "Departure" in (inp.get_attribute("placeholder") or "") or "Date" in (inp.get_attribute("placeholder") or ""):
                    date_input = inp
                    break
            
            if date_input:
                driver.execute_script("arguments[0].click();", date_input)
                time.sleep(2)
                # Click the first available date in the calendar
                driver.execute_script("document.querySelectorAll('td.p-datepicker-today').forEach(el => el.click());")
                time.sleep(1)
                # If today not found, click any active day
                driver.execute_script("document.querySelectorAll('td:not(.p-disabled) span').forEach(el => el.click());")
                time.sleep(1)
        except Exception as e:
            print(f"Date picker error: {e}")
            
        print("Clicking Search...")
        driver.execute_script("document.querySelectorAll('button').forEach(btn => { if(btn.innerText.includes('Search Flights')) btn.click(); })")
        
        print("Waiting for response...")
        body = None
        start_time = time.time()
        while time.time() - start_time < 20 and not body:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search' in url.lower() or 'flight' in url.lower() or 'api' in url.lower():
                            target_req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': target_req_id})
                                if res.get('body') and ('"fare"' in res['body'] or '"journey"' in res['body']):
                                    body = res['body']
                                    print(f"Captured JSON from {url}")
                                    break
                            except:
                                pass
                except:
                    pass
            time.sleep(1)
            
        if body:
            with open("akasa_payload.json", "w", encoding="utf-8") as f:
                f.write(body)
            print("Successfully saved akasa_payload.json")
        else:
            print("Failed to capture payload.")
            driver.save_screenshot("akasa_sandbox_fail.png")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
