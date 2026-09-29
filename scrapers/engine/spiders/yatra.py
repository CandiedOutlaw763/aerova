import undetected_chromedriver as uc
import time
import json
import urllib.parse
from typing import List, Dict
from .base_uc import UCSpider
from .utils import safe_quit, setup_cdp_limits


class Spider(UCSpider):
    name = "Yatra"

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        flights_result = []

        options = uc.ChromeOptions()
        driver = uc.Chrome(version_main=153, options=options)
        setup_cdp_limits(driver)

        try:
            print(f"[{self.name}] Navigating to Yatra homepage to bypass Akamai...")
            driver.get("https://www.yatra.com/")
            time.sleep(8)

            encoded_date = urllib.parse.quote(date_str, safe='')
            cabin = "Economy" if fare_class.lower() == "economy" else "Business"
            
            deep_link = (
                f"https://flight.yatra.com/air-search-ui/dom2/trigger"
                f"?type=O&viewName=normal&flexi=0&noOfSegments=1"
                f"&origin={origin}&originCountry=IN"
                f"&destination={destination}&destinationCountry=IN"
                f"&flight_depart_date={encoded_date}"
                f"&ADT=1&CHD=0&INF=0&class={cabin}&source=fresco-home&version=1.1"
            )

            print(f"[{self.name}] Executing Deep Link...")
            driver.get(deep_link)

            print(f"[{self.name}] Polling for 35s to allow all airline XHRs to render into DOM...")
            time.sleep(35)
            
            html = driver.page_source
            from bs4 import BeautifulSoup
            import re
            soup = BeautifulSoup(html, 'lxml')
            
            cards = soup.find_all('div', class_=re.compile('result-set|flightItem'))
            
            for card in cards:
                try:
                    airline_tag = card.find('span', title=True)
                    if not airline_tag: continue
                    airline_name = airline_tag.get('title')
                    
                    fl_num_elem = card.find('p', class_='normal fs-12 font-lightgrey fl-no')
                    fl_num = fl_num_elem.text.strip() if fl_num_elem else ''
                    
                    card_text = card.get_text(separator=' ', strip=True).lower()
                    
                    # MoSPI Strict Standard: Premium Cabin Bleed Filter
                    if 'premium economy' in card_text or 'business' in card_text or 'first class' in card_text:
                        continue
                        
                    # MoSPI Strict Standard: Non-stop only
                    if '1 stop' in card_text or '2 stop' in card_text or 'layover' in card_text:
                        continue
                    
                    price_elem = card.find('p', class_='ow-price-above-btn')
                    if not price_elem:
                        price_elem = card.find('div', class_=re.compile('fare-amount|price'))
                    if not price_elem: continue
                        
                    price_str = price_elem.text.strip()
                    total_fare = int(re.sub(r'\D', '', price_str))
                    
                    flights_result.append({
                        'carrier': fl_num.split('-')[0].strip() if '-' in fl_num else airline_name,
                        'airline_name': airline_name,
                        'flight_number': fl_num,
                        'total_fare': total_fare,
                        'cabin': fare_class
                    })
                except Exception as e:
                    pass
                    
            print(f"[{self.name}] DOM Parsing extracted {len(flights_result)} flights.")

        except Exception as e:
            print(f"[{self.name}] Error scraping: {e}")
        finally:
            safe_quit(driver)

        return flights_result



if __name__ == "__main__":
    spider = Spider()
    res = spider.scrape("DEL", "BOM", "T+15", "Economy", "28/09/2026")
    for f in res[:10]:
        print(f)
