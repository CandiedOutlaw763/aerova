import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def run():
    print("Testing SpiceJet Full Search and Extraction FINAL...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.spicejet.com/")
        time.sleep(10)
        
        print("Clicking Destination input...")
        driver.execute_script("""
            let inps = document.querySelectorAll('input');
            for(let i of inps) {
                if(i.value === 'Select Destination') {
                    i.focus();
                    i.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        
        print("Typing BOM in destination...")
        active = driver.switch_to.active_element
        for char in "BOM":
            active.send_keys(char)
            time.sleep(0.2)
        time.sleep(2)
        
        print("Clicking BOM from dropdown...")
        driver.execute_script("""
            let els = document.querySelectorAll('div');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'BOM') {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        
        print("Clicking anywhere to close popup...")
        ActionChains(driver).move_by_offset(50, 50).click().perform()
        time.sleep(2)
        
        print("Clicking Search...")
        try:
            search_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='home-page-flight-cta']")
            ActionChains(driver).move_to_element(search_btn).click().perform()
        except Exception as e:
            print("Failed ActionChains click.", str(e))
            driver.execute_script("""
                document.querySelector("[data-testid='home-page-flight-cta']").click();
            """)
        
        driver.save_screenshot("spicejet_after_search.png")
        
        print("Waiting for API response...")
        start_time = time.time()
        
        while time.time() - start_time < 30:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search' in url.lower() or 'flight' in url.lower() or 'availability' in url.lower() or 'api/v1' in url.lower():
                            if 'gstatic' not in url and 'google' not in url and 'facebook' not in url:
                                print(f"API Intercepted: {url}")
                                if 'customflightsearch' in url.lower() or 'search' in url.lower():
                                    req_id = log_json['params']['requestId']
                                    res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                    body = res.get('body', '')
                                    if len(body) > 2500 and ('flights' in body.lower() or 'fares' in body.lower() or 'currencyCode' in body):
                                        print(f"Jackpot! Flight API: {url} | Length: {len(body)}")
                                        with open('spicejet_jackpot_real.json', 'w') as f:
                                            f.write(body)
                                        return
                except Exception:
                    pass
            time.sleep(1)
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
