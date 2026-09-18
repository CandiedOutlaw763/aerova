import time
import json
import re
import base64
import gzip
from typing import List, Dict
from .base_uc import UCSpider

class Spider(UCSpider):
    name = "Cleartrip"

    def _scrape_dom(self, driver) -> List[Dict]:
        flights = []
        try:
            # First try INITIAL_STATE parsing...
            html = driver.page_source
            scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
            for s in scripts:
                if 'window.__INITIAL_STATE__' in s or 'staticData' in s or 'flights' in s.lower():
                    try:
                        js_obj = re.search(r'(\{[\s\S]+\})', s)
                        if js_obj:
                            data = json.loads(js_obj.group(1))
                            def extract_prices(obj, depth=0):
                                if depth > 8: return []
                                found = []
                                if isinstance(obj, list):
                                    for item in obj:
                                        found.extend(extract_prices(item, depth+1))
                                elif isinstance(obj, dict):
                                    if 'totalPrice' in obj and 'airlineCode' in obj:
                                        found.append((obj['airlineCode'], obj.get('baseFare', 0), obj.get('tax', 0), obj['totalPrice']))
                                    for v in obj.values():
                                        found.extend(extract_prices(v, depth+1))
                                return found
                            
                            matches = extract_prices(data)
                            if matches:
                                for (carrier, base, tax, total) in matches:
                                    flights.append({
                                        'carrier': str(carrier),
                                        'base_fare': int(base) if base else 0,
                                        'taxes': int(tax) if tax else 0,
                                        'total_fare': int(total)
                                    })
                                return flights
                    except Exception:
                        pass

            # Fallback: BeautifulSoup DOM parser to hunt for exact flight cards
            from bs4 import BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all elements containing airline names
            airlines = ['IndiGo', 'Air India', 'SpiceJet', 'Akasa Air', 'Vistara', 'Air India Express']
            found_cards = []
            for airline in airlines:
                elems = soup.find_all(string=re.compile(airline, re.IGNORECASE))
                for el in elems:
                    # Go up to a container that is likely a flight card
                    parent = el.find_parent('div')
                    while parent:
                        text = parent.get_text()
                        if '₹' in text and len(text) > 50 and len(text) < 1000:
                            if parent not in found_cards:
                                found_cards.append(parent)
                            break
                        parent = parent.find_parent('div')
            
            for card in found_cards[:20]:
                text = card.get_text(separator=' ', strip=True)
                
                # MoSPI Strict Standard: Premium Cabin Bleed Filter
                text_lower = text.lower()
                if 'premium economy' in text_lower or 'business' in text_lower or 'first class' in text_lower:
                    continue
                    
                # MoSPI Strict Standard: Non-stop only
                if '1 stop' in text_lower or '2 stop' in text_lower or 'layover' in text_lower:
                    continue
                
                # Extract Price
                price_match = re.search(r'₹\s*([\d,]+)', text)
                if not price_match:
                    continue
                price_val = int(price_match.group(1).replace(',', ''))
                if price_val < 2000 or price_val > 50000:
                    continue
                    
                # Extract Airline
                carrier = 'Unknown'
                for airline in airlines:
                    if airline.lower() in text.lower():
                        carrier = airline
                        break
                        
                # Only add if it's unique
                already_exists = False
                for f in flights:
                    if f['carrier'] == carrier and f['total_fare'] == price_val:
                        already_exists = True
                        break
                
                if not already_exists:
                    flights.append({
                        'carrier': carrier,
                        'base_fare': 0, 'taxes': 0, 'total_fare': price_val
                    })
        except Exception as e:
            print(f"[{self.name}] BeautifulSoup scrape error: {e}")
            
        return flights

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        flights = []
        driver = self.get_driver()
        try:
            # Enable CDP Network interception
            driver.execute_cdp_cmd('Network.enable', {})
            
            # Build deep link
            try:
                parts = date_str.split('/')
                if len(parts) == 3:
                    import datetime as dt_mod
                    parsed = dt_mod.datetime.strptime(date_str, "%d/%m/%Y")
                    ct_date = parsed.strftime("%d/%m/%Y")
                else:
                    import datetime as dt_mod
                    parsed = dt_mod.datetime.strptime(date_str, "%Y-%m-%d")
                    ct_date = parsed.strftime("%d/%m/%Y")
            except Exception:
                ct_date = "28/09/2026"

            deep_link = f"https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date={ct_date}&from={origin}&to={destination}"
            
            try:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                from selenium.common.exceptions import WebDriverException, TimeoutException
                actions = ActionChains(driver)

                print(f"[{self.name}] Navigating to Cleartrip homepage...")
                driver.set_page_load_timeout(15)
                try:
                    driver.get("https://www.cleartrip.com/")
                except (TimeoutException, WebDriverException):
                    print(f"[{self.name}] Homepage load timed out. Polling title...")

                # Wait for Cloudflare
                deadline = time.time() + 25
                cleared = False
                while time.time() < deadline:
                    title = driver.title.lower()
                    blocked = (
                        "just a moment" in title
                        or "checking your browser" in title
                        or "please wait" in title
                        or "challenge validation" in title
                        or "attention required" in title
                    )
                    if blocked or not title or title in ("", "about:blank"):
                        time.sleep(1)
                        continue
                    cleared = True
                    break

                if not cleared:
                    print(f"[{self.name}] Cloudflare challenge did not clear. Skipping.")
                    return []
                print(f"[{self.name}] Challenge cleared. Title: {driver.title!r}")

                # JS Soft Navigation inside the same window context to bypass Cloudflare/Turnstile
                print(f"[{self.name}] Navigating to search via window.location.href...")
                try:
                    driver.execute_script(f"window.location.href = '{deep_link}';")
                except (TimeoutException, WebDriverException):
                    pass
                
                time.sleep(15)
                print(f"[{self.name}] Search page ready. URL: {driver.current_url}")

                # Dismiss modals
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)

                print(f"[{self.name}] Polling CDP for payload...")
                start = time.time()
                accumulated = set()

                while time.time() - start < 35 and not flights:
                    time.sleep(2)
                    logs = driver.get_log('performance')
                    for entry in logs:
                        try:
                            msg = json.loads(entry.get('message', '{}')).get('message', {})
                            if msg.get('method') == 'Network.responseReceived':
                                url = msg.get('params', {}).get('response', {}).get('url', '')
                                if 'b2c/search' in url or 'flight/search' in url or 'v7/NIA' in url or 'search-api' in url:
                                    request_id = msg.get('params', {}).get('requestId')
                                    if request_id:
                                        accumulated.add(request_id)
                        except Exception:
                            pass
                    
                    for req_id in list(accumulated):
                        try:
                            body_info = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                            body = body_info.get('body', '')
                            
                            if body_info.get('base64Encoded'):
                                try:
                                    decoded = base64.b64decode(body)
                                    try:
                                        body = gzip.decompress(decoded).decode('utf-8')
                                    except Exception:
                                        body = decoded.decode('utf-8', errors='ignore')
                                except Exception:
                                    pass
                            
                            if body and len(body) > 1000:
                                try:
                                    data = json.loads(body)
                                    
                                    def extract_ct_prices(obj, depth=0):
                                        if depth > 10: return []
                                        found = []
                                        if isinstance(obj, list):
                                            for item in obj: found.extend(extract_ct_prices(item, depth+1))
                                        elif isinstance(obj, dict):
                                            obj_str = json.dumps(obj).lower()
                                            if 'premium economy' in obj_str or 'business' in obj_str or 'first class' in obj_str:
                                                pass
                                            elif '1 stop' in obj_str or '2 stop' in obj_str or 'layover' in obj_str:
                                                pass
                                            elif 'totalPayable' in obj or 'totalPrice' in obj or 'price' in obj:
                                                price = obj.get('totalPayable', obj.get('totalPrice', obj.get('price', 0)))
                                                carrier = obj.get('airline', obj.get('carrierCode', obj.get('airlineCode', 'Unknown')))
                                                if isinstance(price, dict):
                                                    price = price.get('amount', price.get('value', 0))
                                                base = obj.get('baseFare', 0)
                                                tax = obj.get('taxes', 0)
                                                if price and str(price).isdigit():
                                                    found.append((carrier, base, tax, price))
                                            for v in obj.values():
                                                found.extend(extract_ct_prices(v, depth+1))
                                        return found
                                    
                                    matches = extract_ct_prices(data)
                                    if matches:
                                        for (carrier, base, tax, total) in matches:
                                            flights.append({
                                                'carrier': str(carrier),
                                                'base_fare': int(base) if str(base).isdigit() else 0,
                                                'taxes': int(tax) if str(tax).isdigit() else 0,
                                                'total_fare': int(total)
                                            })
                                        print(f"[{self.name}] CDP intercepted {len(matches)} flights from {url}")
                                        accumulated.remove(req_id)
                                except Exception as json_err:
                                    pass
                        except Exception:
                            pass
                
                if not flights:
                    print(f"[{self.name}] CDP found nothing. Falling back to DOM...")
                    flights = self._scrape_dom(driver)
                    print(f"[{self.name}] DOM extracted {len(flights)} flights")
                    
            finally:
                driver.quit()

        except Exception as e:
            print(f"[{self.name}] Scraping failed: {e}")

        # Format output
        for f in flights:
            f['origin'] = origin
            f['destination'] = destination
            f['advance_window'] = advance_window
            f['fare_class'] = fare_class

        return flights

if __name__ == "__main__":
    spider = Spider()
    res = spider.scrape("DEL", "BOM", "T+15", "Economy", "28/09/2026")
    for f in res[:5]:
        print(f)
