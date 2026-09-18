import json
import time
from typing import List, Dict
from selenium.webdriver.common.by import By
from .base_uc import UCSpider
from .utils import setup_cdp_limits

class Spider(UCSpider):
    name = "Air India"

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        """
        Scrape Air India flights by automating the website UI.
        
        Strategy:
        1. Navigate to airindia.com
        2. Fill origin/destination using Angular mat-autocomplete dropdowns
        3. Open date picker and select the target date
        4. Click Search and intercept the air-bounds API response via CDP
        
        Key selectors:
        - Origin field: [aria-label="Select origin airport"] → mat-autocomplete-trigger input
        - Destination field: [aria-label="Select destination airport"]
        - Dropdown items: mat-option
        - Date trigger: XPath //*[contains(text(), 'Select Date')]
        - Calendar cells: .mat-calendar-body-cell-content
        - API: https://api.airindia.com/cbiz-booking/v2/prime/search/air-bounds
        """
        flights = []
        driver = self.get_driver()

        try:
            print(f"[{self.name}] Enabling CDP Network monitoring...")
            driver.execute_cdp_cmd('Network.enable', {})
            
            # Parse date - handle DD/MM/YYYY and YYYY-MM-DD formats
            import datetime as dt_mod
            try:
                if '/' in date_str:
                    parsed_dt = dt_mod.datetime.strptime(date_str, "%d/%m/%Y")
                elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                    parsed_dt = dt_mod.datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    parsed_dt = dt_mod.datetime.strptime(date_str, "%d-%b-%Y")
            except:
                parsed_dt = dt_mod.datetime.now() + dt_mod.timedelta(days=15)
            target_day = str(parsed_dt.day)
            
            print(f"[{self.name}] Navigating to Air India homepage...")
            driver.get("https://www.airindia.com/")
            time.sleep(12)  # Angular app needs time to bootstrap
            
            print(f"[{self.name}] Dismissing cookie banner...")
            try:
                driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); });")
            except:
                pass
            time.sleep(1)
            
            print(f"[{self.name}] Selecting One Way...")
            driver.execute_script("""
                let inputs = document.querySelectorAll('input[type="radio"]');
                for(let i of inputs) { if(i.value === 'one-way') { i.click(); break; } }
            """)
            time.sleep(0.5)
            
            print(f"[{self.name}] Filling origin = {origin}...")
            driver.execute_script("document.querySelector('[aria-label=\"Select origin airport\"]').click();")
            time.sleep(1.5)
            driver.switch_to.active_element.send_keys(origin)
            time.sleep(2)
            driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
            time.sleep(1.5)
            
            print(f"[{self.name}] Filling destination = {destination}...")
            driver.execute_script("document.querySelector('[aria-label=\"Select destination airport\"]').click();")
            time.sleep(1.5)
            driver.switch_to.active_element.send_keys(destination)
            time.sleep(2)
            driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
            time.sleep(1.5)
            
            print(f"[{self.name}] Opening date picker...")
            try:
                depart_el = driver.find_element(By.XPATH, "//*[contains(text(), 'Select Date')]")
                driver.execute_script("arguments[0].click();", depart_el)
            except Exception:
                # Fallback: click the first date input area
                driver.execute_script("document.querySelectorAll('input[type=text], .date-trigger, [class*=date]')[0].click();")
            time.sleep(1.5)
            
            print(f"[{self.name}] Clicking day {target_day}...")
            driver.execute_script(f"""
                let contents = document.querySelectorAll('.mat-calendar-body-cell-content');
                for(let c of contents) {{
                    if(c.innerText.trim() === '{target_day}') {{ c.click(); return; }}
                }}
            """)
            time.sleep(1)
            
            print(f"[{self.name}] Clicking Search...")
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.trim() === 'Search') b.click(); });")
            
            print(f"[{self.name}] Waiting for air-bounds API response...")
            start_time = time.time()
            
            while time.time() - start_time < 35:
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        log_json = json.loads(entry['message'])['message']
                        if log_json['method'] == 'Network.responseReceived':
                            url = log_json['params']['response'].get('url', '')
                            if 'air-bounds' in url:
                                req_id = log_json['params']['requestId']
                                try:
                                    res = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                    body = res.get('body', '')
                                    if body and len(body) > 100:
                                        data = json.loads(body)
                                        import traceback
                                        try:
                                            with open(r'C:\Users\siddh\.gemini\antigravity-ide\brain\c0071c49-e902-49fa-bd64-446178c24a85\scratch\ai_payload.json', 'w') as f:
                                                json.dump(data, f)
                                        except:
                                            pass
                                        flights = self._parse_response(data, origin, destination, advance_window, fare_class)
                                        print(f"[{self.name}] Parsed {len(flights)} flights.")
                                        return flights
                                except Exception as e2:
                                    print(f"[{self.name}] Body fetch error: {e2}")
                    except:
                        pass
                time.sleep(0.5)
                
            print(f"[{self.name}] Timed out waiting for air-bounds response.")
                
        except Exception as e:
            print(f"[{self.name}] Error during scrape: {e}")
            try:
                driver.save_screenshot("airindia_error.png")
            except:
                pass
        finally:
            driver.quit()

        return flights

    def _parse_response(self, data: dict, origin: str, destination: str, advance_window: str, fare_class: str) -> List[Dict]:
        """Parse air-bounds API response into normalized flight records."""
        results = []
        
        try:
            payload = data.get("responsePayload", [])
            for journey in payload:
                for group in journey.get("airBoundGroups", []):
                    bound_details = group.get("boundDetails", {})
                    segments = bound_details.get("segments", [])
                    
                    # MoSPI Strict Standard: Non-stop flights only
                    if len(segments) > 1:
                        continue
                        
                    for air_bound in group.get("airBounds", []):
                        fare_family = air_bound.get("fareFamilyCode", "")
                        avail = air_bound.get("availabilityDetails", [])
                        cabin = avail[0].get("cabin", "eco") if avail else "eco"
                        
                        # Map cabin to fare_class name
                        cabin_map = {"eco": "Economy", "ecoPremium": "Premium Economy", "business": "Business", "fst": "First Class", "pre": "Premium Economy", "bus": "Business"}
                        mapped_fare_class = cabin_map.get(cabin, "Economy")
                        
                        # Filter by requested fare_class
                        if mapped_fare_class != fare_class:
                            continue
                        
                        # Get lowest price
                        prices = air_bound.get("prices", {})
                        total_prices = prices.get("totalPrices", [])
                        if total_prices:
                            total_fare = total_prices[0].get("total", 0)
                            currency = total_prices[0].get("currencyCode", "INR")
                        else:
                            # Try aiUnitPrice
                            ai_price = air_bound.get("aiUnitPrice", {})
                            total_fare = ai_price.get("value", 0)
                            currency = ai_price.get("currencyCode", "INR")
                        
                        if total_fare > 0:
                            results.append({
                                "origin": origin,
                                "destination": destination,
                                "carrier": "AI",
                                "advance_window": advance_window,
                                "fare_class": mapped_fare_class,
                                "booking_class": avail[0].get("bookingClass", "") if avail else "",
                                "fare_family": fare_family,
                                "total_fare": total_fare,
                                "currency": currency,
                            })
        except Exception as e:
            print(f"[{self.name}] Parse error: {e}")
            
        return results
