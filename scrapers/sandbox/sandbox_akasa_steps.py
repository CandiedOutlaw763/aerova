import sys
import os
import json
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains

def click_absolute(driver, x, y):
    actions = ActionChains(driver)
    actions.w3c_actions.pointer_action.move_to_location(x, y)
    actions.w3c_actions.pointer_action.click()
    actions.perform()
    time.sleep(2)

def run():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = uc.Chrome(version_main=152, options=options)
    
    try:
        driver.get("https://www.akasaair.com/")
        time.sleep(10)
        
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(el => { if(el.innerText.includes('Accept')) el.click() })")
            time.sleep(2)
        except:
            pass
            
        print("Clicking Origin...")
        click_absolute(driver, 218, 464)
        ActionChains(driver).send_keys("DEL").perform()
        time.sleep(2)
        click_absolute(driver, 257, 782)
        
        print("Clicking Destination...")
        click_absolute(driver, 375, 464)
        ActionChains(driver).send_keys("BOM").perform()
        time.sleep(2)
        click_absolute(driver, 439, 782)
        
        print("Clicking Date...")
        click_absolute(driver, 495, 464)
        click_absolute(driver, 426, 778)
        
        print("Clicking Search...")
        click_absolute(driver, 795, 604)
        
        print("Waiting for response...")
        body_json = None
        start_time = time.time()
        while time.time() - start_time < 20 and not body_json:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if ('api/nsk' in url.lower() or 'search' in url.lower()) and 'storyblok' not in url.lower():
                            target_req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': target_req_id})
                                if res.get('body') and ('"fare"' in res['body'] or '"journey"' in res['body'] or '"amount"' in res['body'] or '"flights"' in res['body']):
                                    body_json = res['body']
                                    print(f"Captured JSON from {url}")
                                    break
                            except:
                                pass
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("akasa_final_state.png")
        if body_json:
            with open("akasa_payload.json", "w", encoding="utf-8") as f:
                f.write(body_json)
            print("Successfully saved akasa_payload.json")
        else:
            print("Failed to capture payload.")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
