import requests
import json

def run():
    print("Testing IndiGo API with user_key...")
    
    url = "https://api-prod-flight-skyplus6e.goindigo.in/v2/flight/search"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "user_key": "43b557c03fc85cc213e91df0f526cc7a",
        "Ocp-Apim-Subscription-Key": "43b557c03fc85cc213e91df0f526cc7a", # Azure API Management
        "Origin": "https://www.goindigo.in",
        "Referer": "https://www.goindigo.in/"
    }
    
    payload = {
        "codes": {
            "currency": "INR",
            "promotionCode": ""
        },
        "criteria": [
            {
                "dates": {
                    "beginDate": "2026-09-30"
                },
                "flightFilters": {
                    "type": "All"
                },
                "stations": {
                    "originStationCodes": ["DEL"],
                    "destinationStationCodes": ["BOM"]
                }
            }
        ],
        "passengers": {
            "residentCountry": "IN",
            "types": [
                {
                    "count": 1,
                    "discountCode": "",
                    "type": "ADT"
                }
            ]
        },
        "taxesAndFees": "TaxesAndFees",
        "tripCriteria": "oneWay",
        "isRedeemTransaction": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print("Response JSON keys:", list(data.keys()))
            if "data" in data and "trips" in data["data"]:
                print("Trips found:", len(data["data"]["trips"]))
        except:
            print("Response text:", response.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
