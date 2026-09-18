import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

d = uc.Chrome(version_main=152)
d.get('https://www.makemytrip.com/')
time.sleep(5)

try:
    d.find_element(By.CSS_SELECTOR, '.commonModal__close').click()
except:
    pass
time.sleep(1)

try:
    d.find_element(By.CSS_SELECTOR, '[data-cy="closeModal"]').click()
except:
    pass

try:
    d.find_element(By.ID, 'fromCity').click()
    print('CLICKED FROMCITY')
except Exception as e:
    print('COULD NOT CLICK FROMCITY', type(e).__name__)
    
time.sleep(2)
d.save_screenshot('mmt_step2.png')
d.quit()
