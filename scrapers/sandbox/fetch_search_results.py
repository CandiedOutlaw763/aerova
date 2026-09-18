import os
import time
from datetime import datetime, timedelta
from scrapling import StealthyFetcher
import urllib.parse

def generate_urls(origin, destination, date_str):
    # date_str format: YYYY-MM-DD
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dd_mm_yyyy = dt.strftime("%d/%m/%Y")
    dd_mm_yyyy_dash = dt.strftime("%d-%m-%Y")
    ddmmyyyy = dt.strftime("%d%m%Y")
    yyyymmdd = dt.strftime("%Y%m%d")
    
    urls = {
        "MakeMyTrip": f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{dd_mm_yyyy}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E",
        "Yatra": f"https://flight.yatra.com/air-search-ui/dom2/trigger?type=O&viewName=normal&flexi=0&noOfSegments=1&origin={origin}&originCountry=IN&destination={destination}&destinationCountry=IN&flight_depart_date={dd_mm_yyyy}&ADT=1&CHD=0&INF=0&class=Economy",
        "EaseMyTrip": f"https://flight.easemytrip.com/FlightList/Index?srch={origin}-{origin}-India|{destination}-{destination}-India|{dd_mm_yyyy}&px=1-0-0&ccls=0&isow=true",
        "Cleartrip": f"https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date={dd_mm_yyyy}&from={origin}&to={destination}",
        "Ixigo": f"https://www.ixigo.com/search/result/flight?from={origin}&to={destination}&date={ddmmyyyy}&returnDate=&adults=1&children=0&infants=0&class=e",
        "Goibibo": f"https://www.goibibo.com/flights/air-{origin}-{destination}-{yyyymmdd}-1-0-0-E-D/",
        "IndiGo": f"https://www.goindigo.in/booking/flight-select.html?tripType=1&origin={origin}&destination={destination}&departDate={dd_mm_yyyy_dash}&pax=1",
        "AirIndia": f"https://www.airindia.com/in/en/book/search-flights/flight-search.html?journeyType=oneway&origin={origin}&destination={destination}&departDate={date_str}&adults=1",
        "AirIndiaExpress": f"https://www.airindiaexpress.com/search?tripType=O&origin={origin}&destination={destination}&departDate={date_str}&adults=1",
        "AkasaAir": f"https://book.akasaair.com/search?origin={origin}&destination={destination}&departureDate={date_str}&adults=1",
        "SpiceJet": f"https://book.spicejet.com/Search.aspx?originStation={origin}&destinationStation={destination}&departureDate={date_str}"
    }
    return urls

def fetch_doms():
    origin = "DEL"
    destination = "BOM"
    target_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
    
    urls = generate_urls(origin, destination, target_date)
    os.makedirs("doms", exist_ok=True)
    
    fetcher = StealthyFetcher(headless=True)
    
    for name, url in urls.items():
        print(f"\n--- Fetching {name} ---")
        print(f"URL: {url}")
        try:
            page = fetcher.fetch(url)
            # Wait 15 seconds to allow flight results (AJAX) to load
            time.sleep(15)
            
            html = page.html_content
            
            if not html:
                print(f"[{name}] WARNING: html_content is empty. Falling back to body text if any.")
                html = page.text if page.text else ""
                
            filepath = f"doms/{name}.html"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
                
            print(f"[{name}] Saved DOM ({len(html)} bytes) to {filepath}")
        except Exception as e:
            print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    fetch_doms()
