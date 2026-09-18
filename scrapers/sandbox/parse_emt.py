from bs4 import BeautifulSoup
import json

def extract_flights():
    with open("emt_test.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    flights = []
    
    # In EaseMyTrip, flight rows usually have class 'flightItem' or something similar.
    # Let's just find all divs with 'ng-repeat' or 'id' starting with something
    # Actually, we can just look for flight names and prices.
    for div in soup.find_all('div', class_='flt-item'): # guessing class
        print(div.text[:100])
        
    # If flt-item is wrong, let's find the actual class for prices
    # Prices are usually in a div containing the rupee symbol.
    price_spans = soup.find_all(text=lambda t: t and '₹' in t)
    print("Price elements found:", len(price_spans))
    
    # We will just write a snippet of HTML to a debug file that contains a price to inspect its structure.
    import re
    matches = re.finditer(r'<div[^>]*>.*?₹[\d,]+.*?</div>', html, re.DOTALL | re.IGNORECASE)
    
    snippets = []
    for i, m in enumerate(matches):
        if i > 5: break
        snippets.append(m.group(0))
        
    with open("emt_debug_snippets.html", "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(snippets))

if __name__ == "__main__":
    extract_flights()
