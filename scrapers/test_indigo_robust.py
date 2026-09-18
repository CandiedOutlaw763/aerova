import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing robust UI population...")
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
        from_input.send_keys("DEL")
        
        # Wait for the item containing DEL to appear in the list
        start = time.time()
        found_del = False
        while time.time() - start < 5:
            res = driver.execute_script("""
                let items = document.querySelectorAll('ul.MuiList-root li');
                for(let i=0; i<items.length; i++) {
                    if(items[i].textContent.toUpperCase().includes('DEL')) {
                        items[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if res:
                found_del = True
                break
            time.sleep(0.5)
            
        if not found_del:
            html = driver.execute_script("let u = document.querySelector('ul.MuiList-root'); return u ? u.outerHTML : '';")
            print("DEL LIST HTML:", html)
            
        time.sleep(1)
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        driver.execute_script("arguments[0].click();", to_input)
        time.sleep(1)
        to_input.send_keys(Keys.CONTROL, 'a')
        to_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        to_input.send_keys("BOM")
        
        # Wait for BOM
        start = time.time()
        found_bom = False
        while time.time() - start < 5:
            res = driver.execute_script("""
                let items = document.querySelectorAll('ul.MuiList-root li');
                for(let i=0; i<items.length; i++) {
                    if(items[i].textContent.toUpperCase().includes('BOM')) {
                        items[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if res:
                found_bom = True
                break
            time.sleep(0.5)
            
        if not found_bom:
            html = driver.execute_script("let u = document.querySelector('ul.MuiList-root'); return u ? u.outerHTML : '';")
            print("BOM LIST HTML:", html)
            
        time.sleep(2)

        
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
        driver.save_screenshot("indigo_final_url.png")
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
