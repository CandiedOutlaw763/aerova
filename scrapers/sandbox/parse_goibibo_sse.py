import json

def find_prices(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    flights_data = []
    
    for chunk in chunks:
        if isinstance(chunk, dict):
            if 'appendList' in chunk:
                # appendList contains objects with "fll" and "fare"
                for item in chunk['appendList']:
                    fare = item.get('fare', {})
                    if fare:
                        print(f"Fare block found: {fare}")
            
            # Look for something like data or flights
            for k, v in chunk.items():
                if k == 'appendList':
                    for f_item in v:
                        flights_data.append(f_item)

    print(f"Total flights found in appendList: {len(flights_data)}")
    if flights_data:
        print("Sample fare details:")
        print(json.dumps(flights_data[0].get('fare', {}), indent=2))

if __name__ == "__main__":
    find_prices("goibibo_parsed.json")
