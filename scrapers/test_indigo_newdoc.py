import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo Fetch Override on NewDocument...")
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
                    
                    if (typeof url === 'string' && url.includes('v2/flight/search') && options && options.body) {
                        try {
                            let body = JSON.parse(options.body);
                            body.criteria[0].dates.beginDate = "2026-09-30";
                            body.criteria[0].stations.originStationCodes = ["DEL"];
                            body.criteria[0].stations.destinationStationCodes = ["BOM"];
                            options.body = JSON.stringify(body);
                            arguments[1] = options;
                            console.log("Fetch payload injected successfully!");
                        } catch(e) {
                            console.error("Fetch intercept error", e);
                        }
                    }
                    return originalFetch.apply(this, arguments);
                };
                
                const originalXHR = window.XMLHttpRequest.prototype.send;
                window.XMLHttpRequest.prototype.send = function(body) {
                    if (this._url && this._url.includes('v2/flight/search') && body) {
                        try {
                            let b = JSON.parse(body);
                            b.criteria[0].dates.beginDate = "2026-09-30";
                            b.criteria[0].stations.originStationCodes = ["DEL"];
                            b.criteria[0].stations.destinationStationCodes = ["BOM"];
                            body = JSON.stringify(b);
                            console.log("XHR payload injected successfully!");
                        } catch(e) {
                            console.error("XHR intercept error", e);
                        }
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
        
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
        # Hide any fixed elements that might block clicks
        driver.execute_script("""
            document.querySelectorAll('*').forEach(el => {
                try {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.display = 'none';
                    }
                } catch(e) {}
            });
        """)
        time.sleep(1)
        
        print("Interacting with Origin...")
        from_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__from input')
        driver.execute_script("arguments[0].click();", from_input)
        time.sleep(1)
        from_input.send_keys(Keys.CONTROL, 'a')
        from_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        from_input.send_keys("DEL")
        time.sleep(1.5)
        driver.execute_script("let items = document.querySelectorAll('ul.MuiList-root li'); if(items.length > 0) items[0].click();")
        time.sleep(1)
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        driver.execute_script("arguments[0].click();", to_input)
        time.sleep(1)
        to_input.send_keys(Keys.CONTROL, 'a')
        to_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        to_input.send_keys("BOM")
        time.sleep(1.5)
        driver.execute_script("let items = document.querySelectorAll('ul.MuiList-root li'); if(items.length > 0) items[0].click();")
        time.sleep(1)
        
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        print("Clicking Search...")
        search_btn = driver.find_element(By.CSS_SELECTOR, 'button.skyplus-button--filled')
        driver.execute_script("arguments[0].click();", search_btn)
        
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
                        if 'flight' in url.lower() and 'search' in url.lower() and 'v2' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body'):
                                print("\nSUCCESS!")
                                print(res['body'][:500])
                                success = True
                                return
                except:
                    pass
            time.sleep(1)
            
        if not success:
            print("Failed to capture response.")
            driver.save_screenshot("indigo_newdoc_fail.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
