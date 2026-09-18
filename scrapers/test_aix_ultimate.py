import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express Ultimate...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(10)
        
        # Hide overlays
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
        
        # 1. Origin
        print("Clicking Origin...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Bengaluru' && el.children.length === 0) {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        print("Focusing and typing DEL...")
        driver.execute_script("""
            let inps = document.querySelectorAll('input');
            for(let inp of inps) {
                if(!inp.readOnly && !inp.disabled && !inp.value.includes('BOM')) {
                    inp.focus();
                    inp.value = '';
                    break;
                }
            }
        """)
        active = driver.switch_to.active_element
        for char in "DEL":
            active.send_keys(char)
            time.sleep(0.3)
        time.sleep(1)
        
        print("Clicking DEL from dropdown...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.includes('New Delhi') && el.innerText.includes('DEL') && el.children.length < 5) {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        # 2. Destination
        print("Clicking Destination...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Flying to' && el.children.length === 0) {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        print("Focusing and typing BOM...")
        driver.execute_script("""
            let inps = document.querySelectorAll('input');
            for(let inp of inps) {
                if(!inp.readOnly && !inp.disabled && !inp.value.includes('DEL')) {
                    inp.focus();
                    inp.value = '';
                    break;
                }
            }
        """)
        active = driver.switch_to.active_element
        for char in "BOM":
            active.send_keys(char)
            time.sleep(0.3)
        time.sleep(1)
        
        print("Clicking BOM from dropdown...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.includes('Mumbai') && el.innerText.includes('BOM') && el.children.length < 5) {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        # 3. Date
        print("Selecting Date...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.includes('Departure') && el.innerText.includes('Sep')) {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        driver.execute_script("""
            let cells = document.querySelectorAll('.DayPicker-Day');
            for(let cell of cells) {
                if (cell.innerText.trim() === '30' && !cell.classList.contains('DayPicker-Day--disabled')) {
                    cell.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        driver.save_screenshot("aix_ultimate_ready.png")
        
        # 4. Search
        print("Clicking Search...")
        driver.execute_script("""
            let els = document.querySelectorAll('div, button, a');
            for(let el of els) {
                let rect = el.getBoundingClientRect();
                if (rect.width > 40 && rect.height > 40 && rect.right > window.innerWidth - 300 && rect.y > 100 && rect.y < 600) {
                    let style = window.getComputedStyle(el);
                    if (style.backgroundColor.includes('rgb(24') || style.backgroundColor.includes('rgb(255, 102') || style.backgroundColor.includes('rgb(255, 93')) {
                        el.click();
                        break;
                    }
                }
            }
        """)
        
        print("Waiting for API response...")
        start_time = time.time()
        
        while time.time() - start_time < 15:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search' in url.lower() or 'availability' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body') and len(res['body']) > 500:
                                if 'currencyCode' in res['body'] or 'fares' in res['body'] or 'journeys' in res['body']:
                                    print(f"\\n*** JACKPOT *** found flight data in: {url}")
                                    with open('aix_jackpot_real.json', 'w') as f:
                                        f.write(res['body'])
                                    return
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("aix_ultimate_after_search.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
