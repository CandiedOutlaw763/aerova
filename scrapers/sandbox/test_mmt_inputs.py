import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=152)

driver.get("https://www.makemytrip.com/")
time.sleep(10)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
inputs = soup.find_all('input')
for i in inputs:
    print("INPUT id:", i.get('id'), "placeholder:", i.get('placeholder'), "type:", i.get('type'))

driver.quit()
