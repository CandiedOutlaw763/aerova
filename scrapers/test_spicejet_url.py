import time
from selenium import webdriver

def run():
    print("Testing SpiceJet Direct URL...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # SpiceJet usually formats date as YYYY-MM-DD in the URL
        url = "https://www.spicejet.com/search?origin=DEL&destination=BOM&flightDate=2026-09-30&currency=INR&passengerCount=1&tripType=OneWay"
        print(f"Navigating to {url}")
        driver.get(url)
        time.sleep(15)
        
        driver.save_screenshot("spicejet_direct_url.png")
        print("Done!")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
