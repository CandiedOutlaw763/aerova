import time
import json
import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=152)

driver.execute_cdp_cmd('Network.enable', {})
url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
print("Navigating to", url)
driver.get(url)
time.sleep(15)

logs = driver.get_log('performance')
urls = []
for entry in logs:
    try:
        msg = json.loads(entry['message'])['message']
        if msg['method'] == 'Network.responseReceived':
            req_url = msg['params']['response'].get('url', '')
            if 'makemytrip.com' in req_url and 'api' not in req_url and 'event-log' not in req_url:
                urls.append(req_url)
    except:
        pass

for u in sorted(set(urls)):
    print(u)

driver.quit()
