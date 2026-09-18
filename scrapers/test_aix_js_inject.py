import time
import json
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI with JS Injection...")
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
        
        print("Injecting Origin (DEL)...")
        driver.execute_script("""
            function setReactValue(element, value) {
                let lastValue = element.value;
                element.value = value;
                let event = new Event('input', { bubbles: true });
                event.simulated = true;
                let tracker = element._valueTracker;
                if (tracker) {
                    tracker.setValue(lastValue);
                }
                element.dispatchEvent(event);
            }
            
            // Wait, maybe we just need to click it first
            let origin_click = document.querySelector('#basic-url-origin');
            if (origin_click) {
                origin_click.click();
            }
            
            setTimeout(() => {
                let inp = document.querySelector('#basic-url-origin');
                if (inp) {
                    setReactValue(inp, 'DEL');
                    setTimeout(() => {
                        // Click New Delhi
                        let els = document.querySelectorAll('*');
                        for(let el of els) {
                            if (el.innerText && el.innerText.includes('New Delhi') && el.innerText.includes('DEL') && el.children.length < 5) {
                                el.click();
                                break;
                            }
                        }
                    }, 1000);
                }
            }, 500);
        """)
        time.sleep(3)
        
        print("Injecting Destination (BOM)...")
        driver.execute_script("""
            function setReactValue(element, value) {
                let lastValue = element.value;
                element.value = value;
                let event = new Event('input', { bubbles: true });
                event.simulated = true;
                let tracker = element._valueTracker;
                if (tracker) {
                    tracker.setValue(lastValue);
                }
                element.dispatchEvent(event);
            }
            
            let dest_click = Array.from(document.querySelectorAll('*')).find(el => el.innerText && el.innerText.trim() === 'Flying to');
            if (dest_click) {
                dest_click.click();
            }
            
            setTimeout(() => {
                // Find the input that doesn't contain 'DEL'
                let inps = document.querySelectorAll('input');
                let inp = Array.from(inps).find(i => !i.value.includes('DEL') && !i.readOnly && !i.disabled && i.type === 'text');
                if (inp) {
                    setReactValue(inp, 'BOM');
                    setTimeout(() => {
                        let els = document.querySelectorAll('*');
                        for(let el of els) {
                            if (el.innerText && el.innerText.includes('Mumbai') && el.innerText.includes('BOM') && el.children.length < 5) {
                                el.click();
                                break;
                            }
                        }
                    }, 1000);
                }
            }, 500);
        """)
        time.sleep(3)
        
        print("Selecting Date...")
        driver.execute_script("""
            let dateClick = Array.from(document.querySelectorAll('*')).find(el => el.innerText && el.innerText.includes('Departure') && el.innerText.includes('Sep'));
            if (dateClick) {
                dateClick.click();
            }
            
            setTimeout(() => {
                let cells = document.querySelectorAll('.DayPicker-Day');
                for(let cell of cells) {
                    if (cell.innerText.trim() === '30' && !cell.classList.contains('DayPicker-Day--disabled')) {
                        cell.click();
                        break;
                    }
                }
            }, 1000);
        """)
        time.sleep(3)
        
        print("Clicking Search...")
        driver.save_screenshot("aix_js_before_search.png")
        
        clicked = driver.execute_script("""
            let els = document.querySelectorAll('div, button, a');
            for(let el of els) {
                let rect = el.getBoundingClientRect();
                if (rect.width > 40 && rect.height > 40 && rect.right > window.innerWidth - 300 && rect.y > 100 && rect.y < 600) {
                    let style = window.getComputedStyle(el);
                    if (style.backgroundColor.includes('rgb(24') || style.backgroundColor.includes('rgb(255, 102') || style.backgroundColor.includes('rgb(255, 93')) {
                        el.click();
                        return true;
                    }
                }
            }
            return false;
        """)
        print("Search clicked?", clicked)
        
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
            
        driver.save_screenshot("aix_js_after_search.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
