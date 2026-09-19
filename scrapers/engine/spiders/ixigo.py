"""
Ixigo Spider — XHR/JSON interception via CDP.

Ixigo's SRP fires GET/POST requests to:
  https://www.ixigo.com/api/v2/flight/search (or similar)

The response contains a JSON payload with flight results including
fare breakdown (baseFare, totalFare, taxes).
"""
import json
import time
from typing import List, Dict
import undetected_chromedriver as uc
from .base_uc import UCSpider
from .utils import safe_quit, setup_cdp_limits


class Spider(UCSpider):
    name = "Ixigo"

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        flights_result = []

        # date_str: DD/MM/YYYY -> DDMMYYYY for Ixigo URL
        parts = date_str.split('/')
        ixigo_date = f"{parts[0]}{parts[1]}{parts[2]}"  # 28092026

        cabin_map = {'economy': 'e', 'business': 'b'}
        cabin = cabin_map.get(fare_class.lower(), 'e')

        # Ixigo results URL
        url = (
            f"https://www.ixigo.com/search/result/flight"
            f"?from={origin}&to={destination}&date={ixigo_date}"
            f"&adults=1&children=0&infants=0&class={cabin}&source=Search+Form"
        )

        options = uc.ChromeOptions()
        # No need for performance logs for DOM parsing, but we can keep it
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = uc.Chrome(version_main=152, options=options)

        try:
            print(f"[{self.name}] Navigating to Ixigo results: {url}")
            driver.set_page_load_timeout(30)
            try:
                driver.get(url)
            except Exception:
                pass

            print(f"[{self.name}] Waiting for flight cards to render...")
            
            # Wait for elements to load
            start = time.time()
            while time.time() - start < 45:
                time.sleep(2)
                html = driver.page_source
                if 'Listing_listItem' in html and '₹' in html:
                    time.sleep(3) # allow full render
                    break

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            cards = [div for div in soup.find_all('div') if any('Listing_listItem' in c for c in div.get('class', []))]
            print(f"[{self.name}] Found {len(cards)} flight cards in DOM.")
            
            for card in cards:
                text_parts = list(card.stripped_strings)
                # Clean parts: ignore promotional tags like "Cheapest", "Fastest"
                clean_parts = [p for p in text_parts if p not in ['Cheapest', 'Fastest', 'Early Bird']]
                
                card_text = " ".join(clean_parts).lower()
                # MoSPI Strict Standard: Premium Cabin Bleed Filter
                if 'premium economy' in card_text or 'business' in card_text or 'first class' in card_text:
                    continue
                    
                # MoSPI Strict Standard: Non-stop only
                if '1 stop' in card_text or '2 stop' in card_text or 'layover' in card_text:
                    continue
                
                try:
                    # Usually: [Airline, FlightNum, DepTime, DepCode, Duration, Stops, ArrTime, ArrCode, ₹Price]
                    # Let's find the first occurrence of ₹ to anchor the price
                    price_idx = next((i for i, p in enumerate(clean_parts) if '₹' in p), -1)
                    if price_idx == -1 or price_idx < 8:
                        continue
                        
                    airline = clean_parts[0]
                    # Some promotional tags might still be here, let's do a fallback lookup if airline is not standard
                    carrier_code = "UNKNOWN"
                    if "IndiGo" in airline: carrier_code = "IndiGo"
                    elif "Air-India Express" in airline or "Air India Express" in airline: carrier_code = "Air India Express"
                    elif "Air India" in airline: carrier_code = "Air India"
                    elif "Akasa Air" in airline: carrier_code = "Akasa Air"
                    elif "SpiceJet" in airline: carrier_code = "SpiceJet"
                    elif "Vistara" in airline: carrier_code = "Vistara"
                    else: carrier_code = airline

                    price_str = clean_parts[price_idx].replace('₹', '').replace(',', '').strip()
                    total_fare = int(price_str)
                    
                    # Approximations since Ixigo doesn't show base vs tax cleanly in the main card
                    base_fare = int(total_fare * 0.85)
                    taxes = total_fare - base_fare

                    flights_result.append({
                        'carrier': carrier_code,
                        'airline_name': airline,
                        'base_fare': base_fare,
                        'taxes': taxes,
                        'total_fare': total_fare,
                        'cabin': fare_class.capitalize()
                    })
                except Exception as e:
                    pass

            print(f"[{self.name}] Successfully extracted {len(flights_result)} flights.")

        except Exception as e:
            print(f"[{self.name}] Error: {e}")
        finally:
            safe_quit(driver)

        return flights_result
        try:
            items = None
            if isinstance(data, dict):
                for path in [
                    ['results'], ['data', 'results'], ['flightResults'],
                    ['data', 'flightResults'], ['flights']
                ]:
                    node = data
                    for key in path:
                        if isinstance(node, dict):
                            node = node.get(key)
                        else:
                            node = None
                            break
                    if isinstance(node, list) and len(node) > 0:
                        items = node
                        break

            if not items:
                return results

            seen = set()
            for item in items:
                try:
                    fare = item.get('fare', item.get('price', item.get('totalFare', {})))
                    total, base, taxes = 0, 0, 0

                    if isinstance(fare, dict):
                        total = int(fare.get('totalFare', fare.get('total', fare.get('tf', 0))))
                        base = int(fare.get('baseFare', fare.get('base', fare.get('bf', 0))))
                        taxes = total - base
                    elif isinstance(fare, (int, float)):
                        total = int(fare)

                    if not total:
                        continue

                    # Carrier
                    segs = item.get('segments', item.get('legs', []))
                    code = 'XX'
                    name = 'Unknown'
                    if segs and isinstance(segs[0], dict):
                        seg = segs[0]
                        al = seg.get('airline', seg.get('carrier', {}))
                        if isinstance(al, dict):
                            code = al.get('iataCode', al.get('code', 'XX'))
                            name = al.get('name', code)
                        elif isinstance(al, str):
                            code = al
                            name = al

                    if code in seen:
                        continue
                    seen.add(code)

                    results.append({
                        'carrier': code,
                        'airline_name': name,
                        'base_fare': base,
                        'taxes': taxes,
                        'total_fare': total,
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"[{self.name}] Parse error: {e}")

        return results


if __name__ == '__main__':
    spider = Spider()
    res = spider.scrape('DEL', 'BOM', 'T+15', 'Economy', '28/09/2026')
    for f in res[:10]:
        print(f)
