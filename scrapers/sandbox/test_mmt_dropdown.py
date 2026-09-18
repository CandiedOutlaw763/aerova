import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=152)

driver.get("https://www.makemytrip.com/")
time.sleep(15)

try:
    driver.execute_script("""
        let closes = document.querySelectorAll('.commonModal__close, [data-cy="closeModal"], .close');
        for(let c of closes) { try { c.click(); } catch(e) {} }
    """)
except:
    pass

driver.find_element(By.ID, "fromCity").click()
time.sleep(2)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
inputs = soup.find_all('input')
for i in inputs:
    print("INPUT class:", i.get('class'), "placeholder:", i.get('placeholder'), "type:", i.get('type'))

driver.quit()
