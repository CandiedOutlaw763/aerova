import time
import json
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from .base_uc import UCSpider

class AirIndiaExpressSpider(UCSpider):
    name = "aix"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def extract_flights(self, origin: str, dest: str, date_str: str) -> dict:
        """
        Extract flights from Air India Express for a given route and date.
        date_str format: YYYY-MM-DD
        """
        print(f"[{self.name}] Searching flights {origin} -> {dest} on {date_str}")
        driver = self.get_driver()
        
        try:
            # Enable network interception
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
            
            # Parse target date
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 1. ORIGIN
            print(f"[{self.name}] Setting origin: {origin}")
            driver.execute_script("""
                let els = document.querySelectorAll('*');
                for(let el of els) {
                    if(el.innerText && (el.innerText.trim() === 'Bengaluru' || el.innerText.trim() === 'Flying from') && el.children.length === 0) {
                        el.click();
                        break;
                    }
                }
            """)
            time.sleep(1)
            
            # Focus input
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
                
            time.sleep(0.5)
            for char in origin:
                active.send_keys(char)
                time.sleep(0.1)
                
            time.sleep(1.5)
            
            # Click Origin from dropdown
            origin_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{origin}')]")
            clicked = False
            for el in origin_elements:
                if el.is_displayed():
                    try:
                        ActionChains(driver).move_to_element(el).click().perform()
                        clicked = True
                        break
                    except:
                        pass
            if not clicked:
                print(f"[{self.name}] WARNING: Could not click {origin} in dropdown.")
            time.sleep(1)

            # 2. DESTINATION
            print(f"[{self.name}] Setting destination: {dest}")
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
            
            driver.execute_script("""
                let inps = document.querySelectorAll('input');
                for(let inp of inps) {
                    if(!inp.readOnly && !inp.disabled && !inp.value.includes(arguments[0])) {
                        inp.focus();
                        break;
                    }
                }
            """, origin)
            time.sleep(1)
            
            active = driver.switch_to.active_element
            for char in dest:
                active.send_keys(char)
                time.sleep(0.1)
                
            time.sleep(1.5)
            
            # Click Dest from dropdown
            dest_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{dest}')]")
            clicked = False
            for el in dest_elements:
                if el.is_displayed():
                    try:
                        ActionChains(driver).move_to_element(el).click().perform()
                        clicked = True
                        break
                    except:
                        pass
            if not clicked:
                print(f"[{self.name}] WARNING: Could not click {dest} in dropdown.")
            time.sleep(1)

            # 3. DATE
            # AIX date picking is complex. If it's a nearby date, it's already in view.
            # Let's just click the departure field and find the cell containing the day.
            print(f"[{self.name}] Setting date: {date_str}")
            driver.execute_script("""
                let els = document.querySelectorAll('*');
                for(let el of els) {
                    if (el.innerText && el.innerText.includes('Departure') && el.innerText.includes('20')) {
                        el.click();
                        break;
                    }
                }
            """)
            time.sleep(1)
            
            day_str = str(target_date.day)
            driver.execute_script("""
                let cells = document.querySelectorAll('div, td, span');
                for(let cell of cells) {
                    if (cell.innerText && cell.innerText.trim() === arguments[0]) {
                        // verify it's a date cell by checking style or classes roughly
                        let style = window.getComputedStyle(cell);
                        if (cell.classList.length > 0 || cell.innerText.length <= 2) {
                             cell.id = 'target-date-cell';
                             break;
                        }
                    }
                }
            """, day_str)
            
            try:
                date_cell = driver.find_element(By.ID, 'target-date-cell')
                ActionChains(driver).move_to_element(date_cell).click().perform()
            except:
                print(f"[{self.name}] WARNING: Date cell not found. Using default date.")
            time.sleep(1)
            
            # 4. SEARCH
            print(f"[{self.name}] Submitting search...")
            driver.execute_script("""
                let els = document.querySelectorAll('div, button, a');
                for(let el of els) {
                    let rect = el.getBoundingClientRect();
                    // AIX Search button is a large orange circle/button on the right
                    if (rect.width > 40 && rect.height > 40 && rect.right > window.innerWidth - 300 && rect.y > 100 && rect.y < 600) {
                        let style = window.getComputedStyle(el);
                        if (style.backgroundColor.includes('rgb(24') || style.backgroundColor.includes('rgb(255, 102') || style.backgroundColor.includes('rgb(255, 93')) {
                            el.id = 'target-search-btn';
                            break;
                        }
                    }
                }
            """)
            
            try:
                search_btn = driver.find_element(By.ID, 'target-search-btn')
                ActionChains(driver).move_to_element(search_btn).click().perform()
            except:
                print(f"[{self.name}] Could not find Search button with ActionChains. Trying JS fallback...")
                driver.execute_script("document.getElementById('target-search-btn').click();")
            
            # Wait and extract data
            print(f"[{self.name}] Waiting for flight data in network logs...")
            start_time = time.time()
            extracted_json = None
            
            while time.time() - start_time < 20:
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        log_json = json.loads(entry['message'])['message']
                        if log_json['method'] == 'Network.responseReceived':
                            url = log_json['params']['response'].get('url', '')
                            # AIX uses graphql or specific REST endpoints for availability
                            if 'search' in url.lower() or 'availability' in url.lower() or 'graphql' in url.lower():
                                req_id = log_json['params']['requestId']
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                body = res.get('body', '')
                                if body and len(body) > 1000:
                                    if 'currencyCode' in body or 'fares' in body or 'journeys' in body or 'flightList' in body:
                                        print(f"[{self.name}] Jackpot! Intercepted data from: {url}")
                                        extracted_json = json.loads(body)
                                        break
                    except Exception as e:
                        pass
                
                if extracted_json:
                    break
                    
                time.sleep(1)
                
            if not extracted_json:
                print(f"[{self.name}] Failed to capture flight data before timeout.")
                return {"error": "Timeout or failed to intercept network data"}
                
            print(f"[{self.name}] Successfully extracted flight data.")
            return extracted_json

        except Exception as e:
            print(f"[{self.name}] Error during extraction: {e}")
            return {"error": str(e)}
        finally:
            driver.quit()

if __name__ == "__main__":
    spider = AirIndiaExpressSpider(headless=False)
    data = spider.extract_flights("DEL", "BOM", "2026-09-30")
    print("Found data keys:", data.keys() if 'error' not in data else data)
