import time
import json
import pyautogui
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express with PyAutoGUI OS-level typing...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.maximize_window()
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
        
        # Bring window to front (Windows only)
        try:
            import win32gui, win32con
            hwnd = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            win32gui.SetForegroundWindow(hwnd)
        except:
            pass
            
        time.sleep(2)
        
        # Get coordinates for Origin
        print("Locating Origin...")
        origin_rect = driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Bengaluru' && el.children.length === 0) {
                    let r = el.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }
            }
            return null;
        """)
        
        if origin_rect:
            print(f"Origin rect: {origin_rect}")
            # Add chrome offset (approx 130px for maximized window)
            # Or use driver.execute_script("return window.outerHeight - window.innerHeight") to get exact chrome height
            chrome_height = driver.execute_script("return window.outerHeight - window.innerHeight;")
            
            x = int(origin_rect['x'])
            y = int(origin_rect['y'] + chrome_height)
            
            pyautogui.click(x, y)
            time.sleep(1)
            pyautogui.write('DEL', interval=0.2)
            time.sleep(1)
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            
        # Get coordinates for Destination
        print("Locating Destination...")
        dest_rect = driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if(el.innerText && el.innerText.trim() === 'Flying to' && el.children.length === 0) {
                    let r = el.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }
            }
            return null;
        """)
        
        if dest_rect:
            print(f"Dest rect: {dest_rect}")
            chrome_height = driver.execute_script("return window.outerHeight - window.innerHeight;")
            x = int(dest_rect['x'])
            y = int(dest_rect['y'] + chrome_height)
            
            pyautogui.click(x, y)
            time.sleep(1)
            pyautogui.write('BOM', interval=0.2)
            time.sleep(1)
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            
        # Select Date
        print("Locating Date...")
        date_rect = driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.includes('Departure') && el.innerText.includes('Sep')) {
                    let r = el.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }
            }
            return null;
        """)
        
        if date_rect:
            print(f"Date rect: {date_rect}")
            chrome_height = driver.execute_script("return window.outerHeight - window.innerHeight;")
            x = int(date_rect['x'])
            y = int(date_rect['y'] + chrome_height)
            
            pyautogui.click(x, y)
            time.sleep(1)
            
            # Click day 30
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
            
        driver.save_screenshot("aix_pyauto_ready.png")
            
        # Click Search
        print("Locating Search...")
        search_rect = driver.execute_script("""
            let els = document.querySelectorAll('div, button, a');
            for(let el of els) {
                let rect = el.getBoundingClientRect();
                if (rect.width > 40 && rect.height > 40 && rect.right > window.innerWidth - 300 && rect.y > 100 && rect.y < 600) {
                    let style = window.getComputedStyle(el);
                    if (style.backgroundColor.includes('rgb(24') || style.backgroundColor.includes('rgb(255, 102') || style.backgroundColor.includes('rgb(255, 93')) {
                        return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                    }
                }
            }
            return null;
        """)
        
        if search_rect:
            print(f"Search rect: {search_rect}")
            chrome_height = driver.execute_script("return window.outerHeight - window.innerHeight;")
            x = int(search_rect['x'])
            y = int(search_rect['y'] + chrome_height)
            
            pyautogui.click(x, y)
            
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
            
        driver.save_screenshot("aix_pyauto_after_search.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
