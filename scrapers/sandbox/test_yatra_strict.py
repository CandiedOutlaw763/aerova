import undetected_chromedriver as uc
import time
import json
import urllib.parse
from pprint import pprint

def test():
    print(f"\n--- Testing Yatra Strict ---")
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = uc.Chrome(version_main=152, options=options)
    
    driver.get("https://www.yatra.com/")
    time.sleep(10)
    
    date_str = "28/09/2026"
    encoded_date = urllib.parse.quote(date_str, safe='')
    deep_link = f"https://flight.yatra.com/air-search-ui/dom2/trigger?type=O&viewName=normal&flexi=0&noOfSegments=1&origin=DEL&originCountry=IN&destination=BOM&destinationCountry=IN&flight_depart_date={encoded_date}&ADT=1&CHD=0&INF=0&class=Economy&source=fresco-home&version=1.1"
    
    print(f"Deep link: {deep_link}")
    driver.get(deep_link)
    
    start_time = time.time()
    accumulated = set()
    urls_seen = set()
    while time.time() - start_time < 30:
        time.sleep(2)
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                log_json = json.loads(entry['message'])['message']
                if log_json['method'] == 'Network.responseReceived':
                    url = log_json['params']['response'].get('url', '')
                    if 'poll' in url or 'fare' in url:
                        urls_seen.add(url)
                        accumulated.add(log_json['params']['requestId'])
            except Exception:
                pass
        
        for req_id in list(accumulated):
            try:
                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                body = res.get('body', '')
                if len(body) > 100:
                    try:
                        parsed = json.loads(body)
                        if 'fltSchedule' in parsed:
                            print(f"!!! FOUND fltSchedule in req {req_id} !!!")
                            accumulated.remove(req_id)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                pass
                
    print(f"Target URLs seen: {urls_seen}")
    driver.quit()

if __name__ == '__main__':
    test()
