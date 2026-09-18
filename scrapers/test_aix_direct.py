import requests
import json

def run():
    print("Testing direct AIX API request...")
    url = "https://api.airindiaexpress.com/b2c-flightsearch/v1/search-availability"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.airindiaexpress.com",
        "Referer": "https://www.airindiaexpress.com/"
    }
    
    payload = {
        "searchParams": {
            "paxInfo": {
                "ADT": 1,
                "CHD": 0,
                "INF": 0
            },
            "routes": [
                {
                    "origin": "DEL",
                    "destination": "BOM",
                    "departureDate": "2026-09-30"
                }
            ],
            "cabinClass": "Economy",
            "searchType": "OneWay",
            "isDomestic": True,
            "currencyCode": "INR",
            "language": "en-GB"
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        print("Status Code:", res.status_code)
        if res.status_code == 200:
            print("Response:", res.text[:500])
        else:
            print("Failed Response:", res.text[:500])
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    run()
