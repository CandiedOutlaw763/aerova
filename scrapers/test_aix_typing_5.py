import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI with precise coordinate clicks...")
    spider = UCSpider()
    driver = spider.get_driver()
    actions = ActionChains(driver)
    
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
        
        # Click Origin
        origin_input = driver.find_element(By.ID, "basic-url-origin")
        actions.move_to_element(origin_input).click().perform()
        time.sleep(1)
        
        # Clear and Type Origin
        origin_input.send_keys(Keys.CONTROL, 'a')
        origin_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "DEL":
            origin_input.send_keys(char)
            time.sleep(0.3)
        time.sleep(2)
        
        # Click DEL
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
        
        # The destination input doesn't have an ID. We will click the text "Flying to"
        # and then send keys to the active element.
        print("Clicking 'Flying to' via ActionChains...")
        success = driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.trim() === 'Flying to' && el.children.length === 0) {
                    let rect = el.getBoundingClientRect();
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                }
            }
            return null;
        """)
        if success:
            print(f"Clicking at {success['x']}, {success['y']}")
            actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), success['x'], success['y']).click().perform()
            time.sleep(1)
            
            active = driver.switch_to.active_element
            active.send_keys(Keys.CONTROL, 'a')
            active.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            for char in "BOM":
                active.send_keys(char)
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
        else:
            print("Could not find 'Flying to'")
            
        print("Selecting date...")
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
        
        driver.save_screenshot("aix_ready_for_search.png")
        
        print("Clicking Search...")
        # Search button is the large orange button on the right
        search_coord = driver.execute_script("""
            // Find all divs. The search button is usually a very wide div on the right.
            let rects = [];
            let els = document.querySelectorAll('div, button');
            for(let el of els) {
                let rect = el.getBoundingClientRect();
                if (rect.width > 50 && rect.height > 50 && rect.right > window.innerWidth - 250 && rect.y > 250 && rect.y < 500) {
                    // Check if it's mostly orange
                    let style = window.getComputedStyle(el);
                    if (style.backgroundColor.includes('rgb(255') || style.backgroundColor.includes('rgb(249')) {
                        return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                    }
                }
            }
            // fallback: find the button with specific class
            let btn = document.querySelector('.flight-search-btn');
            if (btn) {
                let rect = btn.getBoundingClientRect();
                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
            }
            return null;
        """)
        
        if search_coord:
            print(f"Clicking Search at {search_coord['x']}, {search_coord['y']}")
            actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, 'body'), search_coord['x'], search_coord['y']).click().perform()
        else:
            print("Could not find Search button coordinates!")
            
        print("Waiting for API response...")
        start_time = time.time()
        
        while time.time() - start_time < 20:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search-availability' in url.lower() or 'search' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body') and len(res['body']) > 500:
                                if 'currencyCode' in res['body'] or 'fares' in res['body'] or 'journeys' in res['body'] or 'flights' in res['body']:
                                    print(f"\\n*** JACKPOT *** found flight data in: {url}")
                                    with open('aix_jackpot_real.json', 'w') as f:
                                        f.write(res['body'])
                                    return
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("aix_after_search3.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
