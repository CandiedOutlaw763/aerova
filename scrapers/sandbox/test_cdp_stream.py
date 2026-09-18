import undetected_chromedriver as uc
import time
import json
import base64

def run_stream_capture():
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
    
    target_req_id = None
    target_url = None
    target_content_type = None
    
    # First, find the request ID for search-stream-dt
    for entry in logs:
        try:
            log_json = json.loads(entry['message'])['message']
            method = log_json['method']
            
            if method == 'Network.responseReceived':
                res = log_json['params']['response']
                url = res.get('url', '')
                if 'search-stream-dt' in url.lower():
                    target_req_id = log_json['params']['requestId']
                    target_url = url
                    headers = res.get('headers', {})
                    # Find Content-Type header (case insensitive)
                    for k, v in headers.items():
                        if k.lower() == 'content-type':
                            target_content_type = v
                            break
                    print(f"Found Target Response: {url}")
                    print(f"Content-Type: {target_content_type}")
                    break
        except Exception as e:
            continue
            
    if target_req_id:
        try:
            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': target_req_id})
            body = res.get('body', '')
            is_base64 = res.get('base64Encoded', False)
            
            print(f"Body length: {len(body)}, Base64 encoded: {is_base64}")
            
            if is_base64:
                raw_data = base64.b64decode(body)
                with open("mmt_stream_response.bin", "wb") as f:
                    f.write(raw_data)
                
                # Try to write as text as well just in case it's decodeable
                try:
                    with open("mmt_stream_response.txt", "w", encoding="utf-8") as f:
                        f.write(raw_data.decode('utf-8', errors='replace'))
                except:
                    pass
            else:
                with open("mmt_stream_response.txt", "w", encoding="utf-8") as f:
                    f.write(body)
                    
            print("Successfully dumped stream response.")
            
        except Exception as e:
            print("Failed to get body:", e)
    else:
        print("Did not find search-stream-dt response in logs.")

    driver.quit()

if __name__ == "__main__":
    run_stream_capture()
