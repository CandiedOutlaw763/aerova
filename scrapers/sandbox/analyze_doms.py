import os
import sys
from bs4 import BeautifulSoup
import re

sys.stdout.reconfigure(encoding='utf-8')

def analyze_prices():
    dom_dir = "doms"
    files = [f for f in os.listdir(dom_dir) if f.endswith(".html")]
    
    for file in files:
        filepath = os.path.join(dom_dir, file)
        size = os.path.getsize(filepath)
        print(f"\n{'='*40}")
        print(f"Analyzing {file} ({size} bytes)")
        
        if size < 5000:
            print("File too small, likely blocked or empty.")
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
        # Find all elements containing the rupee symbol ₹ or Rs
        price_pattern = re.compile(r'(?:₹|Rs\.?)\s*([\d,]+)')
        texts = soup.find_all(string=price_pattern)
        
        prices = []
        for text in texts:
            match = price_pattern.search(text)
            if match:
                price_str = match.group(1).replace(",", "")
                if price_str.isdigit():
                    prices.append(int(price_str))
                    
        if prices:
            print(f"Found {len(prices)} price mentions.")
            print(f"Min price: {min(prices)}")
            print(f"Max price: {max(prices)}")
            
            # Print a few examples of the parent tags to find classes
            print("Sample container classes:")
            for text in texts[:3]:
                parent = text.parent
                print(f"  Tag: {parent.name}, Class: {parent.get('class')}, Text: '{text.strip()}'")
        else:
            print("No prices found using standard regex.")

if __name__ == "__main__":
    analyze_prices()
