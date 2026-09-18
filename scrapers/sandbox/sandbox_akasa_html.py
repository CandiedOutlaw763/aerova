import sys
import os
import json
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def run():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(version_main=152, options=options)
    
    try:
        driver.get("https://www.akasaair.com/")
        time.sleep(8)
        
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(el => { if(el.innerText.includes('Accept')) el.click() })")
            time.sleep(2)
        except:
            pass
            
        print("Clicking date input...")
        driver.execute_script("""
            const inputs = Array.from(document.querySelectorAll('input'));
            for (let inp of inputs) {
                if (inp.placeholder && (inp.placeholder.includes('Departure') || inp.placeholder.includes('Date'))) {
                    inp.click();
                    break;
                }
            }
        """)
        time.sleep(3)
        
        driver.save_screenshot("akasa_calendar_open.png")
        
        html = driver.page_source
        with open("akasa_calendar_open.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Done!")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
