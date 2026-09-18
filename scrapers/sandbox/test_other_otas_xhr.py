import undetected_chromedriver as uc
import time
import json
import sys

def test_ota(name, url):
    print(f"\n--- Testing {name} ---")
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(version_main=152, options=options)
    driver.get(url)
    
    print("Waiting 20 seconds for page load...")
    time.sleep(20)
    
    logs = driver.get_log('performance')
    print(f"Captured {len(logs)} performance logs.")
    
    target_urls = []
    for entry in logs:
        log_json = json.loads(entry['message'])['message']
        method = log_json['method']
        
        if method == 'Network.responseReceived':
            res_url = log_json['params']['response']['url']
            # We want json/api responses
            if 'api' in res_url.lower() or 'search' in res_url.lower() or 'flight' in res_url.lower():
                request_id = log_json['params']['requestId']
                target_urls.append((res_url, request_id))
    
    found_json = False
    for res_url, req_id in target_urls:
        try:
            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
            body = res.get('body', '')
            if len(body) > 5000 and ('fare' in body.lower() or 'price' in body.lower()):
                try:
                    json.loads(body)
                    print(f"[SUCCESS] Found JSON XHR on {name}! Length: {len(body)}")
                    print(f"URL: {res_url}")
                    found_json = True
                    break
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            pass
            
    if not found_json:
        print(f"[FAIL] Could not find discrete JSON XHR for {name}.")
        
    driver.quit()

if __name__ == "__main__":
    test_ota("Goibibo", "https://www.goibibo.com/flights/air-DEL-BOM-20260928--1-0-0-E-D/")
    test_ota("EaseMyTrip", "https://flight.easemytrip.com/FlightList/Index?srch=DEL-Delhi-India|BOM-Mumbai-India|28/09/2026&px=1-0-0&cbn=0&ar=undefined&isow=true&isads=false&isrl=false")
