import json

def parse_spicejet(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    journeys = data['data']['trips'][0]['journeysAvailable']
    fares_available = data['data']['faresAvailable']
    
    parsed_flights = []
    
    for journey in journeys:
        departure = journey['designator']['departure']
        arrival = journey['designator']['arrival']
        flight_num = journey['carrierString']
        
        # Find the cheapest fare
        cheapest_price = float('inf')
        for fare_key, fare_info in journey.get('fares', {}).items():
            if fare_key in fares_available:
                fare_details = fares_available[fare_key]
                passengers = fare_details.get('passengerFares', [])
                if passengers:
                    price = passengers[0].get('fareAmount', float('inf'))
                    if price < cheapest_price:
                        cheapest_price = price
        
        parsed_flights.append({
            'flight_number': flight_num,
            'departure': departure,
            'arrival': arrival,
            'price': cheapest_price if cheapest_price != float('inf') else None
        })
        
    for pf in parsed_flights:
        print(pf)

if __name__ == "__main__":
    parse_spicejet("spicejet_api_3.json")
