import time
import json
import random
from scrapling.fetchers import StealthySession

extracted_json = None

def handle_response(response):
    global extracted_json
    url = response.url.lower()
    
    # Check for actual flight search API payloads, ignoring generic config
    if 'search' in url or 'flight' in url or 'api' in url:
        if response.request.method != 'OPTIONS' and 'client-config' not in url:
            try:
                body = response.json()
                body_str = str(body).lower()
                # Must contain actual flight listing arrays
                if 'price' in body_str and ('itinerary' in body_str or 'flightlist' in body_str or 'flights' in body_str):
                    print(f"\n[Intercepted Flight API] {response.url}")
                    extracted_json = body
            except:
                pass

def type_like_human(page, text):
    """Type with random human-like jitter using Playwright keyboard"""
    for char in text:
        page.keyboard.type(char, delay=random.randint(50, 200))
        time.sleep(random.uniform(0.05, 0.2))

def mmt_orchestration(page):
    global extracted_json
    print("[UI] Landing on homepage...")
    
    # 1. Listen to all network responses
    page.on("response", handle_response)
    
    # 2. Wait for initial page rendering
    time.sleep(4)
    
    # 3. Handle random popups (Language/Country, Ads)
    # We forcefully delete common MakeMyTrip ad overlays using Javascript
    page.evaluate("""() => {
        document.querySelectorAll('.imageSlideContainer, .modalMain, .close, .langCardClose').forEach(el => el.remove());
    }""")
    print("[UI] Cleared potential overlays.")

    # 4. Use Deep Link for T+15
    try:
        print("[UI] Navigating via Deep Link for T+15 (Sep 28 2026)...")
        deep_link = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        page.goto(deep_link)
    except Exception as e:
        print(f"[UI] Failed to navigate deep link: {e}")
    
    print("[UI] Waiting for results to load...")
    time.sleep(15)
    
    # Extract raw text from HTML
    try:
        raw_text = page.evaluate('document.body.innerText')
        with open("mmt_t15_raw_text.txt", "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"=== SUCCESS: Saved raw text to mmt_t15_raw_text.txt ===")
        
        raw_html = page.content()
        with open("mmt_t15_raw_html.html", "w", encoding="utf-8") as f:
            f.write(raw_html)
    except Exception as e:
        print(f"Error extracting HTML: {e}")


if __name__ == "__main__":
    print("Starting Scrapling StealthySession (Headful Chrome)...")
    with StealthySession(
        headless=False,
        real_chrome=True, 
        solve_cloudflare=True,
        locale="en-IN",
        timezone_id="Asia/Kolkata"
    ) as session:
        try:
            session.fetch("https://www.makemytrip.com/flights/", page_action=mmt_orchestration)
        except Exception as e:
            print(f"Session failed: {e}")
