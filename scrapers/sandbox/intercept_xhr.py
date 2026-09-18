import asyncio
import json
import os
from playwright.async_api import async_playwright

async def intercept_flights(platform_name, url):
    print(f"\n{'='*50}")
    print(f"Intercepting XHR for {platform_name}")
    print(f"{'='*50}")
    
    os.makedirs("intercepted", exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser (not headless so we can bypass simple bot checks if needed, but headless=True for now)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        async def handle_response(response):
            if response.request.resource_type in ["fetch", "xhr"]:
                try:
                    # Ignore tiny responses and preflights
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type.lower():
                            body = await response.text()
                            if len(body) > 2000: # Lowered threshold to 2KB
                                req_url = response.url
                                print(f"[{platform_name}] 🎯 Found JSON payload! Size: {len(body)} bytes -> {req_url}")
                                
                                safe_url = req_url.split('?')[0].split('/')[-1]
                                if not safe_url:
                                    safe_url = "api"
                                filename = f"intercepted/{platform_name}_{safe_url}_{len(body)}.json"
                                with open(filename, "w", encoding="utf-8") as f:
                                    f.write(body)
                except Exception as e:
                    pass
                    
        page.on("response", handle_response)
        
        try:
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="load", timeout=60000)
            print("Page loaded. Waiting 20 seconds for AJAX...")
            await asyncio.sleep(20)
        except Exception as e:
            print(f"Navigation error: {e}")
            
        await browser.close()

async def main():
    # Test Cleartrip and EaseMyTrip
    urls = {
        "Cleartrip": "https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date=28/09/2026&from=DEL&to=BOM",
        "EaseMyTrip": "https://flight.easemytrip.com/FlightList/Index?srch=DEL-DEL-India|BOM-BOM-India|28/09/2026&px=1-0-0&ccls=0&isow=true"
    }
    
    for name, url in urls.items():
        await intercept_flights(name, url)

if __name__ == "__main__":
    asyncio.run(main())
