import time
import undetected_chromedriver as uc
import json

def test_cdp_interception():
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = uc.Chrome(version_main=152, options=options)
    driver.get("https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E")
    
    print("Waiting 15 seconds for page load...")
    time.sleep(15)
    
    logs = driver.get_log('performance')
    print(f"Captured {len(logs)} performance logs.")
    
    # Try to find the search response
    target_urls = []
    for entry in logs:
        log_json = json.loads(entry['message'])['message']
        method = log_json['method']
        if method == 'Network.responseReceived':
            url = log_json['params']['response']['url']
            if 'search' in url.lower() or 'flight' in url.lower() or 'api' in url.lower():
                request_id = log_json['params']['requestId']
                target_urls.append((url, request_id))
    
    print(f"Found {len(target_urls)} potential endpoints.")
    for url, req_id in target_urls:
        try:
            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
            body = res.get('body', '')
            
            # Check if this looks like a flight response
            if len(body) > 5000 and ('fare' in body.lower() or 'price' in body.lower() or 'flight' in body.lower() or 'itinerary' in body.lower()):
                print(f"Found juicy response! URL: {url} Length: {len(body)}")
                
                # Check if it's actually JSON and not just HTML
                try:
                    json_data = json.loads(body)
                    filename = f"mmt_api_response_{req_id}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(body)
                    print(f"Saved to {filename}")
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            pass
            
    driver.quit()

if __name__ == "__main__":
    test_cdp_interception()
