import json
import time
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from .base_uc import UCSpider

class Spider(UCSpider):
    name = "IndiGo"

    def parse_indigo_json(self, json_str: str, advance_window: str, fare_class: str) -> List[Dict]:
        data = json.loads(json_str)
        if "data" in data and isinstance(data["data"], dict):
            data = data["data"]
            
        flights = []
        
        if "trips" in data and len(data["trips"]) > 0:
            for trip in data["trips"]:
                journeys = trip.get("journeysAvailable", [])
                
                for journey in journeys:
                    designator = journey.get("designator", {})
                    origin = designator.get("origin")
                    destination = designator.get("destination")
                    departure = designator.get("departure")
                    arrival = designator.get("arrival")
                    
                    # MoSPI Strict Standard: Non-stop only
                    journey_str = json.dumps(journey).lower()
                    if '1 stop' in journey_str or '2 stop' in journey_str or 'layover' in journey_str:
                        continue
                    if len(journey.get("segments", [])) > 1:
                        continue
                    
                    passenger_fares = journey.get("passengerFares", [])
                    if passenger_fares:
                        # Find the minimum totalFareAmount across active fares
                        min_fare = None
                        min_taxes = 0
                        
                        for fare in passenger_fares:
                            if fare.get("isActive", False):
                                total_amount = fare.get("totalFareAmount", 0)
                                total_tax = fare.get("totalTax", 0)
                                
                                if min_fare is None or total_amount < min_fare:
                                    min_fare = total_amount
                                    min_taxes = total_tax
                                    
                        if min_fare is not None:
                            base_fare = min_fare - min_taxes
                            flights.append({
                                "origin": origin,
                                "destination": destination,
                                "carrier": "IndiGo (6E)",
                                "departure_time": departure,
                                "arrival_time": arrival,
                                "advance_window": advance_window,
                                "fare_class": fare_class,
                                "base_fare": base_fare,
                                "taxes": min_taxes,
                                "total_fare": min_fare
                            })
                            
        return flights

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        import datetime
        print(f"[{self.name}] Scraping API for {origin} -> {destination} on {date_str}...")
        
        # Parse the target day
        try:
            if '-' in date_str and len(date_str.split('-')[1]) == 3:
                # 14-Oct-2026
                dt = datetime.datetime.strptime(date_str, "%d-%b-%Y")
            elif '/' in date_str:
                # 28/10/2026
                dt = datetime.datetime.strptime(date_str, "%d/%m/%Y")
            else:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except:
            dt = datetime.datetime.now() + datetime.timedelta(days=15)
            
        target_day = str(dt.day)
        target_month_str = dt.strftime("%B %Y")  # e.g., "September 2026"
        
        flights = []
        driver = self.get_driver()
        
        try:
            driver.execute_cdp_cmd('Network.enable', {})
            print(f"[{self.name}] Loading homepage...")
            driver.get('https://www.goindigo.in/')
            time.sleep(8)
            
            # Hide sticky elements
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
            time.sleep(1)
            
            print(f"[{self.name}] Entering Origin: {origin}...")
            from_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__from input')
            driver.execute_script("arguments[0].click();", from_input)
            time.sleep(1)
            
            from_input.send_keys(Keys.CONTROL, 'a')
            from_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            
            for char in origin:
                from_input.send_keys(char)
                time.sleep(0.3)
                
            time.sleep(2)
            
            driver.execute_script(f"""
                let items = document.querySelectorAll('.city-selection__list-item, .city-selection__list-item--info, ul.MuiList-root li');
                for (let item of items) {{
                    if (item.innerText.includes('{origin}')) {{
                        item.click();
                        return true;
                    }}
                }}
                if(items.length > 0) {{
                    items[0].click();
                    return true;
                }}
            """)
            time.sleep(1)
            
            print(f"[{self.name}] Entering Destination: {destination}...")
            to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
            driver.execute_script("arguments[0].click();", to_input)
            time.sleep(1)
            
            to_input.send_keys(Keys.CONTROL, 'a')
            to_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            
            for char in destination:
                to_input.send_keys(char)
                time.sleep(0.3)
                
            time.sleep(2)
            
            driver.execute_script(f"""
                let items = document.querySelectorAll('.city-selection__list-item, .city-selection__list-item--info, ul.MuiList-root li');
                for (let item of items) {{
                    if (item.innerText.includes('{destination}')) {{
                        item.click();
                        return true;
                    }}
                }}
                if(items.length > 0) {{
                    items[0].click();
                    return true;
                }}
            """)
            time.sleep(1)
            
            print(f"[{self.name}] Opening Date Picker...")
            date_inputs = driver.find_elements(By.CSS_SELECTOR, '.search-widget-form-body__date')
            if date_inputs:
                driver.execute_script("arguments[0].click();", date_inputs[0])
                time.sleep(1)
                
            print(f"[{self.name}] Selecting Date: {target_day}...")
            
            # Navigate to correct month if possible (IndiGo datepicker uses scrolling or clicking next)
            # We'll just try to click the day.
            
            found = driver.execute_script(f"""
                let targetDay = "{target_day}";
                let cells = document.querySelectorAll('.react-datepicker__day, .DayPicker-Day, [role="gridcell"], td, .custom-date-picker-calendar__day');
                let clicked = false;
                for(let i=0; i<cells.length; i++) {{
                    let cell = cells[i];
                    if(cell.innerText.trim() === targetDay && !cell.classList.contains('outside-month') && !cell.classList.contains('react-datepicker__day--outside-month') && !cell.classList.contains('custom-date-picker-calendar__day--outside-month')) {{
                        cell.click();
                        clicked = true;
                        break;
                    }}
                }}
                return clicked;
            """)
            
            if found:
                print(f"[{self.name}] Date selected successfully.")
            else:
                print(f"[{self.name}] Could not find date easily in calendar.")
                
            time.sleep(1)
            
            print(f"[{self.name}] Clicking Search...")
            search_btn = driver.find_element(By.CSS_SELECTOR, 'button.skyplus-button--filled')
            driver.execute_script("arguments[0].click();", search_btn)
            
            print(f"[{self.name}] Waiting for background API response...")
            start_time = time.time()
            data = None
            
            while time.time() - start_time < 25:
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        log_json = json.loads(entry['message'])['message']
                        if log_json['method'] == 'Network.responseReceived':
                            url = log_json['params']['response'].get('url', '')
                            if 'flight' in url.lower() and 'search' in url.lower() and 'v2' in url.lower():
                                req_id = log_json['params']['requestId']
                                try:
                                    res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                    if res.get('body') and len(res['body']) > 100:
                                        data = json.loads(res['body'])
                                        break
                                except Exception:
                                    pass
                    except:
                        pass
                if data:
                    break
                time.sleep(1)
                
            if data:
                print(f"[{self.name}] Payload captured successfully.")
                flights = self.parse_indigo_json(json.dumps(data), advance_window, fare_class)
            else:
                print(f"[{self.name}] Failed to capture response JSON via CDP.")
                driver.save_screenshot("indigo_ui_fail.png")
                
        except Exception as e:
            print(f"[{self.name}] Scraping failed: {e}")
        finally:
            driver.quit()

        return flights