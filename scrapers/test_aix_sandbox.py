import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(10)
        
        driver.save_screenshot("aix_home.png")
        
        # Log network requests to see if any APIs are called during load
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                log_json = json.loads(entry['message'])['message']
                if log_json['method'] == 'Network.requestWillBeSent':
                    url = log_json['params']['request']['url']
                    if 'api' in url.lower() or 'search' in url.lower() or 'flight' in url.lower():
                        print("Found interesting URL:", url)
            except:
                pass
                
        # Dump input fields
        inputs = driver.execute_script("""
            let results = [];
            let els = document.querySelectorAll('input, button');
            for(let el of els) {
                if (el.className || el.id || el.placeholder || el.innerText) {
                    results.push({
                        tag: el.tagName,
                        type: el.type || '',
                        id: el.id || '',
                        class: el.className || '',
                        placeholder: el.placeholder || '',
                        text: el.innerText.trim()
                    });
                }
            }
            return results;
        """)
        
        print("\nInput fields on page:")
        print(json.dumps(inputs, indent=2))
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
