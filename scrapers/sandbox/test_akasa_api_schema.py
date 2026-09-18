import time
import json
import undetected_chromedriver as uc
from datetime import datetime, timedelta

def run():
    options = uc.ChromeOptions()
    driver = uc.Chrome(version_main=152, options=options)
    
    url = "https://prod-bl.qp.akasaair.com/api/ibe/availability/search"
    
    # 3 days from now
    target_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    target_date_t = f"{target_date}T00:00:00"
    
    schemas = [
        {"origin": "DEL", "destination": "BOM", "date": target_date},
        {"origin": "DEL", "destination": "BOM", "date": target_date_t},
        {"stations": {"originStationCode": "DEL", "destinationStationCode": "BOM"}, "beginDate": target_date},
        {"stations": {"origin": "DEL", "destination": "BOM"}, "beginDate": target_date},
        {"departureStation": "DEL", "arrivalStation": "BOM", "date": target_date},
        {"origin": "DEL", "destination": "BOM", "outboundDate": target_date},
    ]
    
    try:
        print("Loading Akasa Air homepage to solve Akamai...")
        driver.get("https://www.akasaair.com/")
        time.sleep(10) # Wait for Akamai sensor to collect telemetry and validate _abck
        
        for i, criteria in enumerate(schemas):
            payload = {
                "passengers": {"types": [{"type": "ADT", "count": 1}], "residentCountry": ""},
                "codes": {"currencyCode": "INR", "promotionCode": ""},
                "criteria": [criteria],
                "numberOfFaresPerJourney": 10,
                "offerCode": None,
                "taxesAndFees": 1
            }
            
            js = f"""
            fetch('{url}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*'
                }},
                body: JSON.stringify({json.dumps(payload)})
            }})
            .then(res => res.json())
            .then(data => {{
                window['fetchResponse_{i}'] = data;
            }})
            .catch(e => {{
                window['fetchResponse_{i}'] = 'ERROR: ' + e;
            }});
            """
            
            driver.execute_script(js)
            print(f"Dispatched fetch {i}...")
            
        print("Waiting for responses...")
        time.sleep(5)
        
        for i, criteria in enumerate(schemas):
            res = driver.execute_script(f"return window['fetchResponse_{i}'];")
            if res and isinstance(res, dict) and "results" in res:
                print(f"SUCCESS with schema {i}: {criteria}")
                with open("akasa_correct_payload.json", "w") as f:
                    f.write(json.dumps(res))
                break
            elif res:
                print(f"Schema {i} returned error/message: {res}")
            else:
                print(f"Schema {i} returned nothing.")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
