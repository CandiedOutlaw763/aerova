import json
import sys

def parse():
    try:
        with open('../../mmt_flight_data_intercepted.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # MMT json structure is often deeply nested.
        # Usually it's in data -> flightList or similar.
        flights = None
        
        # Search recursively for something that looks like an itinerary list
        def find_flights(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'itinerary' and isinstance(v, list) and len(v) > 0:
                        return v
                    if k == 'flightList' and isinstance(v, list) and len(v) > 0:
                        return v
                    if k == 'flights' and isinstance(v, list) and len(v) > 0:
                        return v
                    if k == 'journeyList' or k == 'itineraryList':
                        return v
                    res = find_flights(v)
                    if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_flights(item)
                    if res: return res
            return None

        # Just do a rough extraction: Find all dicts with 'fare' or 'price' and 'flightNumber'
        results = []
        def find_prices(obj):
            if isinstance(obj, dict):
                # if this dict represents a flight
                flight_no = obj.get('flightNumber') or obj.get('fn')
                airline = obj.get('airline') or obj.get('al') or obj.get('airlineName')
                
                # Check for prices
                price = None
                fare = obj.get('fare')
                if isinstance(fare, dict):
                    price = fare.get('totalFare') or fare.get('grossAmount')
                if not price:
                    price = obj.get('price') or obj.get('totalPrice') or obj.get('priceDetail', {}).get('totalFare')
                    
                if flight_no and price:
                    results.append({'flight': f"{airline} {flight_no}", 'price': price, 'raw': obj})
                
                for k, v in obj.items():
                    find_prices(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_prices(item)

        find_prices(data)
        
        if not results:
            print("Could not find standard flight/price keys. Please inspect JSON structure.")
        else:
            print(f"Found {len(results)} flight price entries.")
            # Print top 15
            for r in results[:15]:
                print(f"Flight: {r['flight']} | Price: ₹{r['price']}")
                
    except Exception as e:
        print(f"Error parsing JSON: {e}")

if __name__ == "__main__":
    parse()
