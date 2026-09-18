import time
import json
from engine.spiders.base_uc import UCSpider

def run():
    print("Extracting Subscription Key from AIX...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(5)
        
        # Check Local Storage and Session Storage
        ls = driver.execute_script("return window.localStorage;")
        ss = driver.execute_script("return window.sessionStorage;")
        
        print("Local Storage Keys:")
        for k, v in ls.items():
            if 'key' in k.lower() or 'token' in k.lower() or len(v) > 20:
                print(f"  {k}: {v[:50]}...")
                
        print("\\nSession Storage Keys:")
        for k, v in ss.items():
            if 'key' in k.lower() or 'token' in k.lower() or len(v) > 20:
                print(f"  {k}: {v[:50]}...")
                
        # Also let's check network logs to see if we can find the header
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_script("fetch('https://api.airindiaexpress.com/b2c-flightsearch/v1/countries').then(r => r.json())")
        time.sleep(2)
        
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                log_json = json.loads(entry['message'])['message']
                if log_json['method'] == 'Network.requestWillBeSent':
                    headers = log_json['params']['request']['headers']
                    for h, val in headers.items():
                        if 'ocp-apim-subscription-key' in h.lower() or 'authorization' in h.lower() or 'key' in h.lower():
                            print(f"Found interesting header: {h}: {val}")
            except:
                pass
                
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
