import json

def extract_prices():
    try:
        with open('mmt_flight_data_intercepted.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        flights = []
        
        def search_dict(d):
            if isinstance(d, dict):
                # Check if this dict looks like a flight segment
                flight_num = d.get('flightNumber') or d.get('fltNo') or d.get('fn')
                airline = d.get('airlineName') or d.get('al') or d.get('airline')
                
                # Check for price
                price = None
                if 'price' in d: price = d['price']
                elif 'fare' in d: 
                    if isinstance(d['fare'], dict): price = d['fare'].get('totalFare') or d['fare'].get('grossAmount')
                    else: price = d['fare']
                elif 'totalPrice' in d: price = d['totalPrice']
                
                if flight_num and airline and price:
                    flights.append(f"{airline} {flight_num}: ₹{price}")
                
                for k, v in d.items():
                    search_dict(v)
            elif isinstance(d, list):
                for item in d:
                    search_dict(item)

        search_dict(data)
        
        # Deduplicate and print
        unique_flights = list(set(flights))
        if unique_flights:
            print("=== MMT T+15 FLIGHTS (DEL-BOM, Sept 28 2026) ===")
            for f in sorted(unique_flights)[:15]:
                print(f)
        else:
            print("Could not find standard flight/price structures.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_prices()
