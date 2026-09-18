import json
import time
from selenium.webdriver.common.by import By
from engine.spiders.base_uc import UCSpider

def run():
    print("Capturing IndiGo Headers with Split Setters...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(10)
        
        try:
            driver.execute_script("document.querySelectorAll('.close').forEach(el => el.click())")
        except:
            pass
            
        print("Setting Origin...")
        driver.execute_script("""
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            const fromInput = document.querySelector('div.search-widget-form-body__from input');
            nativeSetter.call(fromInput, "DEL");
            fromInput.dispatchEvent(new Event('input', { bubbles: true }));
        """)
        
        time.sleep(2)
        print("Setting Destination...")
        driver.execute_script("""
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            const toInput = document.querySelector('div.search-widget-form-body__to input');
            nativeSetter.call(toInput, "BOM");
            toInput.dispatchEvent(new Event('input', { bubbles: true }));
        """)
        
        time.sleep(2)
        print("Clicking Search...")
        driver.execute_script("document.querySelector('button.skyplus-button--filled').click()")
        
        print("Waiting for network requests...")
        start_time = time.time()
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.requestWillBeSent':
                        req = log_json['params']['request']
                        url = req.get('url', '')
                        if 'flight' in url.lower() and 'search' in url.lower() and req.get('method') == 'POST':
                            print(f"\nFOUND SEARCH REQUEST: {url}")
                            print("HEADERS:")
                            for k, v in req.get('headers', {}).items():
                                print(f"{k}: {v}")
                            return
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("indigo_debug_screen3.png")
        print("Failed to find request. Saved screenshot.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
