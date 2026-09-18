import requests
from bs4 import BeautifulSoup
import re

def test_easemytrip():
    url = "https://flight.easemytrip.com/FlightList/Index?srch=DEL-Delhi-India|BOM-Mumbai-India|28/09/2026&px=1-0-0&cclass=0&cc=0&isOneway=true&tripId=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print("Status Code:", response.status_code)
        
        # Save HTML
        with open("emt_test.html", "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print("Length of HTML:", len(response.text))
        
        # Search for prices
        prices = re.findall(r'₹\s*([\d,]+)', response.text)
        print("Prices found in HTML:", prices[:10])
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_easemytrip()
