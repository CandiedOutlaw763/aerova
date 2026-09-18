import time
import json
import undetected_chromedriver as uc
import re

options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=152)

url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
print("Navigating to", url)
driver.get(url)
time.sleep(15)

html = driver.page_source
scripts = re.findall(r'window\.__(?:INITIAL_STATE|MMT_DATA|DATA)__\s*=\s*(\{.+?\})\s*;', html, re.DOTALL)
print("Found scripts:", len(scripts))
if scripts:
    print("Length of first script:", len(scripts[0]))

print("Searching for airline names in DOM:")
airlines = ['IndiGo', 'Air India', 'SpiceJet', 'Akasa', 'Vistara']
for a in airlines:
    print(f"{a}: {html.count(a)}")

driver.quit()
