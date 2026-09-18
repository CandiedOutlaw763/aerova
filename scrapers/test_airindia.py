import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Fetch Override on NewDocument...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        
        # Inject interceptor BEFORE page load
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': """
                const originalFetch = window.fetch;
                window.fetch = async function() {
                    let url = arguments[0];
                    let options = arguments[1];
                    
                    if (typeof url === 'string' && url.includes('api') && url.includes('flight') && options && options.body) {
                        try {
                            console.log("Air India Fetch Payload before:", options.body);
                            let body = JSON.parse(options.body);
                            // We don't modify it yet, we just want to see it!
                            // arguments[1] = options;
                        } catch(e) {
                            console.error("Fetch intercept error", e);
                        }
                    }
                    return originalFetch.apply(this, arguments);
                };
                
                const originalXHR = window.XMLHttpRequest.prototype.send;
                window.XMLHttpRequest.prototype.send = function(body) {
                    if (this._url && this._url.includes('api') && this._url.includes('flight') && body) {
                        try {
                            console.log("Air India XHR Payload:", body);
                        } catch(e) { }
                    }
                    return originalXHR.call(this, body);
                };
                
                const originalOpen = window.XMLHttpRequest.prototype.open;
                window.XMLHttpRequest.prototype.open = function(method, url) {
                    this._url = url;
                    return originalOpen.apply(this, arguments);
                };
            """
        })
        
        print("Navigating to Air India...")
        driver.get("https://www.airindia.com/")
        time.sleep(8)
        
        print("Waiting for page load...")
        driver.save_screenshot("airindia_home.png")
        
        print("Accepting cookies...")
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); });")
        except:
            pass
            
        time.sleep(1)
        
        print("Checking for iframes...")
        iframes = driver.execute_script("""
            let frames = document.querySelectorAll('iframe');
            let data = [];
            for (let f of frames) {
                data.push({src: f.src, id: f.id, name: f.name});
            }
            return data;
        """)
        print("Iframes:", json.dumps(iframes, indent=2))
        
        print("Finding input#From in all frames via JS...")
        res = driver.execute_script("""
            let el = document.querySelector('input#From');
            return el ? el.outerHTML : 'NOT_FOUND';
        """)
        print("Input#From in main frame:", res)
        
        print("Waiting for response...")
        start_time = time.time()
        success = False
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'flight' in url.lower() and 'search' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body'):
                                print("\nSUCCESS!")
                                print(url)
                                print(res['body'][:500])
                                success = True
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("airindia_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
