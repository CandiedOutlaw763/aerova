import re
import json

def extract():
    with open('mmt_flight_data_intercepted.json', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Extract anything that looks like "totalFare": 6500, or similar
    fares = re.findall(r'"(totalFare|price|totalPrice|amount|grossAmount)"\s*:\s*(\d+)', text)
    # Extract anything that looks like "flightNumber": "123"
    flights = re.findall(r'"(flightNumber|fltNo|fn)"\s*:\s*"([A-Z0-9]+)"', text)
    
    print("Top fares found:")
    for f in sorted(list(set(fares)), key=lambda x: int(x[1]))[:10]:
        print(f"₹{f[1]}")
        
    print("\nFlight Numbers found:")
    print(list(set([f[1] for f in flights]))[:10])

if __name__ == "__main__":
    extract()
