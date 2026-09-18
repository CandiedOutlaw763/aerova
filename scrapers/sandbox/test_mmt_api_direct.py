import undetected_chromedriver as uc
import requests
import time

def run_test():
    print("Launching UC...")
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(version_main=152, options=options)
    
    print("Navigating to MMT homepage to bypass Cloudflare and get cookies...")
    driver.get("https://www.makemytrip.com/")
    time.sleep(8)
    
    # Get cookies
    cookies_list = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
    
    print("Sending direct API request...")
    url = "https://www.makemytrip.com/api/flight/search"
    
    headers = {
        "User-Agent": driver.execute_script("return navigator.userAgent;"),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.makemytrip.com",
        "Referer": "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng",
        "x-device-type": "DESKTOP",
        "x-currency": "INR",
        "x-lang": "eng"
    }
    
    payload = {
        "itinerary": [
            {
                "from": "DEL",
                "to": "BOM",
                "departDate": "28/09/2026"
            }
        ],
        "tripType": "O",
        "paxType": {
            "adults": 1,
            "children": 0,
            "infants": 0
        },
        "cabinClass": "E",
        "fareType": "REGULAR",
        "intl": False,
        "searchType": "SEARCH"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, cookies=cookies_dict, timeout=20)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Try to see if fare details are inside
            import json
            with open("mmt_api_search_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("Successfully saved API response! Length:", len(response.text))
        else:
            print("Response:", response.text[:500])
    except Exception as e:
        print("API Request failed:", e)
        
    driver.quit()

if __name__ == "__main__":
    run_test()
