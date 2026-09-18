import undetected_chromedriver as uc
import time
import json
import requests

def capture_request_and_replay():
    print("Launching UC...")
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(version_main=152, options=options)
    driver.get("https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E")
    
    print("Waiting 20 seconds...")
    time.sleep(20)
    
    logs = driver.get_log('performance')
    
    target_url = None
    target_headers = None
    
    for entry in logs:
        try:
            log_json = json.loads(entry['message'])['message']
            method = log_json['method']
            
            if method == 'Network.requestWillBeSent':
                req = log_json['params']['request']
                url = req.get('url', '')
                if 'search-stream-dt' in url.lower():
                    target_url = url
                    target_headers = req.get('headers', {})
                    print(f"[FOUND REQUEST] URL: {target_url}")
                    break
        except:
            pass
            
    # Also get cookies
    cookies = driver.get_cookies()
    cookie_dict = {c['name']: c['value'] for c in cookies}
    
    driver.quit()

    if target_url and target_headers:
        print("\nReplaying request in Python requests...")
        # Clean up pseudo-headers which requests doesn't like
        clean_headers = {k: v for k, v in target_headers.items() if not k.startswith(':')}
        
        try:
            response = requests.get(target_url, headers=clean_headers, cookies=cookie_dict, stream=True)
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            # Read the first few chunks
            chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks.append(chunk)
                    if sum(len(c) for c in chunks) > 50000:
                        break
                        
            full_body = b''.join(chunks)
            with open("mmt_replayed_stream.bin", "wb") as f:
                f.write(full_body)
            print(f"Saved {len(full_body)} bytes to mmt_replayed_stream.bin")
            print(f"Preview: {full_body[:500].decode('utf-8', errors='ignore')}")
            
        except Exception as e:
            print("Failed to replay request:", e)
    else:
        print("Did not find target request.")

if __name__ == "__main__":
    capture_request_and_replay()
