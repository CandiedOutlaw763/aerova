import time
import os
from scrapling.fetchers import StealthySession

responses_log = []

def setup_interception(page):
    def handle_response(response):
        # We can't safely read body here without blocking/failing, so just log URLs
        responses_log.append(f"{response.url} | TYPE: {response.request.resource_type} | STATUS: {response.status}")
    page.on("response", handle_response)

def capture_mmt_urls():
    print("Launching StealthySession...")
    
    with StealthySession(
        headless=False,
        real_chrome=True
    ) as session:
        
        print("Navigating to MakeMyTrip...")
        url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        
        page = session.fetch(url, page_setup=setup_interception, network_idle=True, timeout=60000)
        print(f"Page loaded! Status: {page.status}")
        
        time.sleep(10)
        
    print(f"Total responses: {len(responses_log)}")
    with open("mmt_all_responses.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(responses_log))
    print("Wrote all URLs to mmt_all_responses.txt")

if __name__ == "__main__":
    capture_mmt_urls()
