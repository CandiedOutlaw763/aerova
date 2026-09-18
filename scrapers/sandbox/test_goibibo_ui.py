import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def test_goibibo():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options)
    
    print("Navigating to Goibibo...")
    driver.get("https://www.goibibo.com/")
    time.sleep(5)
    
    driver.save_screenshot("goibibo_home.png")
    
    with open('goibibo_home.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
        
    driver.quit()
    print("Done")

if __name__ == "__main__":
    test_goibibo()
