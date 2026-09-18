import time
import json
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing AIX ActionChains Click Strategy...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(15)
        
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
        
        # 1. Click Origin
        print("Clicking Origin (Bengaluru)...")
        origin_clicked = driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Bengaluru' && el.children.length === 0) {
                    el.click();
                    return true;
                }
            }
            return false;
        """)
        print(f"Origin clicked: {origin_clicked}")
        time.sleep(2)
        
        print("Focusing input and typing DEL...")
        driver.execute_script("""
            let inps = document.querySelectorAll('input');
            for(let inp of inps) {
                if(!inp.readOnly && !inp.disabled) {
                    inp.focus();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        active = driver.switch_to.active_element
        for _ in range(15):
            active.send_keys(Keys.BACKSPACE)
            time.sleep(0.05)
            
        time.sleep(1)
        for char in "DEL":
            active.send_keys(char)
            time.sleep(0.2)
            
        time.sleep(2)
        
        print("Clicking DEL from dropdown via ActionChains...")
        # Get all elements with New Delhi
        del_elements = driver.find_elements('xpath', "//*[contains(text(), 'New Delhi')]")
        for el in del_elements:
            if el.is_displayed():
                try:
                    ActionChains(driver).move_to_element(el).click().perform()
                    print("Clicked New Delhi successfully.")
                    break
                except Exception as e:
                    pass
        time.sleep(2)
        
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
        time.sleep(2)
        
        print("Focusing input and typing BOM...")
        driver.execute_script("""
            let inps = document.querySelectorAll('input');
            for(let inp of inps) {
                if(!inp.readOnly && !inp.disabled && !inp.value.includes('DEL')) {
                    inp.focus();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        active = driver.switch_to.active_element
        for char in "BOM":
            active.send_keys(char)
            time.sleep(0.2)
            
        time.sleep(2)
        
        print("Clicking BOM from dropdown via ActionChains...")
        bom_elements = driver.find_elements('xpath', "//*[contains(text(), 'Mumbai')]")
        for el in bom_elements:
            if el.is_displayed():
                try:
                    ActionChains(driver).move_to_element(el).click().perform()
                    print("Clicked Mumbai successfully.")
                    break
                except Exception as e:
                    pass
        time.sleep(2)
        
        # 3. Select Date
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
        time.sleep(2)
        driver.execute_script("""
            let cells = document.querySelectorAll('.DayPicker-Day');
            for(let cell of cells) {
                if (cell.innerText.trim() === '30' && !cell.classList.contains('DayPicker-Day--disabled')) {
                    cell.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        
        driver.save_screenshot("aix_actionchains_ready.png")
        
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
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
