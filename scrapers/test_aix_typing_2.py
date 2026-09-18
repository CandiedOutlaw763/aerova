import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing AIX UI and Dumping all JSON responses...")
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
        
        print("Clicking Search...")
        driver.execute_script("""
            let btns = document.querySelectorAll('button');
            for(let btn of btns) {
                if (btn.innerText && btn.innerText.includes('Search Flights')) {
                    btn.click();
                    break;
                }
            }
        """)
        
        print("Waiting for API response...")
        start_time = time.time()
        
        found_responses = []
        
        while time.time() - start_time < 30:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'api' in url.lower() or 'graphql' in url.lower() or 'search' in url.lower() or 'flight' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body') and len(res['body']) > 500:
                                found_responses.append({
                                    "url": url,
                                    "body_snippet": res['body'][:500]
                                })
                                # Look for typical flight data indicators
                                if 'currencyCode' in res['body'] or 'fares' in res['body'] or 'journeys' in res['body'] or 'flights' in res['body']:
                                    print(f"\\n*** JACKPOT *** found flight data in: {url}")
                                    with open('aix_jackpot.json', 'w') as f:
                                        f.write(res['body'])
                                    return
                except:
                    pass
            time.sleep(1)
            
        print("\\nAll responses captured:")
        for r in found_responses:
            print(f"- {r['url']}")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
