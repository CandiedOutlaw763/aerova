from playwright.sync_api import sync_playwright
import time
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        page = context.new_page()
        
        captured_data = {}
        
        def handle_response(response):
            if "api/flight/search" in response.url or "v2/flight/search" in response.url:
                print(f"Intercepted API URL: {response.url}")
                try:
                    req = response.request
                    captured_data['url'] = req.url
                    captured_data['method'] = req.method
                    captured_data['headers'] = req.headers
                    captured_data['post_data'] = req.post_data
                    
                    body = response.json()
                    with open("mmt_api_payload.json", "w") as f:
                        json.dump(captured_data, f, indent=2)
                    with open("mmt_api_response.json", "w") as f:
                        json.dump(body, f, indent=2)
                    print("Successfully saved API payload and response.")
                except Exception as e:
                    print("Error parsing response:", e)

        page.on("response", handle_response)
        
        print("Navigating to MMT...")
        page.goto("https://www.makemytrip.com/")
        time.sleep(5)
        
        print("Navigating to deep link...")
        page.goto("https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E")
        
        time.sleep(15)
        
        browser.close()

if __name__ == "__main__":
    run()
