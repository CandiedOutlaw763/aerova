import time
import json
import re
import base64
import gzip
from typing import List, Dict
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from .base_uc import UCSpider

AIRLINE_MAP = {
    '6E': 'IndiGo', 'AI': 'Air India', 'SG': 'SpiceJet',
    'QP': 'Akasa Air', 'IX': 'Air India Express', 'I5': 'Air India Express',
    'UK': 'Vistara', 'G8': 'Go First',
}

class Spider(UCSpider):
    name = "MakeMyTrip"

    def _parse_body(self, body: str, fare_class: str) -> List[Dict]:
        """Parse SSE / JSON body from response."""
        results = []
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                cards = data.get('cardList', [])
                if not cards:
                    cards = data.get('data', {}).get('cardList', [])
                if isinstance(cards, list) and cards:
                    for card in (cards[0] if isinstance(cards[0], list) else cards):
                        try:
                            card_str = json.dumps(card).lower()
                            
                            # Fare Class Bleed Filter
                            if fare_class == "Economy" and ('premium economy' in card_str or 'business' in card_str or 'first class' in card_str):
                                continue
                            if fare_class == "Premium Economy" and ('business' in card_str or 'first class' in card_str):
                                continue
                            if fare_class == "Business" and 'first class' in card_str:
                                continue
                                
                            # MoSPI Strict Standard: Non-stop only
                            # MMT usually denotes layovers as stops: 1, or layover duration
                            if '1 stop' in card_str or '2 stop' in card_str or 'layover' in card_str:
                                continue
                            
                            nm = (card.get('simpleAirlineHeading') or {}).get('nm', 'Unknown')
                            fb = (card.get('fareBreakup') or {}).get('fareBreakUpItems', [])
                            base, taxes, total = 0, 0, 0
                            for item in fb:
                                text = item.get('text', '').lower()
                                amt = re.sub(r'[^\d]', '', re.sub(r'<[^>]+>', '', str(item.get('amount', ''))))
                                if not amt:
                                    continue
                                v = int(amt)
                                if 'total' in text:
                                    total = v
                                elif 'base' in text:
                                    base = v
                                elif 'tax' in text or 'surcharge' in text:
                                    taxes += v
                            if total > 0:
                                results.append({'carrier': nm, 'base_fare': base, 'taxes': taxes, 'total_fare': total})
                        except Exception:
                            pass
        except Exception:
            pass

        if results:
            return results

        # Try SSE stream format
        for line in body.splitlines():
            if not line.startswith('data: '):
                continue
            payload = line[6:]
            if not payload.startswith('{'):
                try:
                    decoded = base64.b64decode(payload)
                    payload = gzip.decompress(decoded).decode('utf-8')
                except Exception:
                    continue
            try:
                chunk = json.loads(payload)
                cards = chunk.get('cardList', [])
                if isinstance(cards, list) and cards:
                    for card in (cards[0] if isinstance(cards[0], list) else cards):
                        try:
                            card_str = json.dumps(card).lower()
                            # Fare Class Bleed Filter
                            if fare_class == "Economy" and ('premium economy' in card_str or 'business' in card_str or 'first class' in card_str):
                                continue
                            if fare_class == "Premium Economy" and ('business' in card_str or 'first class' in card_str):
                                continue
                            if fare_class == "Business" and 'first class' in card_str:
                                continue
                                
                            # MoSPI Strict Standard: Non-stop only
                            if '1 stop' in card_str or '2 stop' in card_str or '1-stop' in card_str or '2-stop' in card_str or 'layover' in card_str:
                                continue
                                
                            nm = (card.get('simpleAirlineHeading') or {}).get('nm', 'Unknown')
                            fb = (card.get('fareBreakup') or {}).get('fareBreakUpItems', [])
                            base, taxes, total = 0, 0, 0
                            for item in fb:
                                text = item.get('text', '').lower()
                                amt = re.sub(r'[^\d]', '', re.sub(r'<[^>]+>', '', str(item.get('amount', ''))))
                                if not amt:
                                    continue
                                v = int(amt)
                                if 'total' in text:
                                    total = v
                                elif 'base' in text:
                                    base = v
                                elif 'tax' in text or 'surcharge' in text:
                                    taxes += v
                            if total > 0:
                                results.append({'carrier': nm, 'base_fare': base, 'taxes': taxes, 'total_fare': total})
                        except Exception:
                            pass
            except Exception:
                pass
        return results

    def _scrape_dom_html(self, html: str, fare_class: str) -> List[Dict]:
        flights = []
        scripts = re.findall(r'window\.__(?:INITIAL_STATE|MMT_DATA|DATA)__\s*=\s*(\{.+?\})\s*;', html, re.DOTALL)
        for s in scripts:
            try:
                data = json.loads(s)
                def extract(obj, depth=0):
                    if depth > 10:
                        return []
                    found = []
                    if isinstance(obj, list):
                        for item in obj:
                            found.extend(extract(item, depth + 1))
                    elif isinstance(obj, dict):
                        keys = set(obj.keys())
                        if any(k in keys for k in ['totalFare', 'totalPrice', 'pt', 'TF']):
                            obj_str = json.dumps(obj).lower()
                            # Fare Class Bleed Filter
                            if fare_class == "Economy" and ('premium economy' in obj_str or 'business' in obj_str or 'first class' in obj_str):
                                return found
                            if fare_class == "Premium Economy" and ('business' in obj_str or 'first class' in obj_str):
                                return found
                            if fare_class == "Business" and 'first class' in obj_str:
                                return found
                                
                            # MoSPI Strict Standard: Non-stop only
                            if '1 stop' in obj_str or '2 stop' in obj_str or '1-stop' in obj_str or '2-stop' in obj_str or 'layover' in obj_str:
                                return found
                                
                            price = obj.get('totalFare', obj.get('totalPrice', obj.get('pt', obj.get('TF', 0))))
                            carrier = obj.get('airlineCode', obj.get('airline', obj.get('al', '')))
                            base = obj.get('baseFare', obj.get('basefare', obj.get('bf', 0)))
                            tax = obj.get('taxes', obj.get('tax', obj.get('tx', 0)))
                            if price and carrier:
                                found.append((carrier, base, tax, price))
                        for v in obj.values():
                            found.extend(extract(v, depth + 1))
                    return found
                matches = extract(data)
                if matches:
                    for (carrier, base, tax, total) in matches:
                        flights.append({
                            'carrier': AIRLINE_MAP.get(str(carrier), str(carrier)),
                            'base_fare': int(base) if base else 0,
                            'taxes': int(tax) if tax else 0,
                            'total_fare': int(total)
                        })
                    return flights
            except Exception:
                pass

        return flights

    def _scrape_dom(self, driver, origin: str, destination: str, advance_window: str, fare_class: str) -> List[Dict]:
        import time
        from bs4 import BeautifulSoup
        import re
        flights_map = {}
        try:
            for _ in range(12):
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                # MakeMyTrip typically uses 'listingCard' or 'clusterViewPrice' for flight cards
                cards = soup.find_all('div', class_=lambda c: c and 'listingCard' in c)
                
                # If standard classes aren't found, try to locate cards by looking for airline logos/names
                if not cards:
                    airlines = ['IndiGo', 'Air India', 'SpiceJet', 'Akasa Air', 'Vistara']
                    found_cards = []
                    for airline in airlines:
                        elems = soup.find_all(string=re.compile(airline, re.IGNORECASE))
                        for el in elems:
                            parent = el.find_parent('div')
                            while parent:
                                text = parent.get_text()
                                if '₹' in text and len(text) > 50 and len(text) < 1000:
                                    if parent not in found_cards:
                                        found_cards.append(parent)
                                    break
                                parent = parent.find_parent('div')
                    cards = found_cards
                    
                for card in cards:
                    text = card.get_text(separator=' ', strip=True)
                    
                    # Fare Class Bleed Filter
                    text_lower = text.lower()
                    if fare_class == "Economy" and ('premium economy' in text_lower or 'business' in text_lower or 'first class' in text_lower):
                        continue
                    if fare_class == "Premium Economy" and ('business' in text_lower or 'first class' in text_lower):
                        continue
                    if fare_class == "Business" and 'first class' in text_lower:
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
                    for airline in ['IndiGo', 'Air India Express', 'Air India', 'SpiceJet', 'Akasa Air', 'Vistara']:
                        if airline.lower() in text.lower():
                            carrier = airline
                            break
                            
                    # Extract flight number or use a part of text to differentiate flights with same price
                    flight_num_match = re.search(r'([A-Z0-9]{2}-\d{3,4})', text)
                    flight_num = flight_num_match.group(1) if flight_num_match else text[:30].replace(' ', '')
                    
                    key = f"{carrier}_{price_val}_{flight_num}"
                    if key not in flights_map:
                        flights_map[key] = {
                            'carrier': carrier,
                            'origin': origin,
                            'destination': destination,
                            'advance_window': advance_window,
                            'fare_class': fare_class,
                            'base_fare': 0, 'taxes': 0, 'total_fare': price_val
                        }
                
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
        except Exception as e:
            print(f"[{self.name}] Error in BeautifulSoup DOM scrape: {e}")
        return list(flights_map.values())

    def _wait_for_challenge_clear(self, driver, timeout: int = 20) -> bool:
        """
        Wait until the Cloudflare JS challenge clears by polling the page title.
        Cloudflare challenge pages have title "Just a moment..." — once the page
        transitions to real content, the title changes. Returns True if cleared,
        False if timed out.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            title = driver.title.lower()
            # All known Cloudflare / Turnstile challenge titles
            blocked = (
                "just a moment" in title
                or "checking your browser" in title
                or "please wait" in title
                or "challenge validation" in title
                or "attention required" in title
            )
            if blocked:
                time.sleep(1)
                continue
            # Also wait if we're on a blank/loading page
            if not title or title in ("", "about:blank"):
                time.sleep(1)
                continue
            # Title looks like real MMT content
            return True
        return False  # timed out still showing challenge

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        flights = []
        driver = self.get_driver()
        try:
            # Enable CDP Network interception
            driver.execute_cdp_cmd('Network.enable', {})
            
            # Build deep_link
            try:
                parts = date_str.split('/')
                if len(parts) == 3:
                    import datetime as dt_mod
                    parsed = dt_mod.datetime.strptime(date_str, "%d/%m/%Y")
                    mmt_date = parsed.strftime("%d/%m/%Y")
                else:
                    import datetime as dt_mod
                    parsed = dt_mod.datetime.strptime(date_str, "%Y-%m-%d")
                    mmt_date = parsed.strftime("%d/%m/%Y")
            except Exception:
                mmt_date = "28/09/2026"
            
            deep_link = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{mmt_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&ccde=IN&lang=eng"

            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.common.exceptions import WebDriverException
            actions = ActionChains(driver)

            print(f"[{self.name}] Navigating to MMT homepage...")
            driver.set_page_load_timeout(15)
            try:
                driver.get("https://www.makemytrip.com/")
            except (TimeoutException, WebDriverException):
                print(f"[{self.name}] Homepage load timed out. Polling title...")

            cleared = self._wait_for_challenge_clear(driver, timeout=25)
            if not cleared:
                print(f"[{self.name}] Cloudflare challenge did not clear on homepage. Skipping.")
                return []
            print(f"[{self.name}] Challenge cleared. Title: {driver.title!r}")

            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.by import By
            actions = ActionChains(driver)

            # Dismiss modal
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            try:
                driver.execute_script("""
                    let closes = document.querySelectorAll('.commonModal__close, [data-cy="closeModal"], .close');
                    for(let c of closes) { try { c.click(); } catch(e) {} }
                """)
            except:
                pass
            time.sleep(1)

            print(f"[{self.name}] Inputting Origin: {origin}")
            try:
                el = driver.find_element(By.ID, "fromCity")
                actions.move_to_element(el).click().perform()
                time.sleep(1)
                inp = driver.find_element(By.CSS_SELECTOR, "input[placeholder='From']")
                inp.send_keys(origin)
                time.sleep(1)
                suggestion = driver.find_element(By.CSS_SELECTOR, "ul[role='listbox'] li")
                actions.move_to_element(suggestion).click().perform()
                time.sleep(1)
            except Exception as e:
                print(f"[{self.name}] Failed to set Origin: {e}")

            print(f"[{self.name}] Inputting Destination: {destination}")
            try:
                el = driver.find_element(By.ID, "toCity")
                actions.move_to_element(el).click().perform()
                time.sleep(1)
                inp = driver.find_element(By.CSS_SELECTOR, "input[placeholder='To']")
                inp.send_keys(destination)
                time.sleep(1)
                suggestion = driver.find_element(By.CSS_SELECTOR, "ul[role='listbox'] li")
                actions.move_to_element(suggestion).click().perform()
                time.sleep(1)
            except Exception as e:
                print(f"[{self.name}] Failed to set Destination: {e}")

            day = date_str.split('/')[0].lstrip('0')
            print(f"[{self.name}] Selecting Date: {day}")
            try:
                driver.execute_script(f"""
                    let days = document.querySelectorAll('.DayPicker-Day');
                    for (let d of days) {{
                        let text = d.innerText || '';
                        if (text.includes('{day}')) {{
                            d.click();
                            break;
                        }}
                    }}
                """)
                time.sleep(1)
            except Exception as e:
                print(f"[{self.name}] Failed to set Date: {e}")

            print(f"[{self.name}] Selecting Travel Class: {fare_class}")
            try:
                driver.execute_script("""
                    let travelClassEl = document.querySelector('[data-cy="travelClass"]');
                    if (travelClassEl) { travelClassEl.click(); }
                """)
                time.sleep(1)
                class_map = {
                    "Economy": "Economy",
                    "Premium Economy": "Premium Economy",
                    "Business": "Business",
                    "First Class": "First Class"
                }
                target_text = class_map.get(fare_class, "Economy")
                driver.execute_script(f"""
                    let items = document.querySelectorAll('.travelForPopup li');
                    for (let item of items) {{
                        if (item.innerText.includes('{target_text}')) {{
                            item.click();
                            break;
                        }}
                    }}
                    let applyBtn = document.querySelector('.primaryBtn.btnApply');
                    if (applyBtn) {{ applyBtn.click(); }}
                """)
                time.sleep(1)
            except Exception as e:
                print(f"[{self.name}] Failed to set Travel Class: {e}")

            print(f"[{self.name}] Clicking Search...")
            try:
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                driver.execute_script("document.querySelector('a.widgetSearchBtn').click();")
            except Exception as e:
                print(f"[{self.name}] Failed to click Search: {e}")

            time.sleep(10)
            print(f"[{self.name}] Polling CDP for payload...")
            start = time.time()
            accumulated = set()

            while time.time() - start < 35 and not flights:
                time.sleep(2)
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        msg = json.loads(entry['message'])['message']
                        if msg['method'] == 'Network.responseReceived':
                            req_url = msg['params']['response'].get('url', '')
                            if 'api' in req_url or 'search' in req_url or 'flight' in req_url:
                                print(f"[MMT-DEBUG] url: {req_url}")
                            if ('search-stream' in req_url or 'intpricedsr' in req_url
                                    or 'air-search' in req_url or 'flightsearchresult' in req_url):
                                accumulated.add(msg['params']['requestId'])
                    except Exception:
                        continue

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
                        if body and len(body) > 500:
                            parsed = self._parse_body(body, fare_class)
                            if parsed:
                                for f in parsed:
                                    f['origin'] = origin
                                    f['destination'] = destination
                                    f['advance_window'] = advance_window
                                    f['fare_class'] = fare_class
                                flights.extend(parsed)
                                accumulated.remove(req_id)
                                print(f"[{self.name}] CDP intercepted {len(parsed)} flights")
                    except Exception:
                        pass

            if not flights:
                print(f"[{self.name}] CDP found nothing. Falling back to DOM...")
                flights = self._scrape_dom(driver, origin, destination, advance_window, fare_class)
                print(f"[{self.name}] DOM extracted {len(flights)} flights")

        except Exception as e:
            print(f"[{self.name}] Scraping failed: {e}")
        finally:
            with open("mmt_source_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()

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
