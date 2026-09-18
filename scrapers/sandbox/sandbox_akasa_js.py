import sys
import os
import json
import time
import undetected_chromedriver as uc

def run():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = uc.Chrome(version_main=152, options=options)
    
    try:
        print("Navigating to Akasa...")
        driver.get("https://www.akasaair.com/")
        time.sleep(8)
        
        # Accept cookies
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(el => { if(el.innerText.includes('Accept')) el.click() })")
            time.sleep(1)
        except:
            pass
            
        print("Injecting JS automation...")
        automation_script = """
        async function runAutomation() {
            function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
            
            // Origin
            let inputs = Array.from(document.querySelectorAll('input'));
            let origin = inputs.find(i => i.placeholder && i.placeholder.includes('From'));
            if(origin) {
                origin.click();
                await sleep(1000);
                origin.value = 'DEL';
                origin.dispatchEvent(new Event('input', {bubbles: true}));
                await sleep(1000);
                // Try to find DEL in dropdown
                let items = Array.from(document.querySelectorAll('div')).filter(d => d.innerText && d.innerText.includes('New Delhi') && d.innerText.includes('DEL'));
                if(items.length > 0) items[items.length-1].click();
            }
            await sleep(2000);
            
            // Destination
            inputs = Array.from(document.querySelectorAll('input'));
            let dest = inputs.find(i => i.placeholder && i.placeholder.includes('To'));
            if(dest) {
                dest.click();
                await sleep(1000);
                dest.value = 'BOM';
                dest.dispatchEvent(new Event('input', {bubbles: true}));
                await sleep(1000);
                let items = Array.from(document.querySelectorAll('div')).filter(d => d.innerText && d.innerText.includes('Mumbai') && d.innerText.includes('BOM'));
                if(items.length > 0) items[items.length-1].click();
            }
            await sleep(2000);
            
            // Date
            inputs = Array.from(document.querySelectorAll('input'));
            let date = inputs.find(i => i.placeholder && (i.placeholder.includes('Date') || i.placeholder.includes('Departure')));
            if(date) {
                date.click();
                await sleep(1000);
                let days = Array.from(document.querySelectorAll('td:not(.p-disabled) span'));
                if(days.length > 10) days[10].click();
                else if (days.length > 0) days[0].click();
            }
            await sleep(2000);
            
            // Search
            let buttons = Array.from(document.querySelectorAll('button'));
            let search = buttons.find(b => b.innerText && b.innerText.includes('Search Flights'));
            if(search) search.click();
        }
        runAutomation();
        """
        driver.execute_script(automation_script)
        
        print("Waiting for response...")
        body_json = None
        start_time = time.time()
        while time.time() - start_time < 30 and not body_json:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if ('api/nsk' in url.lower() or 'search' in url.lower() or 'flight' in url.lower()) and 'storyblok' not in url.lower() and 'suggest' not in url.lower():
                            target_req_id = log_json['params']['requestId']
                            try:
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': target_req_id})
                                if res.get('body') and ('"fare"' in res['body'] or '"journey"' in res['body'] or '"amount"' in res['body'] or '"flights"' in res['body']):
                                    body_json = res['body']
                                    print(f"Captured JSON from {url}")
                                    break
                            except:
                                pass
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("akasa_js_final.png")
        if body_json:
            with open("akasa_payload.json", "w", encoding="utf-8") as f:
                f.write(body_json)
            print("Successfully saved akasa_payload.json")
        else:
            print("Failed to capture payload.")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
