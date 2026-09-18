import time
import os
from scrapling.fetchers import StealthySession

init_script_content = """
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const url = args[0] instanceof Request ? args[0].url : (typeof args[0] === 'string' ? args[0] : '');
    const response = await originalFetch.apply(this, args);
    
    if (url && url.includes('search-stream-dt')) {
        const clone = response.clone();
        window.__streamContentType = clone.headers.get('content-type') || 'none';
        clone.text().then(text => {
            window.__streamData = text;
        }).catch(err => {
            window.__streamData = "Error: " + err;
        });
    }
    return response;
};
"""

def extract_data(page):
    print("Inside page_action, waiting 15s for stream to finish...")
    time.sleep(15)
    try:
        content_type = page.evaluate("window.__streamContentType")
        stream_data = page.evaluate("window.__streamData")
        
        print(f"\n--- INTERCEPTED DATA ---")
        print(f"Content-Type: {content_type}")
        if stream_data:
            print(f"Data length: {len(stream_data)} chars")
            print(f"Preview: {stream_data[:500]}")
            with open("mmt_intercepted.txt", "w", encoding="utf-8") as f:
                f.write(stream_data)
            print("Written to mmt_intercepted.txt")
        else:
            print("No data captured. __streamData is empty or undefined.")
    except Exception as e:
        print(f"Failed to evaluate: {e}")

def capture_mmt_stream():
    print("Launching StealthySession with Fetch Override...")
    
    script_path = os.path.abspath("override_fetch.js")
    with open(script_path, "w") as f:
        f.write(init_script_content)
        
    with StealthySession(
        headless=False,
        real_chrome=True,
        init_script=script_path
    ) as session:
        
        print("Navigating to MakeMyTrip...")
        url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        
        page = session.fetch(url, network_idle=True, timeout=60000, page_action=extract_data)
        print(f"Page loaded! Status: {page.status}")

if __name__ == "__main__":
    capture_mmt_stream()
