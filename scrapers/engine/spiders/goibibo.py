import time
import json
import re
from typing import List, Dict
from selenium.common.exceptions import TimeoutException
from .base_uc import UCSpider

class Spider(UCSpider):
    name = "Goibibo"

    def _wait_for_challenge_clear(self, driver, timeout: int = 20) -> bool:
        """Poll page title until Cloudflare JS challenge clears. Returns True if cleared."""
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
            if not title or title in ("", "about:blank"):
                time.sleep(1)
                continue
            return True
        return False

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        driver = self.get_driver()
        flights = []
        try:
            # Enable CDP
            driver.execute_cdp_cmd('Network.enable', {})
            
            print(f"[{self.name}] Navigating to Goibibo homepage...")
            driver.set_page_load_timeout(15)
            try:
                driver.get("https://www.goibibo.com/")
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
                    let closes = document.querySelectorAll('.logSprite, .close, span.close, [class*="close"]');
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
                    let paxClass = document.querySelector('.sc-12foipm-2.eTBlwq') || document.querySelector('.pax-class-count') || document.querySelector('.travelForPopup') || document.querySelector('span.sc-12foipm-51');
                    if (paxClass) { paxClass.click(); }
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
                    let items = document.querySelectorAll('li');
                    for (let item of items) {{
                        if (item.innerText.includes('{target_text}')) {{
                            item.click();
                            break;
                        }}
                    }}
                    let applyBtn = document.querySelector('a.sc-12foipm-73, a.done, button.done');
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
                                print(f"[GOIBIBO-DEBUG] url: {req_url}")
                            if ('search' in req_url or 'intpricedsr' in req_url or 'air-search' in req_url or 'flightsearch' in req_url):
                                accumulated.add(msg['params']['requestId'])
                    except Exception:
                        continue

                for req_id in list(accumulated):
                    try:
                        body_info = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                        body = body_info.get('body', '')
                        if body_info.get('base64Encoded'):
                            import base64
                            import gzip
                            try:
                                decoded = base64.b64decode(body)
                                try:
                                    body = gzip.decompress(decoded).decode('utf-8')
                                except Exception:
                                    body = decoded.decode('utf-8', errors='ignore')
                            except Exception:
                                pass

                        if body and len(body) > 500:
                            parsed = self._parse_api_body(body, origin, destination, advance_window, fare_class)
                            if parsed:
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
            print(f"[{self.name}] Error: {e}")
        finally:
            driver.quit()
            
        return flights


    def _parse_api_body(self, body: str, origin: str, destination: str, advance_window: str, fare_class: str) -> List[Dict]:
        results = []
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                cards = data.get('cardList', []) or data.get('data', {}).get('cardList', [])
                if cards:
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
                            # First try to find the Regular bucket in fareFamilies
                            fb = None
                            fare_families = card.get('fareFamilies', [])
                            if isinstance(fare_families, list):
                                for bucket in fare_families:
                                    if bucket.get('bucketName', '').lower() == 'regular':
                                        fb = bucket.get('fareBreakup', {}).get('fareBreakUpItems', [])
                                        break
                                # If no Regular bucket, take the first one
                                if not fb and fare_families:
                                    fb = fare_families[0].get('fareBreakup', {}).get('fareBreakUpItems', [])
                            
                            # Fallback to root fareBreakup if fareFamilies is empty
                            if not fb:
                                fb = (card.get('fareBreakup') or {}).get('fareBreakUpItems', [])
                                
                            base, taxes, total = 0, 0, 0
                            for item in fb:
                                text = item.get('text', '').lower()
                                amt = re.sub(r'[^\d]', '', re.sub(r'<[^>]+>', '', str(item.get('amount', ''))))
                                if not amt: continue
                                v = int(amt)
                                if 'total' in text: total = v
                                elif 'base' in text: base = v
                                elif 'tax' in text or 'surcharge' in text: taxes += v
                            if total > 0:
                                results.append({'carrier': nm, 'base_fare': base, 'taxes': taxes, 'total_fare': total, 'origin': origin, 'destination': destination, 'advance_window': advance_window, 'fare_class': fare_class})
                        except Exception:
                            pass
        except Exception:
            pass

        if results: return results

        for line in body.splitlines():
            if not line.startswith('data: '): continue
            payload = line[6:]
            if not payload.startswith('{'):
                try:
                    import base64, gzip
                    decoded = base64.b64decode(payload)
                    payload = gzip.decompress(decoded).decode('utf-8')
                except Exception:
                    continue
            try:
                chunk = json.loads(payload)
                cards = chunk.get('cardList', [])
                if cards:
                    for card in (cards[0] if isinstance(cards[0], list) else cards):
                        try:
                            card_str = json.dumps(card).lower()
                            
                            # MoSPI Strict Standard: Premium Cabin Bleed Filter
                            if 'premium economy' in card_str or 'business' in card_str or 'first class' in card_str:
                                continue
                                
                            # MoSPI Strict Standard: Non-stop only
                            if '1 stop' in card_str or '2 stop' in card_str or 'layover' in card_str:
                                continue

                            nm = (card.get('simpleAirlineHeading') or {}).get('nm', 'Unknown')
                            fb = (card.get('fareBreakup') or {}).get('fareBreakUpItems', [])
                            base, taxes, total = 0, 0, 0
                            for item in fb:
                                text = item.get('text', '').lower()
                                amt = re.sub(r'[^\d]', '', re.sub(r'<[^>]+>', '', str(item.get('amount', ''))))
                                if not amt: continue
                                v = int(amt)
                                if 'total' in text: total = v
                                elif 'base' in text: base = v
                                elif 'tax' in text or 'surcharge' in text: taxes += v
                            if total > 0:
                                results.append({'carrier': nm, 'base_fare': base, 'taxes': taxes, 'total_fare': total, 'origin': origin, 'destination': destination, 'advance_window': advance_window, 'fare_class': fare_class})
                        except Exception:
                            pass
            except Exception:
                pass
        return results

    def _scrape_dom(self, driver, origin: str, destination: str, advance_window: str, fare_class: str) -> List[Dict]:
        import time
        from bs4 import BeautifulSoup
        import re
        flights_map = {}
        try:
            for _ in range(12):
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                cards = soup.find_all('div', class_=lambda c: c and ('srp-card' in c or 'listingCard' in c))
                
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
                    text_lower = text.lower()
                    
                    # Fare Class Bleed Filter
                    if fare_class == "Economy" and ('premium economy' in text_lower or 'business' in text_lower or 'first class' in text_lower):
                        continue
                    if fare_class == "Premium Economy" and ('business' in text_lower or 'first class' in text_lower):
                        continue
                    if fare_class == "Business" and 'first class' in text_lower:
                        continue
                    if '1 stop' in text_lower or '2 stop' in text_lower or 'layover' in text_lower:
                        continue
                        
                    price_match = re.search(r'₹\s*([\d,]+)', text)
                    if not price_match:
                        continue
                    price_val = int(price_match.group(1).replace(',', ''))
                    if price_val < 2000 or price_val > 50000:
                        continue
                        
                    carrier = 'Unknown'
                    for airline in ['IndiGo', 'Air India Express', 'Air India', 'SpiceJet', 'Akasa Air', 'Vistara']:
                        if airline.lower() in text.lower():
                            carrier = airline
                            break
                            
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

if __name__ == "__main__":
    spider = Spider()
    res = spider.scrape("DEL", "BOM", "T+15", "Economy", "28/09/2026")
    for f in res[:5]:
        print(f)
