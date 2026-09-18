import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from engine.spiders.base_uc import UCSpider

def run():
    print("Testing Air India - Date via direct click...")
    spider = UCSpider()
    driver = spider.get_driver()
    
    try:
        driver.execute_cdp_cmd('Network.enable', {})
        
        print("Navigating to Air India...")
        driver.get("https://www.airindia.com/")
        time.sleep(8)
        
        print("Accepting cookies...")
        try:
            driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); });")
        except:
            pass
        time.sleep(1)
        
        print("Clicking 'One Way' radio button...")
        driver.execute_script("""
            let inputs = document.querySelectorAll('input[type="radio"]');
            for(let i of inputs) { if(i.value === 'one-way') { i.click(); break; } }
        """)
        time.sleep(0.5)
        
        print("Clicking FROM field...")
        driver.execute_script("document.querySelector('[aria-label=\"Select origin airport\"]').click();")
        time.sleep(1.5)
        driver.switch_to.active_element.send_keys("DEL")
        time.sleep(2)
        driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
        time.sleep(1.5)
        
        print("Clicking TO field...")
        driver.execute_script("document.querySelector('[aria-label=\"Select destination airport\"]').click();")
        time.sleep(1.5)
        driver.switch_to.active_element.send_keys("BOM")
        time.sleep(2)
        driver.execute_script("document.querySelectorAll('mat-option')[0].click();")
        time.sleep(1.5)
        
        print("Dumping all clickable date-related elements...")
        date_els = driver.execute_script("""
            let results = [];
            // Look for any element containing 'Depart', 'Select Date', or 'date'
            let allEls = document.querySelectorAll('*');
            for(let el of allEls) {
                let text = el.innerText;
                let cls = el.className;
                if(text && (text.includes('Select Date') || text.includes('Depart')) && el.offsetWidth > 0 && el.children.length === 0) {
                    results.push({tag: el.tagName, text: text.trim().substring(0,50), class: (cls||'').substring(0,60), id: el.id});
                }
            }
            return results.slice(0,10);
        """)
        print("Date elements:", json.dumps(date_els, indent=2))
        
        print("Trying to click via Python find_elements on 'Depart'...")
        try:
            depart_el = driver.find_element(By.XPATH, "//*[contains(text(), 'Select Date')]")
            print("Found Depart element:", depart_el.tag_name, depart_el.get_attribute('class'))
            driver.execute_script("arguments[0].click();", depart_el)
        except Exception as e:
            print("XPath click failed:", e)
            
        time.sleep(1)
        driver.save_screenshot("ai_date_debug.png")
        
        print("Calendar cells count:", driver.execute_script("""
            return document.querySelectorAll('.mat-calendar-body-cell').length;
        """))
        
    except Exception as e:
        import traceback
        print(f"Exception: {e}")
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
