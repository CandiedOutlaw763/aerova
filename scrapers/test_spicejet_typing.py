import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def run():
    print("Testing SpiceJet Typing and Interception with Standard Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.spicejet.com/")
        time.sleep(10)
        
        # 1. Click Origin
        print("Clicking Origin...")
        driver.execute_script("""
            let inps = document.querySelectorAll('input');
            for(let i of inps) {
                if(i.value.includes('Delhi') || i.value.includes('DEL')) {
                    i.focus();
                    i.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        
        # 2. Type Destination
        print("Typing Destination...")
        active = driver.switch_to.active_element
        for char in "BOM":
            active.send_keys(char)
            time.sleep(0.2)
        time.sleep(2)
        
        print("Clicking BOM from dropdown...")
        try:
            bom = driver.find_element(By.XPATH, "//*[contains(text(), 'Mumbai')]")
            ActionChains(driver).move_to_element(bom).click().perform()
        except:
            print("Could not click BOM")
        time.sleep(2)
        
        # 3. Select Date
        print("Selecting Date...")
        driver.execute_script("""
            let cells = document.querySelectorAll('div');
            for(let cell of cells) {
                if (cell.innerText && cell.innerText.trim() === '30' && cell.getAttribute('data-testid') && cell.getAttribute('data-testid').includes('undefined-calendar-day')) {
                    cell.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        driver.save_screenshot("spicejet_ready.png")
        
        # 4. Search
        print("Clicking Search...")
        driver.execute_script("""
            let els = document.querySelectorAll('div, span');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Search Flight') {
                    el.click();
                    break;
                }
            }
        """)
        
        print("Waiting for API response...")
        start_time = time.time()
        
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search' in url.lower() or 'flight' in url.lower() or 'availability' in url.lower():
                            if 'gstatic' not in url and 'google' not in url and 'facebook' not in url:
                                print(f"Found potential API: {url}")
                except Exception:
                    pass
            time.sleep(1)
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
