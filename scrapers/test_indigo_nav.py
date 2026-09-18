import time
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo Direct Navigation...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        url = "https://www.goindigo.in/booking/flight-select.html?tripType=1&origin1=DEL&destination1=BOM&departDate1=2026-09-30&ADT=1&CHD=0&INF=0&currency=INR"
        print(f"Navigating to {url}")
        driver.get(url)
        time.sleep(15)
        
        driver.save_screenshot("indigo_direct_nav.png")
        print("Saved screenshot.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
