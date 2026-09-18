import undetected_chromedriver as uc
import time
import json

def run_fetch_test():
    print("Launching UC...")
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(version_main=152, options=options)
    
    print("Navigating to MMT homepage...")
    driver.get("https://www.makemytrip.com/")
    time.sleep(10)
    
    # Inject and execute a fetch request from within the browser!
    fetch_script = """
    var callback = arguments[arguments.length - 1];
    
    var payload = {
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
        "intl": false,
        "searchType": "SEARCH"
    };

    fetch('https://www.makemytrip.com/api/flight/search', {
        method: 'POST',
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'x-device-type': 'DESKTOP',
            'x-currency': 'INR',
            'x-lang': 'eng'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => callback({success: true, data: data}))
    .catch(error => callback({success: false, error: error.toString()}));
    """
    
    print("Executing fetch script natively in browser...")
    try:
        # execute_async_script waits for the callback to be called
        driver.set_script_timeout(30)
        result = driver.execute_async_script(fetch_script)
        
        if result.get("success"):
            print("Successfully fetched data!")
            with open("mmt_api_fetch_response.json", "w", encoding="utf-8") as f:
                json.dump(result["data"], f, indent=2)
            print("Saved to mmt_api_fetch_response.json")
        else:
            print("Fetch failed:", result.get("error"))
            
    except Exception as e:
        print("Script execution failed:", e)
        
    driver.quit()

if __name__ == "__main__":
    run_fetch_test()
