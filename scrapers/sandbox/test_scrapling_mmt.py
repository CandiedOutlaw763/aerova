import time
import os
from scrapling.fetchers import StealthySession

def capture_mmt_stream():
    print("Launching StealthySession...")
    # Capture the specific stream endpoint
    xhr_pattern = r".*api/search-stream-dt.*"
    
    with StealthySession(
        headless=False,
        capture_xhr=xhr_pattern,
        real_chrome=True # Optional but helps with evasion
    ) as session:
        
        print("Navigating to MakeMyTrip...")
        # Load the page and wait for the network to idle
        url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        
        page = session.fetch(url, network_idle=True, timeout=60000)
        
        print(f"Page loaded! Status: {page.status}")
        
        # Wait a bit extra to ensure streaming finishes
        time.sleep(15)
        
        print(f"Captured {len(page.captured_xhr)} XHR responses matching pattern.")
        
        for i, xhr in enumerate(page.captured_xhr):
            print(f"\n--- XHR {i} ---")
            print(f"URL: {xhr.url}")
            print(f"Status: {xhr.status}")
            print(f"Content-Type: {xhr.headers.get('content-type', 'N/A')}")
            
            body = xhr.body
            print(f"Body length: {len(body)} bytes")
            
            # Save the raw body
            filename = f"mmt_stream_body_{i}.bin"
            with open(filename, "wb") as f:
                f.write(body)
            print(f"Saved raw body to {filename}")
            
            # If text, try to decode first 500 chars
            try:
                text_preview = body.decode('utf-8')[:500]
                print(f"Preview: {text_preview}")
            except:
                print("Could not decode as utf-8 text.")

if __name__ == "__main__":
    capture_mmt_stream()
