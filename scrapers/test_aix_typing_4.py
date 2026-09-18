import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI with precise DOM traversal...")
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
        
        # We know there's a div containing "Bengaluru".
        # We can find all elements and click the one that holds "Bengaluru"
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
        
        # Now find the active input
        active = driver.switch_to.active_element
        active.send_keys(Keys.CONTROL, 'a')
        active.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "DEL":
            active.send_keys(char)
            time.sleep(0.3)
        time.sleep(2)
        
        # Select DEL from dropdown
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.includes('New Delhi') && el.innerText.includes('DEL') && el.children.length < 5) {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        
        # Now destination. After selecting origin, the destination input might automatically become active.
        # Let's type directly if it is.
        active = driver.switch_to.active_element
        if active.tag_name == 'input':
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
            time.sleep(2)
        else:
            print("Destination input was not automatically focused. Let's find 'Flying to'")
            # ... we'll just log this for now
        
        # Date selection
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
        time.sleep(2)
        
        driver.save_screenshot("aix_ready_to_search.png")
        
        # Find the Search button. It's the only button with type="submit" usually, or an image button.
        # It's an orange div next to the search widget.
        driver.execute_script("""
            let els = document.querySelectorAll('button, .flight-search-btn, .search-btn');
            for(let el of els) {
                // The search button is usually a generic button in a specific container
                if (el.className && (el.className.includes('flight-search-btn') || el.className.includes('search-btn'))) {
                    el.click();
                    return;
                }
            }
            
            // Backup: find SVG arrow in a button
            let svgs = document.querySelectorAll('svg');
            for(let svg of svgs) {
                let parent = svg.parentElement;
                while (parent && parent.tagName !== 'BUTTON') {
                    parent = parent.parentElement;
                }
                if (parent) {
                    // It's a button containing an SVG. Let's see if it's the search button
                    let rect = parent.getBoundingClientRect();
                    if (rect.width > 30 && rect.height > 30 && rect.right > document.body.clientWidth - 400) {
                        parent.click();
                        return;
                    }
                }
            }
        """)
        
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
                                found_responses.append({
                                    "url": url,
                                    "body_snippet": res['body'][:500]
                                })
                                if 'currencyCode' in res['body'] or 'fares' in res['body'] or 'journeys' in res['body'] or 'flights' in res['body']:
                                    print(f"\\n*** JACKPOT *** found flight data in: {url}")
                                    with open('aix_jackpot_real.json', 'w') as f:
                                        f.write(res['body'])
                                    return
                except:
                    pass
            time.sleep(1)
            
        driver.save_screenshot("aix_after_search2.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
