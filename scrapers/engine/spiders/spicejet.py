import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class Spider:
    def __init__(self):
        self.name = "SpiceJet"

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> list:
        print(f"[{self.name}] Scraping API for {origin} -> {destination} on {date_str}...")
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--start-maximized')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        driver = webdriver.Chrome(options=options)
        flights = []
        
        try:
            driver.get("https://www.spicejet.com/")
            time.sleep(10)
            
            # 1. Click Origin
            print(f"[{self.name}] Setting origin to {origin}...")
            driver.execute_script("""
                let inps = document.querySelectorAll('input');
                if(inps.length > 0) {
                    inps[0].focus();
                    inps[0].click();
                }
            """)
            time.sleep(2)
            
            active = driver.switch_to.active_element
            for _ in range(5):
                active.send_keys(u'\ue003') # Backspace
            
            for char in origin:
                active.send_keys(char)
                time.sleep(0.1)
            time.sleep(2)
            
            driver.execute_script(f"""
                let els = document.querySelectorAll('div');
                for(let el of els) {{
                    if(el.innerText && el.innerText.trim() === '{origin}') {{
                        el.click();
                        break;
                    }}
                }}
            """)
            time.sleep(2)
            
            # 2. Click Destination
            print(f"[{self.name}] Setting destination to {destination}...")
            driver.execute_script("""
                let inps = document.querySelectorAll('input');
                if(inps.length > 1) {
                    inps[1].focus();
                    inps[1].click();
                }
            """)
            time.sleep(1)
            
            active = driver.switch_to.active_element
            for char in destination:
                active.send_keys(char)
                time.sleep(0.1)
            time.sleep(2)
            
            driver.execute_script(f"""
                let els = document.querySelectorAll('div');
                for(let el of els) {{
                    if(el.innerText && el.innerText.trim() === '{destination}') {{
                        el.click();
                        break;
                    }}
                }}
            """)
            time.sleep(2)
            
            # 3. Select Date and close calendar
            try:
                if '/' in date_str:
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    dt = datetime.strptime(date_str, "%d-%b-%Y")
                target_day = str(dt.day)
            except Exception as e:
                print(f"[{self.name}] Date parse error ({date_str}): {e}")
                target_day = "28"
                
            print(f"[{self.name}] Selecting Date: {target_day}...")
            driver.execute_script(f"""
                let cells = document.querySelectorAll('div');
                for(let cell of cells) {{
                    if (cell.innerText && cell.innerText.trim() === '{target_day}' && cell.getAttribute('data-testid') && cell.getAttribute('data-testid').includes('undefined-calendar-day')) {{
                        cell.click();
                        break;
                    }}
                }}
            """)
            time.sleep(2)
            
            # Dismiss calendar if still open
            ActionChains(driver).move_by_offset(20, 20).click().perform()
            time.sleep(2)
            
            # 4. Click Search
            print(f"[{self.name}] Triggering search...")
            try:
                search_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='home-page-flight-cta']")
                ActionChains(driver).move_to_element(search_btn).click().perform()
            except Exception:
                driver.execute_script("""
                    let btn = document.querySelector("[data-testid='home-page-flight-cta']");
                    if(btn) btn.click();
                """)
            
            print(f"[{self.name}] Waiting for availability API...")
            start_time = time.time()
            api_data = None
            
            while time.time() - start_time < 20:
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        log_json = json.loads(entry['message'])['message']
                        if log_json['method'] == 'Network.responseReceived':
                            url = log_json['params']['response'].get('url', '')
                            if 'api/' in url.lower() and 'search/availability' in url.lower():
                                req_id = log_json['params']['requestId']
                                res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                body = res.get('body', '')
                                if body and len(body) > 1000:
                                    api_data = json.loads(body)
                                    break
                    except Exception:
                        pass
                if api_data:
                    break
                time.sleep(1)
                
            if not api_data:
                print(f"[{self.name}] Timeout waiting for API.")
                return []
                
            try:
                trips = api_data.get('data', {}).get('trips', [])
                if not trips:
                    print(f"[{self.name}] No trips found in API response.")
                    return []
                    
                journeys = trips[0].get('journeysAvailable', [])
                fares_available = api_data.get('data', {}).get('faresAvailable', {})
                
                for journey in journeys:
                    flight_num = journey.get('carrierString')
                    designator = journey.get('designator', {})
                    dep_time = designator.get('departure')
                    arr_time = designator.get('arrival')
                    
                    # MoSPI Strict Standard: Non-stop only
                    journey_str = json.dumps(journey).lower()
                    if '1 stop' in journey_str or '2 stop' in journey_str or 'layover' in journey_str:
                        continue
                    if len(journey.get('segments', [])) > 1:
                        continue
                    
                    for fare_key, fare_info in journey.get('fares', {}).items():
                        # Only consider fares that are actually available
                        if fare_info.get('availableCount', 0) == 0:
                            continue
                        if fare_key in fares_available:
                            fare_details = fares_available[fare_key]
                            passengers = fare_details.get('passengerFares', [])
                            if passengers:
                                total_amount = passengers[0].get('fareAmount', 0)
                                
                                taxes = 0
                                for sc in passengers[0].get('serviceCharges', []):
                                    if sc.get('type') in [4, 5] or sc.get('code') in ['GST', 'UDF', 'PSF']:
                                        taxes += sc.get('amount', 0)
                                        
                                if total_amount > 0:
                                    base_fare = total_amount - taxes
                                    flights.append({
                                        "origin": origin,
                                        "destination": destination,
                                        "carrier": f"SpiceJet ({flight_num})",
                                        "departure_time": dep_time,
                                        "arrival_time": arr_time,
                                        "advance_window": advance_window,
                                        "fare_class": fare_class,
                                        "base_fare": base_fare,
                                        "taxes": taxes,
                                        "total_fare": total_amount
                                    })
                
                print(f"[{self.name}] Extracted {len(flights)} flights successfully.")
                
            except Exception as e:
                print(f"[{self.name}] Parse error: {e}")
            
        except Exception as e:
            print(f"[{self.name}] Critical Exception: {e}")
        finally:
            driver.quit()
            
        return flights
