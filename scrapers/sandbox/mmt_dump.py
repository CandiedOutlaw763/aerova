import time
from scrapling.fetchers import StealthySession

def mmt_dump(page):
    time.sleep(4)
    # Remove overlays
    page.evaluate("""() => {
        document.querySelectorAll('.imageSlideContainer, .modalMain, .close, .langCardClose').forEach(el => el.remove());
    }""")
    
    print("[UI] Clicking Origin...")
    page.locator('label[for="fromCity"]').click(force=True)
    time.sleep(2)
    
    html = page.content()
    with open("mmt_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Dumped HTML to mmt_debug.html")

if __name__ == "__main__":
    with StealthySession(
        headless=False,
        real_chrome=True,
        solve_cloudflare=True,
        locale="en-IN",
        timezone_id="Asia/Kolkata"
    ) as session:
        session.fetch("https://www.makemytrip.com/flights/", page_action=mmt_dump)
