import undetected_chromedriver as uc
import time
import json

def capture_goibibo():
    print("Launching UC...")
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(version_main=152, options=options)
    driver.get("https://www.goibibo.com/flights/air-DEL-BOM-20260928--1-0-0-E-D/")
    
    print("Waiting 20 seconds...")
    time.sleep(20)
    
    logs = driver.get_log('performance')
    
    target_req_id = None
    target_url = None
    
    for entry in logs:
        try:
            log_json = json.loads(entry['message'])['message']
            method = log_json['method']
            
            if method == 'Network.responseReceived':
                res = log_json['params']['response']
                url = res.get('url', '')
                if 'search-stream-dt' in url.lower() or 'search' in url.lower():
                    # We might want to see all URLs briefly
                    if 'api' in url.lower():
                        print(f"API Response: {url}")
                        if 'search-stream-dt' in url.lower():
                            target_req_id = log_json['params']['requestId']
                            target_url = url
        except:
            pass
            
    if target_req_id:
        print(f"\nAttempting to read body for Goibibo search-stream-dt requestId: {target_req_id}")
        try:
            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': target_req_id})
            body = res.get('body', '')
            print(f"Body length: {len(body)}")
            print(f"Preview: {body[:500]}")
        except Exception as e:
            print("Failed to get body:", e)
    else:
        print("Did not find search-stream-dt response in Goibibo logs.")

    driver.quit()

if __name__ == "__main__":
    capture_goibibo()
