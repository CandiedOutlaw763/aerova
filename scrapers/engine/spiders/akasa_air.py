import json
from typing import List, Dict
from .base_uc import UCSpider

class Spider(UCSpider):
    name = "Akasa Air"

    def parse_akasa_json(self, json_str: str, advance_window: str, fare_class: str) -> List[Dict]:
        data = json.loads(json_str)
        if "data" in data and isinstance(data["data"], dict):
            data = data["data"]
            
        flights = []
        
        # 1. Build a lookup for fare details
        fare_lookup = {}
        if "faresAvailable" in data:
            for f in data["faresAvailable"]:
                key = f["key"]
                fare_lookup[key] = {
                    "discountedTotal": f["value"]["totals"]["discountedTotal"],
                    "fareTotal": f["value"]["totals"]["fareTotal"],
                    "publishedTotal": f["value"]["totals"]["publishedTotal"],
                }
                
                try:
                    service_charges = f["value"]["fares"][0]["passengerFares"][0]["serviceCharges"]
                    base_fare = 0
                    taxes = 0
                    for charge in service_charges:
                        if charge["type"] == "FarePrice":
                            base_fare += charge["amount"]
                        elif charge["type"] == "TravelFee":
                            taxes += charge["amount"]
                    fare_lookup[key]["base_fare"] = base_fare
                    fare_lookup[key]["taxes"] = taxes
                except:
                    fare_lookup[key]["base_fare"] = f["value"]["totals"]["discountedTotal"]
                    fare_lookup[key]["taxes"] = 0

        # 2. Iterate through journeys to find flights
        if "results" in data and len(data["results"]) > 0:
            trips = data["results"][0].get("trips", [])
            for trip in trips:
                journeys_by_market = trip.get("journeysAvailableByMarket", [])
                for market in journeys_by_market:
                    journeys = market.get("value", [])
                    
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
                        if len(journey.get('segments', [])) > 1:
                            continue
                        
                        fares = journey.get("fares", [])
                        if fares:
                            fare_key = fares[0].get("fareAvailabilityKey")
                            fare_info = fare_lookup.get(fare_key, {})
                            
                            base_fare = fare_info.get("base_fare", 0)
                            taxes = fare_info.get("taxes", 0)
                            total_fare = base_fare + taxes
                            
                            if total_fare == 0:
                                total_fare = fare_info.get("discountedTotal", 0)
                                
                            flights.append({
                                "origin": origin,
                                "destination": destination,
                                "carrier": "Akasa Air (QP)",
                                "departure_time": departure,
                                "arrival_time": arrival,
                                "advance_window": advance_window,
                                "fare_class": fare_class,
                                "base_fare": base_fare,
                                "taxes": taxes,
                                "total_fare": total_fare
                            })
                            
        return flights

    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        import datetime
        print(f"[{self.name}] Scraping API for {origin} -> {destination} on {date_str}...")
        
        # Convert DD-MMM-YYYY or DD/MM/YYYY to YYYY-MM-DDT00:00:00
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
            
        formatted_date = dt.strftime("%Y-%m-%dT00:00:00")
        
        payload = {
            "criteria": [{
                "stations": {
                    "originStationCodes": [origin],
                    "destinationStationCodes": [destination],
                    "searchDestinationMacs": True,
                    "searchOriginMacs": True
                },
                "dates": {
                    "beginDate": formatted_date
                },
                "filters": {
                    "compressionType": 1,
                    "maxConnections": 8,
                    "productClasses": ["NB", "LB", "EC", "AV"],
                    "fareTypes": ["NB", "LB", "R", "V"]
                }
            }],
            "passengers": {
                "types": [{"type": "ADT", "count": 1}],
                "residentCountry": ""
            },
            "codes": {
                "currencyCode": "INR",
                "promotionCode": ""
            },
            "offerCode": None,
            "numberOfFaresPerJourney": 10,
            "taxesAndFees": 1
        }

        flights = []
        driver = self.get_driver()
        
        try:
            print(f"[{self.name}] Loading homepage to generate Akamai session cookies...")
            driver.get("https://www.akasaair.com/")
            
            import time
            time.sleep(10) # Essential for Akamai telemetry gathering
            
            print(f"[{self.name}] Executing background API POST request...")
            
            js_script = f"""
            var done = arguments[0];
            fetch('https://prod-bl.qp.akasaair.com/api/ibe/availability/search', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*'
                }},
                body: JSON.stringify({json.dumps(payload)})
            }})
            .then(res => res.json())
            .then(data => done(data))
            .catch(e => done({{"error": e.toString()}}));
            """
            
            # Using execute_async_script to wait for the fetch promise to resolve
            response_json = driver.execute_async_script(js_script)
            
            if response_json and "error" not in response_json:
                print(f"[{self.name}] Payload captured successfully. Raw JSON sample:")
                print(str(response_json)[:1000])
                flights = self.parse_akasa_json(json.dumps(response_json), advance_window, fare_class)
            else:
                print(f"[{self.name}] API request failed: {response_json}")
                
        except Exception as e:
            print(f"[{self.name}] Scraping failed: {e}")
        finally:
            from .utils import safe_quit
            safe_quit(driver)

        return flights
