from seleniumwire import undetected_chromedriver as uc
import time

def capture_with_selenium_wire():
    print("Launching Selenium-Wire with undetected_chromedriver...")
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(options=options, version_main=152)
    print("Navigating to MakeMyTrip...")
    driver.get("https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E")
    
    print("Waiting 30 seconds for page to load and fetch flights...")
    time.sleep(30)
    
    target_found = False
    for request in driver.requests:
        if request.response and 'search-stream-dt' in request.url:
            print(f"\n[FOUND] URL: {request.url}")
            print(f"[FOUND] Content-Type: {request.response.headers.get('Content-Type', 'None')}")
            try:
                body = request.response.body
                print(f"Body length: {len(body)} bytes")
                with open("mmt_stream_wire.bin", "wb") as f:
                    f.write(body)
                print("Successfully dumped stream response.")
                
                try:
                    text_preview = body.decode('utf-8')[:500]
                    print(f"Preview: {text_preview}")
                except Exception as e:
                    print("Failed to decode as text:", e)
                
                target_found = True
                break
            except Exception as e:
                print("Failed to get body:", e)
                
    if not target_found:
        print("Did not find search-stream-dt response in captured requests.")

    driver.quit()

if __name__ == "__main__":
    capture_with_selenium_wire()
