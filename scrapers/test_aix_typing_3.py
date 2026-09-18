import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI Interactivity v3...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(8)
        
        # Hide sticky overlays
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
        
        print("Interacting with Origin...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.trim() === 'Bengaluru') {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        origin_input = driver.find_element(By.ID, "basic-url-origin")
        origin_input.send_keys(Keys.CONTROL, 'a')
        origin_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "DEL":
            origin_input.send_keys(char)
            time.sleep(0.3)
        time.sleep(2)
        
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
        
        print("Interacting with Destination...")
        # Since clicking DEL probably closed the dropdown, we need to click destination explicitly
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.trim() === 'Flying to') {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        # In AIX, the destination input might be basic-url-destination
        try:
            dest_input = driver.find_element(By.ID, "basic-url-destination")
        except:
            dest_input = driver.switch_to.active_element
            
        dest_input.send_keys(Keys.CONTROL, 'a')
        dest_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "BOM":
            dest_input.send_keys(char)
            time.sleep(0.3)
        time.sleep(2)
        
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
        
        print("Interacting with Date...")
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
        
        driver.save_screenshot("aix_before_search.png")
        
        print("Clicking Search...")
        # Search button is the orange circle. Let's find it by class
        found = driver.execute_script("""
            let btns = document.querySelectorAll('button');
            for(let btn of btns) {
                if (btn.className.includes('btn-flight') || btn.innerHTML.includes('flight-search')) {
                    btn.click();
                    return true;
                }
            }
            // fallback: find the orange circle button directly
            let searchDiv = document.querySelector('.flight-search-btn') || document.querySelector('.search-btn');
            if (searchDiv) {
                searchDiv.click();
                return true;
            }
            // another fallback
            let svgBtn = document.querySelector('.search-icon-wrapper button') || document.querySelector('.search-btn-wrapper button');
            if (svgBtn) {
                svgBtn.click();
                return true;
            }
            return false;
        """)
        print("Search button clicked?", found)
        
        print("Waiting for API response...")
        start_time = time.time()
        
        found_responses = []
        
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search-availability' in url.lower() or 'flightsearch' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body') and len(res['body']) > 500:
                                print(f"\\n*** JACKPOT *** found flight data in: {url}")
                                with open('aix_jackpot.json', 'w') as f:
                                    f.write(res['body'])
                                return
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("aix_after_search.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
