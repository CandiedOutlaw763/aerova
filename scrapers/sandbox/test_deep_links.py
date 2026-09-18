import os
import json
import time
from scrapling.fetchers import StealthySession

platforms = {
    "MakeMyTrip": "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E",
    "Goibibo": "https://www.goibibo.com/flights/air-DEL-BOM-20260928--1-0-0-E-D/",
    "Yatra": "https://flight.yatra.com/air-search-ui/dom2/trigger?type=O&viewName=normal&flexi=0&noOfSegments=1&origin=DEL&originCountry=IN&destination=BOM&destinationCountry=IN&flight_depart_date=28/09/2026&ADT=1&CHD=0&INF=0&class=Economy",
    "Cleartrip": "https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date=28/09/2026&from=DEL&to=BOM",
    "EaseMyTrip": "https://flight.easemytrip.com/FlightList/Index?srch=DEL-Delhi-India|BOM-Mumbai-India|28/09/2026&px=1-0-0&cbn=0&ar=undefined&isapi=N&apptype=B2C",
    "Ixigo": "https://www.ixigo.com/search/result/flight?from=DEL&to=BOM&date=28092026&returnDate=&adults=1&children=0&infants=0&class=e&source=Search%20Form",
    "SpiceJet": "https://www.spicejet.com/search?from=DEL&to=BOM&tripType=1&departure=2026-09-28&adult=1&child=0&infant=0&currency=INR",
    "AirIndia": "https://www.airindia.com/in/en/book/search-flights.html?journeyType=oneway&origin=DEL&destination=BOM&departDate=2026-09-28&adults=1",
    "AirIndiaExpress": "https://www.airindiaexpress.com/search?origin=DEL&destination=BOM&departureDate=2026-09-28",
    "AkasaAir": "https://www.akasaair.com/search?origin=DEL&destination=BOM&departureDate=2026-09-28",
    "IndiGo": "https://www.goindigo.in/booking/flight-select.html" # May require POST, we'll try deep link or intercept
}

os.makedirs("intercepted", exist_ok=True)

def parse_and_dump_xhr(page, site_name):
    print(f"[{site_name}] Waiting for network XHR responses...")
    # Scrapling page has intercepted XHRs accessible via Playwright's network hooks?
    # Actually, we can just use page.on("response") like we did in the MMT test!
    pass # we'll bind the handler below

def run_all():
    global current_site
    with StealthySession(headless=False, real_chrome=True, locale="en-IN", timezone_id="Asia/Kolkata", solve_cloudflare=True) as session:
        for name, url in platforms.items():
            print(f"\n======================================")
            print(f"Testing {name} deep link...")
            current_site = name
            global site_data
            site_data = None
            
            def handle_response(response):
                global site_data
                url_str = response.url.lower()
                if ('search' in url_str or 'flight' in url_str or 'api' in url_str or 'fare' in url_str or 'graphql' in url_str):
                    if response.request.method != 'OPTIONS':
                        try:
                            body = response.json()
                            bstr = str(body).lower()
                            if 'price' in bstr or 'fare' in bstr or 'amount' in bstr:
                                if 'airline' in bstr or 'itinerary' in bstr or 'flight' in bstr:
                                    print(f"[{current_site}] Intercepted API: {response.url}")
                                    site_data = body
                        except:
                            pass

            try:
                base_url = "https://" + url.split("/")[2]
                print(f"[{current_site}] Hitting homepage {base_url} first to establish session...")
                session.fetch(base_url)
                time.sleep(3)
                
                # We can inject the handler manually via session.page if it exists, or just pass a page_action
                def action(page):
                    page.on("response", handle_response)
                    time.sleep(12) # wait 12 seconds for the search to complete
                
                print(f"[{current_site}] Hitting deep link...")
                session.fetch(url, page_action=action)
                
                if site_data:
                    with open(f"intercepted/{name}.json", "w", encoding="utf-8") as f:
                        json.dump(site_data, f)
                    print(f"[{name}] Saved JSON data.")
                else:
                    print(f"[{name}] No relevant flight data intercepted.")
            except Exception as e:
                print(f"[{name}] ERROR: {e}")

if __name__ == "__main__":
    run_all()
