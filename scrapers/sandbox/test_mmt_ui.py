import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=152)

driver.get("https://www.makemytrip.com/")
time.sleep(15)

try:
    driver.execute_script("""
        let closes = document.querySelectorAll('.commonModal__close, [data-cy="closeModal"], .close');
        for(let c of closes) { try { c.click(); } catch(e) {} }
    """)
except:
    pass
time.sleep(2)

actions = ActionChains(driver)
el = driver.find_element(By.ID, "fromCity")
print("Clicking fromCity...")
actions.move_to_element(el).click().perform()
time.sleep(2)

try:
    inp = driver.find_element(By.CSS_SELECTOR, "input[placeholder='From']")
    print("Found 'From' input:", inp)
    inp.send_keys("DEL")
    time.sleep(2)
    suggestion = driver.find_element(By.CSS_SELECTOR, "ul[role='listbox'] li")
    actions.move_to_element(suggestion).click().perform()
    print("Selected suggestion")
except Exception as e:
    print("Failed 'From':", e)

driver.quit()
