import time
import undetected_chromedriver as uc
from typing import List, Dict

class UCSpider:
    name = "UCBaseSpider"
    
    def __init__(self):
        pass
        
    def get_driver(self):
        # We specify version_main=152 to match the local Chrome version of the runner
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        # Removing suspicious flags that trigger Akamai Bot Manager
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        return uc.Chrome(version_main=152, options=options)
        
    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        raise NotImplementedError("Subclasses must implement scrape()")
