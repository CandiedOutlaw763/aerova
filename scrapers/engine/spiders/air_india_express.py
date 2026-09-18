"""
Air India Express Spider — Uses UC browser to load the page and intercept
the REST API response from their Navitaire-based booking system.

AIX fires a POST to:
  https://book.airindiaexpress.com/api/FlightAvailability/Search (or similar)
We navigate to the website, let the page generate session tokens, then make
the API call directly via JS (fetch) to avoid bot-detection.
"""
import time
import json
import re
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from .base_uc import UCSpider


class Spider(UCSpider):
    name = "Air India Express"

    AIRLINE_MAP = {
        'IX': 'Air India Express',
        'I5': 'Air India Express',
    }

    def _parse_availability(self, data: dict, origin: str, destination: str,
                             advance_window: str, fare_class: str) -> List[Dict]:
        flights = []
        try:
            # Navitaire response structure
            journeys = (
                data.get('journeys', []) or
                data.get('data', {}).get('journeys', []) or
                data.get('scheduleResponse', {}).get('journeys', []) or
                []
            )
            for j in journeys:
                # MoSPI Strict Standard: Non-stop only
                journey_str = json.dumps(j).lower()
                if '1 stop' in journey_str or '2 stop' in journey_str or 'layover' in journey_str:
                    continue
                    
                segments = j.get('segments', [])
                if len(segments) > 1:
                    continue
                    
                for seg in segments:
                    fares = seg.get('fares', [])
                    for fare in fares:
                        pax_fares = fare.get('passengerFares', [])
                        for pf in pax_fares:
                            total = pf.get('fareAmount', pf.get('totalFare', 0))
                            taxes = sum(
                                sc.get('amount', 0)
                                for sc in pf.get('serviceCharges', [])
                                if sc.get('type', '').lower() in ('tax', 'travelfee', 'fee')
                            )
                            base = total - taxes
                            if total > 0:
                                flights.append({
                                    'origin': origin,
                                    'destination': destination,
                                    'carrier': 'Air India Express',
                                    'advance_window': advance_window,
                                    'fare_class': fare_class,
                                    'base_fare': round(base, 2),
                                    'taxes': round(taxes, 2),
                                    'total_fare': round(total, 2),
                                })
        except Exception as e:
            print(f"[{self.name}] Parse error: {e}")
        return flights

    def _scrape_dom(self, html: str, origin: str, destination: str, advance_window: str, fare_class: str) -> List[Dict]:
        flights = []
        try:
            # Generic heuristic DOM scraping for AIX
            price_pattern = re.compile(r'₹\s*([\d,]+)')
            prices_raw = price_pattern.findall(html)
            prices = sorted(set(int(p.replace(',', '')) for p in prices_raw if 3000 < int(p.replace(',', '')) < 50000))

            if prices:
                for p in prices[:10]:
                    flights.append({
                        'carrier': 'Air India Express',
                        'base_fare': 0, 'taxes': 0, 'total_fare': p,
                        'origin': origin, 'destination': destination,
                        'advance_window': advance_window, 'fare_class': fare_class
                    })
        except Exception as e:
            print(f"[{self.name}] DOM scrape error: {e}")
        return flights

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        print(f"[{self.name}] Searching flights {origin} -> {destination} on {date_str}")
        flights = []
        driver = self.get_driver()

        try:
            driver.execute_cdp_cmd('Network.enable', {})

            # Parse date → YYYY-MM-DD
            try:
                if '/' in date_str:
                    from datetime import datetime
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                elif len(date_str.split('-')[0]) == 4:
                    from datetime import datetime
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    from datetime import datetime
                    dt = datetime.strptime(date_str, "%d-%b-%Y")
            except Exception:
                from datetime import datetime
                dt = datetime.now()
            date_iso = dt.strftime("%Y-%m-%d")

            print(f"[{self.name}] Loading AIX homepage for Native UI automation...")
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
            print(f"[{self.name}] Entering Origin {origin}...")
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
            
            inps = driver.execute_script("""
                return Array.from(document.querySelectorAll('input')).filter(el => {
                    try {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && el.getBoundingClientRect().width > 0 && !el.readOnly;
                    } catch(e) { return false; }
                });
            """)
            if inps:
                try:
                    inps[0].click()
                    time.sleep(0.5)
                    inps[0].send_keys(Keys.CONTROL, 'a')
                    inps[0].send_keys(Keys.BACKSPACE)
                    time.sleep(0.5)
                    inps[0].send_keys(origin)
                    time.sleep(2)
                    
                    # Explicitly click the dropdown item!
                    driver.execute_script(f"""
                        let options = document.querySelectorAll('*');
                        for(let opt of options) {{
                            if(opt.innerText && opt.innerText.includes('{origin}') && opt.innerText.length < 100 && opt.children.length === 0) {{
                                opt.click();
                                break;
                            }}
                        }}
                    """)
                except Exception as e:
                    print(f"[{self.name}] Origin input error: {e}")
            time.sleep(1)
            
            # 2. Destination
            print(f"[{self.name}] Entering Destination {destination}...")
            driver.execute_script("""
                let els = document.querySelectorAll('*');
                for(let el of els) {
                    if(el.innerText && (el.innerText.trim() === 'Flying to' || el.innerText.trim() === 'Destination') && el.children.length === 0) {
                        el.click();
                        break;
                    }
                }
            """)
            time.sleep(1)
            
            inps = driver.execute_script("""
                return Array.from(document.querySelectorAll('input')).filter(el => {
                    try {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && el.getBoundingClientRect().width > 0 && !el.readOnly;
                    } catch(e) { return false; }
                });
            """)
            # The destination input might be the second one on the page, or the first one if the origin one is hidden
            if inps:
                target_inp = inps[-1] # Usually the last active input is the one we want
                try:
                    target_inp.click()
                    time.sleep(0.5)
                    target_inp.send_keys(Keys.CONTROL, 'a')
                    target_inp.send_keys(Keys.BACKSPACE)
                    time.sleep(0.5)
                    target_inp.send_keys(destination)
                    time.sleep(2)
                    
                    # Explicitly click the dropdown item!
                    driver.execute_script(f"""
                        let options = document.querySelectorAll('*');
                        for(let opt of options) {{
                            if(opt.innerText && opt.innerText.includes('{destination}') && opt.innerText.length < 100 && opt.children.length === 0) {{
                                opt.click();
                                break;
                            }}
                        }}
                    """)
                except Exception as e:
                    print(f"[{self.name}] Destination input error: {e}")
            time.sleep(1)
            
            # 3. Date
            print(f"[{self.name}] Selecting Date...")
            driver.execute_script("""
                let els = document.querySelectorAll('*');
                for(let el of els) {
                    if (el.innerText && (el.innerText.includes('Departure') || el.innerText.includes('Depart')) && (el.innerText.includes('202') || el.innerText.includes('Jan') || el.innerText.includes('Feb') || el.innerText.includes('Mar') || el.innerText.includes('Apr') || el.innerText.includes('May') || el.innerText.includes('Jun') || el.innerText.includes('Jul') || el.innerText.includes('Aug') || el.innerText.includes('Sep') || el.innerText.includes('Oct') || el.innerText.includes('Nov') || el.innerText.includes('Dec'))) {
                        el.click();
                        break;
                    }
                }
            """)
            time.sleep(1)
            
            target_day = str(dt.day)
            driver.execute_script(f"""
                let cells = document.querySelectorAll('.DayPicker-Day');
                for(let cell of cells) {{
                    if (cell.innerText.trim() === '{target_day}' && !cell.classList.contains('DayPicker-Day--disabled')) {{
                        cell.click();
                        break;
                    }}
                }}
            """)
            time.sleep(1)
            
            # 4. Search
            print(f"[{self.name}] Clicking Search...")
            driver.execute_script("""
                let els = document.querySelectorAll('*');
                let y_axis = 250; 
                let x_axis = window.innerWidth - 300;
                
                for(let el of els) {
                    if(el.innerText && (el.innerText.trim() === 'Flying from' || el.innerText.trim() === 'Departure')) {
                        let rect = el.getBoundingClientRect();
                        y_axis = rect.y + (rect.height / 2);
                        // The widget usually ends around window.innerWidth - (window.innerWidth - rect.right)*0.2 or something
                        // But we can just scan horizontally to find the button
                        break;
                    }
                }
                
                // Scan horizontally along the Y-axis from the right side of the screen
                let clicked = false;
                for(let x = window.innerWidth - 100; x > window.innerWidth / 2; x -= 20) {
                    let el = document.elementFromPoint(x, y_axis);
                    if (el) {
                        let style = window.getComputedStyle(el);
                        // The button or its container is usually orange/reddish
                        if (style.backgroundColor.includes('rgb(255') || style.backgroundColor.includes('rgb(24')) {
                            el.click();
                            clicked = true;
                            break;
                        }
                    }
                }
                
                if (!clicked) {
                    // Try blindly clicking the right edge of the widget
                    let el = document.elementFromPoint(window.innerWidth - 250, y_axis);
                    if (el) el.click();
                }
            """)
            time.sleep(1)
            # Also send an ENTER just in case
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            
            print(f"[{self.name}] Polling CDP for API response...")
            start_time = time.time()
            
            while time.time() - start_time < 20 and not flights:
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        log_json = json.loads(entry['message'])['message']
                        if log_json['method'] == 'Network.responseReceived':
                            url = log_json['params']['response'].get('url', '')
                            if 'search' in url.lower() or 'availability' in url.lower() or 'flight' in url.lower():
                                req_id = log_json['params']['requestId']
                                try:
                                    res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                    body = res.get('body', '')
                                    if body and len(body) > 500:
                                        if 'currencyCode' in body or 'fares' in body or 'journeys' in body:
                                            data = json.loads(body)
                                            parsed = self._parse_availability(data, origin, destination, advance_window, fare_class)
                                            if parsed:
                                                flights.extend(parsed)
                                                print(f"[{self.name}] Successfully intercepted API via UI automation!")
                                                break
                                except Exception:
                                    pass
                    except Exception:
                        pass
                time.sleep(1)

            if not flights:
                print(f"[{self.name}] Failed to capture flight data via CDP. Falling back to DOM...")
                time.sleep(5) # Give DOM time to render flights
                html = driver.page_source
                flights = self._scrape_dom(html, origin, destination, advance_window, fare_class)
                print(f"[{self.name}] DOM extracted {len(flights)} flights")
                if not flights:
                    driver.save_screenshot("aix_fail.png")
            else:
                print(f"[{self.name}] Total: {len(flights)} flights extracted.")

        except Exception as e:
            print(f"[{self.name}] Error: {e}")
        finally:
            driver.quit()

        return flights


if __name__ == "__main__":
    spider = Spider()
    res = spider.scrape("DEL", "BOM", "T+15", "Economy", "28/09/2026")
    for f in res[:5]:
        print(f)
