import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing IndiGo Dropdown...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.get("https://www.goindigo.in/")
        time.sleep(8)
        
        # Hide sticky elements
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
        
        print("Interacting with Destination...")
        to_input = driver.find_element(By.CSS_SELECTOR, '.search-widget-form-body__to input')
        driver.execute_script("arguments[0].click();", to_input)
        time.sleep(1)
        
        driver.execute_script("""
            var element = arguments[0];
            var value = "BOM";
            const valueSetter = Object.getOwnPropertyDescriptor(element, 'value').set;
            const prototype = Object.getPrototypeOf(element);
            const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
            if (valueSetter && valueSetter !== prototypeValueSetter) {
                prototypeValueSetter.call(element, value);
            } else {
                valueSetter.call(element, value);
            }
            element.dispatchEvent(new Event('input', { bubbles: true }));
        """, to_input)
        time.sleep(2)
        
        # Dump dropdown items
        items = driver.execute_script("""
            let results = [];
            let container = document.querySelector('.search-widget-form-body__to').parentElement;
            let allEls = document.querySelectorAll('*');
            for(let el of allEls) {
                if (el.innerText && el.innerText.includes('Mumbai') && el.innerText.includes('BOM') && el.children.length < 5) {
                    results.push({tag: el.tagName, class: el.className, text: el.innerText.trim()});
                }
            }
            return results;
        """)
        print("Dropdown items:", json.dumps(items, indent=2))
        
        driver.save_screenshot("indigo_dropdown_debug.png")
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
