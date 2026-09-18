import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI Interactivity v6...")
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
        
        # Now there should be an input field with class "form-control" or similar
        driver.execute_script("""
            let inputs = document.querySelectorAll('input');
            for(let inp of inputs) {
                let rect = inp.getBoundingClientRect();
                if(rect.width > 0 && rect.height > 0 && !inp.readOnly && !inp.disabled) {
                    inp.focus();
                    inp.value = '';
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        """)
        time.sleep(0.5)
        
        active = driver.switch_to.active_element
        for char in "DEL":
            active.send_keys(char)
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
        
        # Find the destination input
        driver.execute_script("""
            let inputs = document.querySelectorAll('input');
            for(let inp of inputs) {
                let rect = inp.getBoundingClientRect();
                if(rect.width > 0 && rect.height > 0 && !inp.readOnly && !inp.disabled && !inp.value.includes('DEL')) {
                    inp.focus();
                    inp.value = '';
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        """)
        time.sleep(0.5)
        
        active = driver.switch_to.active_element
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
        driver.save_screenshot("aix_search_before_click.png")
        
        # The search button is the large orange container. Let's find it visually via bounding boxes
        clicked = driver.execute_script("""
            let els = document.querySelectorAll('div, button, a');
            for(let el of els) {
                let rect = el.getBoundingClientRect();
                // It's usually the right-most element in the search bar
                if (rect.width > 50 && rect.height > 50 && rect.right > window.innerWidth - 300 && rect.y > 200 && rect.y < 600) {
                    let style = window.getComputedStyle(el);
                    // Check if background color is orange-ish
                    if (style.backgroundColor.includes('rgb(24') || style.backgroundColor.includes('rgb(255, 102') || style.backgroundColor.includes('rgb(255, 93')) {
                        el.click();
                        return true;
                    }
                }
            }
            
            // Backup: find SVG that represents the search arrow
            let svgs = document.querySelectorAll('svg');
            for (let svg of svgs) {
                let rect = svg.getBoundingClientRect();
                if (rect.right > window.innerWidth - 300 && rect.y > 200 && rect.y < 600) {
                    svg.parentElement.click();
                    return true;
                }
            }
            return false;
        """)
        print("Search clicked?", clicked)
        
        print("Waiting for API response...")
        start_time = time.time()
        
        found_responses = []
        
        while time.time() - start_time < 15:
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    log_json = json.loads(entry['message'])['message']
                    if log_json['method'] == 'Network.responseReceived':
                        url = log_json['params']['response'].get('url', '')
                        if 'search' in url.lower() or 'flight' in url.lower() or 'availability' in url.lower():
                            req_id = log_json['params']['requestId']
                            res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            if res.get('body') and len(res['body']) > 500:
                                found_responses.append(url)
                                if 'currencyCode' in res['body'] or 'fares' in res['body'] or 'journeys' in res['body']:
                                    print(f"\\n*** JACKPOT *** found flight data in: {url}")
                                    with open('aix_jackpot_real.json', 'w') as f:
                                        f.write(res['body'])
                                    return
                except:
                    pass
            time.sleep(1)
            
        print("\\nFound endpoints:", found_responses)
        driver.save_screenshot("aix_search_after_click.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
