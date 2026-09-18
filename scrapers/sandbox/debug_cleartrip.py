"""Debug script to dump ALL XHR responses from Cleartrip"""
import json
import time
import sys
import os
sys.path.insert(0, os.path.abspath('../engine'))
import undetected_chromedriver as uc
from spiders.utils import setup_cdp_limits

if __name__ == '__main__':
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = uc.Chrome(version_main=152, options=options)
    setup_cdp_limits(driver)

    url = "https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date=28/09/2026&from=DEL&to=BOM&intl=n&sd=&carrier=&page=loaded"

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
                    if 'flight/search/v2' in req_url:
                        print(f"Intercepted API URL: {req_url}")
                        try:
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            body = res.get('body', '')
                            with open('cleartrip_v2.json', 'w', encoding='utf-8') as f:
                                f.write(body)
                            print(f"Saved {len(body)} bytes to cleartrip_v2.json")
                            break
                        except Exception as e:
                            print(f"Failed to fetch body: {e}")
            except Exception:
                pass

    print(f"\nFound {len(all_xhr)} XHR responses from cleartrip:")
    for url, info in all_xhr.items():
        print(f"\n  URL: {url}")
        print(f"  ContentType: {info['ct']}")
        print(f"  Body length: {info['body_len']}")
        print(f"  Preview: {info['body_preview'][:150]}")

    driver.quit()
