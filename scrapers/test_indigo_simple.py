import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo with Keys.ENTER...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
        # Hide any fixed elements that might block clicks
        driver.execute_script("""
            document.querySelectorAll('*').forEach(el => {
                try {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.display = 'none';
                    }
                } catch(e) {}
            });
        """)
        time.sleep(1)
        
        print("Interacting with Origin...")
        from_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__from input')
        driver.execute_script("arguments[0].click();", from_input)
        time.sleep(1)
        from_input.send_keys(Keys.CONTROL, 'a')
        from_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "DEL":
            from_input.send_keys(char)
            time.sleep(0.2)
            
        time.sleep(2)
        from_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        from_input.send_keys(Keys.ENTER)
        time.sleep(1)
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        driver.execute_script("arguments[0].click();", to_input)
        time.sleep(1)
        to_input.send_keys(Keys.CONTROL, 'a')
        to_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        for char in "BOM":
            to_input.send_keys(char)
            time.sleep(0.2)
            
        time.sleep(2)
        to_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        to_input.send_keys(Keys.ENTER)
        time.sleep(1)
        
        driver.save_screenshot("indigo_after_destination.png")
        
        print("Clicking Search...")
        search_btn = driver.find_element(By.CSS_SELECTOR, 'button.skyplus-button--filled')
        driver.execute_script("arguments[0].click();", search_btn)
        
        print("Waiting for page navigation...")
        start_time = time.time()
        while time.time() - start_time < 15:
            if "booking" in driver.current_url or "flight-select" in driver.current_url:
                break
            time.sleep(1)
            
        print("Final URL:", driver.current_url)
        driver.save_screenshot("indigo_final_url2.png")
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
