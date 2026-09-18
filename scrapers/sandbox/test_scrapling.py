import time
import os
import sys
from scrapling import StealthyFetcher
from datetime import datetime, timedelta

# Fix for windows console emoji issue
sys.stdout.reconfigure(encoding='utf-8')

def test_platforms():
    platforms = {
        "MakeMyTrip": "https://www.makemytrip.com/flights/",
        "Yatra": "https://www.yatra.com/",
        "EaseMyTrip": "https://www.easemytrip.com/",
        "Cleartrip": "https://www.cleartrip.com/flights",
        "Ixigo": "https://www.ixigo.com/",
        "Goibibo": "https://www.goibibo.com/",
        "IndiGo": "https://www.goindigo.in/",
        "AirIndia": "https://www.airindia.com/",
        "AirIndiaExpress": "https://www.airindiaexpress.com/",
        "AkasaAir": "https://www.akasaair.com/",
        "SpiceJet": "https://www.spicejet.com/"
    }

    target_date = datetime.now() + timedelta(days=15)
    print(f"Running Sandbox Test - Target Date (T+15): {target_date.strftime('%Y-%m-%d')}")

    os.makedirs("screenshots", exist_ok=True)
    results = {}

    fetcher = StealthyFetcher(headless=True)
    
    for name, url in platforms.items():
        print(f"\n--- Testing {name} ---")
        try:
            page = fetcher.fetch(url)
            time.sleep(5)
            
            title_elem = page.css('title')
            title = title_elem[0].text if title_elem else "No Title"
            print(f"[{name}] Page Title: {title}")
            
            text = page.text.lower()
            if "cloudflare" in text or "datadome" in text or "access denied" in text or "pardon our interruption" in text or "are you a robot" in text or "captcha" in text:
                print(f"[{name}] [X] BLOCKED by anti-bot.")
                results[name] = "Blocked"
            else:
                print(f"[{name}] [OK] SUCCESS.")
                results[name] = "Success"
        except Exception as e:
            print(f"[{name}] [ERROR] {e}")
            results[name] = f"Error: {str(e)[:50]}"

    print("\n=== FEASIBILITY SUMMARY ===")
    for name, status in results.items():
        print(f"{name}: {status}")

if __name__ == "__main__":
    test_platforms()
