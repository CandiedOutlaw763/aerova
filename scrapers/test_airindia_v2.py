import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Angular component click...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        
        print("Navigating to Air India...")
        driver.get("https://www.airindia.com/")
        time.sleep(8)
        
        print("Accepting cookies...")
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); });")
        except:
            pass
        time.sleep(1)
        
        print("Clicking 'One Way' radio button...")
        driver.execute_script("""
            let inputs = document.querySelectorAll('input[type="radio"]');
            for(let i of inputs) {
                if(i.value === 'one-way' || i.nextSibling && i.nextSibling.textContent && i.nextSibling.textContent.includes('One Way')) {
                    i.click();
                    break;
                }
            }
        """)
        time.sleep(0.5)
        
        print("Clicking FROM field via aria-label...")
        driver.execute_script("""
            let el = document.querySelector('[aria-label="Select origin airport"]');
            if(el) el.click();
        """)
        time.sleep(1.5)
        
        print("Taking screenshot after FROM click...")
        driver.save_screenshot("ai_from_clicked.png")
        
        print("Dumping active element + visible inputs...")
        info = driver.execute_script("""
            let active = document.activeElement;
            let inputs = document.querySelectorAll('input[type="text"]:not([type="hidden"])');
            let visibleInputs = [];
            inputs.forEach(i => {
                let style = window.getComputedStyle(i);
                if(style.display !== 'none' && style.visibility !== 'hidden' && i.offsetWidth > 0) {
                    visibleInputs.push({
                        id: i.id, 
                        placeholder: i.placeholder, 
                        name: i.name, 
                        class: i.className.substring(0, 60),
                        value: i.value
                    });
                }
            });
            return {
                activeTag: active.tagName,
                activeClass: active.className ? active.className.substring(0, 80) : '',
                visibleInputs: visibleInputs
            };
        """)
        print("Active element:", json.dumps(info, indent=2))
        
        print("Typing DEL into active element...")
        active = driver.switch_to.active_element
        active.send_keys("DEL")
        time.sleep(2)
        driver.save_screenshot("ai_del_typed.png")
        
        print("Clicking first dropdown item...")
        driver.execute_script("""
            let items = document.querySelectorAll('.dropdown-item, .ac-suggestion, li[role="option"], .airport-suggestion, .suggestion-item');
            if(items.length > 0) items[0].click();
        """)
        time.sleep(1)
        
        print("Clicking TO field...")
        driver.execute_script("""
            let el = document.querySelector('[aria-label="Select destination airport"]');
            if(el) el.click();
        """)
        time.sleep(1.5)
        
        active2 = driver.switch_to.active_element
        active2.send_keys("BOM")
        time.sleep(2)
        driver.save_screenshot("ai_bom_typed.png")
        
        print("Clicking first dropdown item for BOM...")
        driver.execute_script("""
            let items = document.querySelectorAll('.dropdown-item, .ac-suggestion, li[role="option"], .airport-suggestion, .suggestion-item');
            if(items.length > 0) items[0].click();
        """)
        time.sleep(1)
        
        driver.save_screenshot("ai_after_bom.png")
        
        print("Clicking Search...")
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Search')) b.click(); });")
        
        print("Waiting for API response...")
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
            driver.save_screenshot("ai_final.png")
            
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
