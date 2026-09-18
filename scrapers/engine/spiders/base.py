from typing import List, Dict

class BaseSpider:
    name = "base"
    
    def __init__(self):
        pass
        
    def scrape(self, origin: str, destination: str, advance_window: str, fare_class: str, date_str: str) -> List[Dict]:
        """
        Executes the scraping logic for a specific route, date, and fare class.
        
        Args:
            origin (str): Origin airport code (e.g., 'DEL')
            destination (str): Destination airport code (e.g., 'BOM')
            advance_window (str): e.g., 'T+15'
            fare_class (str): e.g., 'Economy'
            date_str (str): Exact date string, e.g., '28/09/2026' or '20260928' depending on platform
            
        Returns:
            List[Dict]: A list of flight dictionaries matching the db schema:
            [{'carrier': 'IndiGo', 'base_fare': 4000, 'taxes': 1000, 'total_fare': 5000}, ...]
        """
        raise NotImplementedError("Subclasses must implement the scrape method.")
