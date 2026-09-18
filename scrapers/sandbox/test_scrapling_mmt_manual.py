import time
from scrapling.fetchers import StealthySession

def setup_interception(page):
    def handle_response(response):
        if "api/search-stream-dt" in response.url:
            print(f"\n[INTERCEPT] Captured response: {response.url}")
            print(f"[INTERCEPT] Content-Type: {response.headers.get('content-type')}")
            try:
                # In playwright sync api, response.body() will block until the body is downloaded.
                # Since search-stream-dt is a streaming endpoint, this will naturally wait for the stream to complete!
                body = response.body()
                print(f"[INTERCEPT] Body length: {len(body)} bytes")
                with open("mmt_stream_body.bin", "wb") as f:
                    f.write(body)
                print("[INTERCEPT] Body written to mmt_stream_body.bin!")
            except Exception as e:
                print(f"[INTERCEPT] Failed to read body: {e}")
                
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
        
        # Give it a bit more time just in case the stream takes long to finish
        time.sleep(10)
        
if __name__ == "__main__":
    capture_mmt_stream()
