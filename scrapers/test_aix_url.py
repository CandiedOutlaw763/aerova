import time
import json
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express direct URL navigation...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        url = "https://www.airindiaexpress.com/search-availability?origin=DEL&destination=BOM&departDate=2026-09-30&adults=1&tripType=Oneway"
        # Or maybe it's just /flights or /search
        driver.get(url)
        time.sleep(10)
        
        driver.save_screenshot("aix_direct_url.png")
        
        # Also try the other common URL format
        url2 = "https://www.airindiaexpress.com/home?origin=DEL&destination=BOM&date=2026-09-30"
        driver.get(url2)
        time.sleep(10)
        driver.save_screenshot("aix_direct_url2.png")
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
