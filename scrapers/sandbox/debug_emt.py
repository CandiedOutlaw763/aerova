"""Debug script to dump ALL XHR responses from EaseMyTrip"""
import json
import time
import undetected_chromedriver as uc

if __name__ == '__main__':
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = uc.Chrome(version_main=152, options=options)

    url = "https://flight.easemytrip.com/FlightList/Index?srch=DEL-Any-|BOM-Any-|28/09/2026&px=1-0-0&cclass=0&cc=0&isOneway=true&tripId=1"

    print(f"Navigating to: {url}")
    driver.get(url)
    time.sleep(3)

    start = time.time()
    all_xhr = {}

    while time.time() - start < 35:
        time.sleep(2)
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                msg = json.loads(entry['message'])['message']
                if msg['method'] == 'Network.responseReceived':
                    req_url = msg['params']['response'].get('url', '')
                    req_id = msg['params']['requestId']
                    ct = msg['params']['response'].get('mimeType', '')
                    if 'easemytrip' in req_url:
                        try:
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            body = res.get('body', '')
                            if len(body) > 50:
                                all_xhr[req_url] = {'body_len': len(body), 'ct': ct, 'body_preview': body[:200]}
                        except Exception:
                            pass
            except Exception:
                pass

    print(f"\nFound {len(all_xhr)} XHR responses from easemytrip.com:")
    for url, info in all_xhr.items():
        print(f"\n  URL: {url}")
        print(f"  ContentType: {info['ct']}")
        print(f"  Body length: {info['body_len']}")
        print(f"  Preview: {info['body_preview'][:150]}")

    driver.quit()
