import undetected_chromedriver as uc
import time
import json
options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
driver = uc.Chrome(version_main=152, options=options)
driver.execute_cdp_cmd('Network.enable', {'maxTotalBufferSize': 100_000_000, 'maxResourceBufferSize': 50_000_000})

driver.set_page_load_timeout(30)
try: driver.get('https://www.goindigo.in/')
except: pass
time.sleep(5)

# Dismiss cookies popup
try:
    btn = driver.find_element('xpath', "//*[contains(text(), 'Accept')]")
    btn.click()
except Exception as e:
    print('No cookie btn:', e)

try:
    driver.execute_script(
        """
        document.querySelector('button.skyplus-button--filled-primary').click();
        """
    )
except Exception as e:
    print('JS error:', e)

time.sleep(15)
driver.save_screenshot('indigo_postclick.png')
print('Current URL:', driver.current_url)

logs = driver.get_log('performance')
for entry in logs:
    log = json.loads(entry['message'])['message']
    if log['method'] == 'Network.responseReceived':
        resp = log['params']['response']
        url = resp['url']
        if 'indigo' in url and ('search' in url.lower() or 'flight' in url.lower() or 'api' in url.lower()):
            try:
                body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': log['params']['requestId']})['body']
                if len(body) > 1000:
                    mimetype = resp.get('mimeType', '')
                    print(f'URL: {url}, Size: {len(body)}, MimeType: {mimetype}')
            except Exception:
                pass
try: driver.quit()
except: pass
