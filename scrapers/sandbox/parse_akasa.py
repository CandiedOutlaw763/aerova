import json
from typing import List, Dict

def parse_akasa_json(json_str: str, advance_window: str, fare_class: str) -> List[Dict]:
    data = json.loads(json_str)
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
            
            # also extract the individual tax breakdown
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
                    
                    fares = journey.get("fares", [])
                    if fares:
                        # usually taking the first (lowest) fare
                        fare_key = fares[0].get("fareAvailabilityKey")
                        
                        fare_info = fare_lookup.get(fare_key, {})
                        
                        # Use the service charges if available, otherwise fallback to discountedTotal
                        base_fare = fare_info.get("base_fare", 0)
                        taxes = fare_info.get("taxes", 0)
                        
                        # For some reason in Akasa JSON the sum of taxes + base fare = actual price
                        total_fare = base_fare + taxes
                        
                        # Sometimes discountedTotal is the real price, let's just use our calculated one
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

if __name__ == "__main__":
    with open("sandbox/akasa_sample.json", "r") as f:
        json_data = f.read()
    
    flights = parse_akasa_json(json_data, "T+15", "Economy")
    print(f"Extracted {len(flights)} flights from Akasa JSON:")
    for f in flights:
        print(f"  {f['origin']} -> {f['destination']} | {f['departure_time']} | Base: {f['base_fare']}, Tax: {f['taxes']}, Total: {f['total_fare']}")
