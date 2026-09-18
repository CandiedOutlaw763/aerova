import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_uc_mmt():
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(version_main=152, options=options)
    
    print("[UC] Navigating to MakeMyTrip...")
    driver.get("https://www.makemytrip.com/")
    
    print("[UC] Waiting 5 seconds on homepage...")
    time.sleep(5)
    
    deep_link = "https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-28/09/2026&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
    print(f"[UC] Navigating to deep link: {deep_link}")
    driver.get(deep_link)
    
    print("[UC] Waiting for flights to load...")
    time.sleep(15)
    
    print("[UC] Looking for 'VIEW PRICES' or 'View Prices' button...")
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        # Find all buttons that contain "view prices" or similar
        buttons = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view prices') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view fare')]")
        
        if buttons:
            print(f"[UC] Found {len(buttons)} buttons. Using ActionChains to click the first one...")
            btn = buttons[0]
            
            # Scroll to element just in case
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(2)
            
            # ActionChains simulate real physical mouse movement and click
            actions = ActionChains(driver)
            actions.move_to_element(btn).pause(0.5).click().perform()
            
            print("[UC] Successfully executed ActionChains click!")
        else:
            print("[UC] Could not find any button matching the text.")
    except Exception as e:
        print(f"[UC] Error during ActionChains click: {e}")
    
    print("[UC] Waiting for Fare Details overlay...")
    time.sleep(5)
    
    print("[UC] Taking screenshot...")
    driver.save_screenshot("uc_mmt_results.png")
    
    try:
        # Dump HTML
        html = driver.page_source
        with open("uc_mmt_html.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[UC] Saved HTML length: {len(html)}")
    except Exception as e:
        print("[UC] Error dumping HTML:", e)
        
    driver.quit()

if __name__ == "__main__":
    test_uc_mmt()
