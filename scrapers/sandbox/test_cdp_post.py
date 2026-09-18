import undetected_chromedriver as uc
import time
import json

def run_cdp_requests():
    print("Launching UC...")
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(version_main=152, options=options)
    driver.get("https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E")
    
    print("Waiting 20 seconds for page to load and fetch flights...")
    time.sleep(20)
    
    logs = driver.get_log('performance')
    
    print(f"Captured {len(logs)} performance logs.")
    
    post_requests = []
    
    for entry in logs:
        log_json = json.loads(entry['message'])['message']
        method = log_json['method']
        
        if method == 'Network.requestWillBeSent':
            req = log_json['params']['request']
            req_method = req.get('method')
            url = req.get('url')
            
            if req_method == 'POST' and ('flight' in url.lower() or 'search' in url.lower() or 'api' in url.lower()):
                post_data = req.get('postData', '')
                if post_data:
                    post_requests.append({
                        'url': url,
                        'postData': post_data,
                        'headers': req.get('headers', {})
                    })

    print(f"Found {len(post_requests)} interesting POST requests.")
    for i, req in enumerate(post_requests):
        print(f"\n--- Request {i+1} ---")
        print(f"URL: {req['url']}")
        print(f"Payload Preview: {req['postData'][:200]}")
        with open(f"mmt_post_{i}.json", "w", encoding="utf-8") as f:
            json.dump(req, f, indent=2)

    driver.quit()

if __name__ == "__main__":
    run_cdp_requests()
