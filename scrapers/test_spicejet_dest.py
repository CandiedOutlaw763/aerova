import time
import json
from selenium import webdriver

def run():
    print("Testing SpiceJet Destination Selection and Search...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.spicejet.com/")
        time.sleep(10)
        
        print("Clicking Destination input...")
        # Since default is DEL, we just click the second input (Destination)
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
        time.sleep(3)
        
        print("Typing BOM in destination...")
        active = driver.switch_to.active_element
        for char in "BOM":
            active.send_keys(char)
            time.sleep(0.2)
        time.sleep(3)
        
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
        time.sleep(3)
        
        driver.save_screenshot("spicejet_dest_selected.png")
        
        print("Clicking Search...")
        driver.execute_script("""
            let els = document.querySelectorAll('div');
            for(let el of els) {
                let text = el.innerText;
                if(text && text.trim() === 'Search Flight') {
                    // Check if it's the actual button container
                    let rect = el.getBoundingClientRect();
                    if(rect.width > 50 && rect.height > 20) {
                        el.click();
                        break;
                    }
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
                                print(f"API: {url}")
                                if 'availability' in url.lower() or 'search' in url.lower():
                                    req_id = log_json['params']['requestId']
                                    res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                    body = res.get('body', '')
                                    if len(body) > 1000:
                                        print(f"Jackpot! Extracted length: {len(body)}")
                                        with open('spicejet_jackpot.json', 'w') as f:
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
