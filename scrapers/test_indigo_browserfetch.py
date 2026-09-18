import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo browser fetch...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
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
        
        start = time.time()
        while time.time() - start < 5:
            res = driver.execute_script("""
                let items = document.querySelectorAll('ul.MuiList-root li');
                for(let i=0; i<items.length; i++) {
                    if(items[i].innerText.includes('DEL')) {
                        items[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if res: break
            time.sleep(0.5)
        time.sleep(1)
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        driver.execute_script("arguments[0].click();", to_input)
        time.sleep(1)
        to_input.send_keys(Keys.CONTROL, 'a')
        to_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        to_input.send_keys("BOM")
        
        start = time.time()
        while time.time() - start < 5:
            res = driver.execute_script("""
                let items = document.querySelectorAll('ul.MuiList-root li');
                for(let i=0; i<items.length; i++) {
                    if(items[i].innerText.includes('BOM')) {
                        items[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if res: break
            time.sleep(0.5)
        time.sleep(1)
        
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        
        print("Clicking Search...")
        search_btn = driver.find_element(By.CSS_SELECTOR, 'button.skyplus-button--filled')
        driver.execute_script("arguments[0].click();", search_btn)
        
        print("Waiting for headers...")
        start_time = time.time()
        api_headers = None
        
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.requestWillBeSent':
                        req_url = log_json['params']['request'].get('url', '')
                        if 'v2/flight/search' in req_url:
                            api_headers = log_json['params']['request']['headers']
                            break
                except:
                    pass
            if api_headers:
                break
            time.sleep(1)
            
        if not api_headers:
            print("Failed to capture headers.")
            return
            
        print("Making in-browser fetch...")
        payload = {
            "codes": {"currency": "INR", "promotionCode": ""},
            "criteria": [
                {
                    "dates": {"beginDate": "2026-09-30"},
                    "flightFilters": {"type": "All"},
                    "stations": {"originStationCodes": ["DEL"], "destinationStationCodes": ["BOM"]}
                }
            ],
            "passengers": {"residentCountry": "IN", "types": [{"count": 1, "discountCode": "", "type": "ADT"}]},
            "taxesAndFees": "TaxesAndFees",
            "tripCriteria": "oneWay",
            "isRedeemTransaction": False
        }
        
        clean_headers = {}
        for k, v in api_headers.items():
            if not k.startswith(':'):
                clean_headers[k] = v
                
        # Send fetch in browser!
        response_json = driver.execute_async_script("""
            var callback = arguments[arguments.length - 1];
            var url = 'https://api-prod-flight-skyplus6e.goindigo.in/v2/flight/search';
            var payload = arguments[0];
            var headers = arguments[1];
            
            fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            }).then(r => r.text()).then(t => callback(t)).catch(e => callback("ERROR: " + e.toString()));
        """, payload, clean_headers)
        
        print("Response received from in-browser fetch:")
        print(response_json[:500])
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
