import undetected_chromedriver as uc
import time
import json
import urllib.parse

def test_yatra():
    print(f"\n--- Testing Yatra ---")
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Overriding get_driver since we need specific options
    driver = uc.Chrome(version_main=152, options=options)
    
    print("Navigating to Yatra homepage to bypass Akamai...")
    driver.get("https://www.yatra.com/")
    time.sleep(10)
    
    date_str = "28/09/2026"
    encoded_date = urllib.parse.quote(date_str, safe='')
    
    deep_link = f"https://flight.yatra.com/air-search-ui/dom2/trigger?type=O&viewName=normal&flexi=0&noOfSegments=1&origin=DEL&originCountry=IN&destination=BOM&destinationCountry=IN&flight_depart_date={encoded_date}&ADT=1&CHD=0&INF=0&class=Economy&source=fresco-home&version=1.1"
    
    print(f"Executing Deep Link: {deep_link}")
    driver.get(deep_link)
    
    print("Waiting 15 seconds for page load...")
    time.sleep(15)
    
    driver.save_screenshot('yatra_debug.png')
    print("Saved screenshot to yatra_debug.png")
    
    with open('yatra_debug.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
        
    logs = driver.get_log('performance')
    print(f"Captured {len(logs)} performance logs.")
    
    target_urls = []
    for entry in logs:
        try:
            log_json = json.loads(entry['message'])['message']
            method = log_json['method']
            
            if method == 'Network.responseReceived':
                res_url = log_json['params']['response'].get('url', '')
                # Don't filter, capture everything
                request_id = log_json['params']['requestId']
                target_urls.append((res_url, request_id))
        except:
            pass
            
    found_json = False
    all_json = {}
    for res_url, req_id in target_urls:
        try:
            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
            body = res.get('body', '')
            if len(body) > 1000:
                try:
                    parsed = json.loads(body)
                    all_json[res_url] = parsed
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            pass
            
    if all_json:
        with open('yatra_parsed.json', 'w', encoding='utf-8') as f:
            json.dump(all_json, f, indent=2)
        print(f"[SUCCESS] Dumped {len(all_json)} JSON responses.")
    else:
        print(f"[FAIL] Could not find discrete JSON XHR for Yatra.")
            
    if not found_json:
        print(f"[FAIL] Could not find discrete JSON XHR for Yatra.")
        
    driver.quit()

if __name__ == "__main__":
    test_yatra()
