import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India Express UI Interactivity...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.airindiaexpress.com/")
        time.sleep(10)
        
        # Click on 'Flying from'
        print("Clicking 'Flying from'...")
        driver.execute_script("""
            let els = document.querySelectorAll('*');
            for(let el of els) {
                if (el.innerText && el.innerText.trim() === 'Bengaluru') {
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        driver.save_screenshot("aix_from_clicked.png")
        
        # See what inputs appeared
        inputs = driver.execute_script("""
            let results = [];
            let els = document.querySelectorAll('input');
            for(let el of els) {
                results.push({
                    type: el.type || '',
                    id: el.id || '',
                    class: el.className || '',
                    placeholder: el.placeholder || '',
                    value: el.value || ''
                });
            }
            return results;
        """)
        print("\nInputs after clicking from:", json.dumps(inputs, indent=2))
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
