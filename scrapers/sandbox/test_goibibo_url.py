import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def test_goibibo():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options)
    
    url = "https://www.goibibo.com/flights/air-DEL-BOM-20260928--1-0-0-E-D/"
    print(f"Navigating to {url}")
    driver.get(url)
    
    time.sleep(10)
    print(f"Title: {driver.title}")
    
    with open('goibibo_test.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
        
    driver.quit()
    print("Done")

if __name__ == "__main__":
    test_goibibo()
