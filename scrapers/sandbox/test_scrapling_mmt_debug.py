import time
from scrapling.fetchers import StealthySession

def setup_interception(page):
    def handle_response(response):
        if "api/" in response.url:
            print(f"[API Response] {response.url} (Type: {response.request.resource_type})")
            if "search-stream" in response.url:
                print(f"!!! FOUND IT !!! Content-Type: {response.headers.get('content-type')}")
                try:
                    body = response.body()
                    print(f"Body length: {len(body)} bytes")
                    with open("mmt_stream_body.bin", "wb") as f:
                        f.write(body)
                except Exception as e:
                    print(f"Failed to read body: {e}")
                
    page.on("response", handle_response)

def capture_mmt_stream():
    print("Launching StealthySession...")
    
    with StealthySession(
        headless=False,
        real_chrome=True
    ) as session:
        
        print("Navigating to MakeMyTrip...")
        url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        
        page = session.fetch(url, page_setup=setup_interception, network_idle=True, timeout=60000)
        print(f"Page loaded! Status: {page.status}")
        time.sleep(15)
        
if __name__ == "__main__":
    capture_mmt_stream()
