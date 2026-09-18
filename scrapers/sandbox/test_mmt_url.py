import time
import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=152)

url = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
print("Navigating to", url)
driver.get(url)
time.sleep(10)
print("Title:", driver.title)
html = driver.page_source
if "DEL" in html and "BOM" in html:
    print("Direct URL search seems to work!")
else:
    print("Did not load results.")
driver.quit()
