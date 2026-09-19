import json
import re
import time
from typing import List, Dict
import undetected_chromedriver as uc
from .base_uc import UCSpider
from .utils import safe_quit, setup_cdp_limits

class Spider(UCSpider):
    name = "EaseMyTrip"

    AIRLINE_MAP = {
        '6E': 'IndiGo',
        'AI': 'Air India',
        'SG': 'SpiceJet',
        'UK': 'Vistara',
        'QP': 'Akasa Air',
        'I5': 'Air India Express',
        'IX': 'Air India Express',
        'G8': 'Go First',
        'S5': 'Star Air',
        'ZO': 'zoom air',
    }

    def _parse(self, origin, destination, advance_window, fare_class, logs):
        flights = []

        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if log['method'] == 'Network.responseReceived':
                    resp = log['params']['response']
                    url = resp['url']

                    if 'AirAvail_Lights' in url:
                        body_data = self.driver.execute_cdp_cmd(
                            'Network.getResponseBody',
                            {'requestId': log['params']['requestId']}
                        )
                        body = body_data['body']
                        data = json.loads(body)

                        if 'j' not in data or not data['j'] or 's' not in data['j'][0]:
                            continue

                        for f in data['j'][0]['s']:
                            try:
                                f_str = json.dumps(f).lower()
                                
                                # MoSPI Strict Standard: Premium Cabin Bleed Filter
                                if 'premium economy' in f_str or 'business' in f_str or 'first class' in f_str:
                                    continue
                                    
                                # MoSPI Strict Standard: Non-stop only
                                if '1 stop' in f_str or '2 stop' in f_str or '1-stop' in f_str or '2-stop' in f_str or 'layover' in f_str:
                                    continue
                                if len(f.get('segKeyArr', [])) > 1:
                                    continue
                                
                                base  = f.get('AP', 0)
                                taxes = f.get('TT', 0)
                                total = f.get('TF', f.get('PT', 0))

                                seg_key = f.get('segMatchingKey', '')
                                if not seg_key:
                                    continue

                                # segMatchingKey looks like "6E2334DEL-BOM" — grab leading 2-char IATA code
                                m = re.match(r'^([A-Z][A-Z0-9])', seg_key)
                                if not m:
                                    continue

                                code = m.group(1)
                                carrier = self.AIRLINE_MAP.get(code, code)

                                flights.append({
                                    'origin': origin,
                                    'destination': destination,
                                    'carrier': carrier,
                                    'airline_name': carrier,
                                    'advance_window': advance_window,
                                    'fare_class': fare_class,
                                    'base_fare': base,
                                    'taxes': taxes,
                                    'total_fare': total,
                                })
                            except Exception:
                                pass

                        print(f"[{self.name}] Extracted {len(flights)} flights from API JSON")
                        return flights
            except Exception:
                pass

        return flights

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        flights_result = []

        # EaseMyTrip URL expects date as DD/MM/YYYY — that's already the format we pass
        url = (
            f"https://www.easemytrip.com/flight-search/listing"
            f"?srch={origin}-Any-|{destination}-Any-|{date_str}"
            f"&px=1-0-0&cbn=0&ar=undefined&isow=true&isdm=true"
            f"&lang=en-us&&IsDoubleSeat=false&CCODE=IN&curr=INR&apptype=B2C"
        )

        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = uc.Chrome(version_main=152, options=options)
        setup_cdp_limits(self.driver)

        try:
            print(f"[{self.name}] Navigating to EaseMyTrip results...")
            self.driver.set_page_load_timeout(15)
            try:
                self.driver.get(url)
            except Exception:
                pass

            print(f"[{self.name}] Polling 40s for flight API response...")

            start_time = time.time()
            while time.time() - start_time < 40:
                logs = self.driver.get_log('performance')
                flights_result = self._parse(origin, destination, advance_window, fare_class, logs)
                if flights_result:
                    break
                time.sleep(2)

        except Exception as e:
            print(f"[{self.name}] Error: {e}")
        finally:
            safe_quit(self.driver)

        return flights_result
