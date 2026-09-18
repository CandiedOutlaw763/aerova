import os
import sys

# Add the root project directory to the python path so we can import scrapers
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scrapers.parsers.ota_parsers import get_ota_parser
from scrapers.parsers.airline_parsers import get_airline_parser

sys.stdout.reconfigure(encoding='utf-8')

def main():
    dom_dir = "doms"
    files = [f for f in os.listdir(dom_dir) if f.endswith(".html")]
    
    print(f"{'Platform':<20} | {'Extracted Price (₹)':<20} | {'DOM Size (Bytes)'}")
    print("-" * 65)
    
    for file in files:
        filepath = os.path.join(dom_dir, file)
        platform_name = file.replace(".html", "")
        size = os.path.getsize(filepath)
        
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
            
        try:
            if platform_name in ["IndiGo", "AirIndia", "AirIndiaExpress", "AkasaAir", "SpiceJet"]:
                parser = get_airline_parser(platform_name, html)
            else:
                parser = get_ota_parser(platform_name, html)
                
            price = parser.extract_lowest_price()
            price_display = f"₹{price}" if price else "Not Found (Blocked/Dynamic)"
            
        except Exception as e:
            price_display = f"Error: {e}"
            
        print(f"{platform_name:<20} | {price_display:<20} | {size}")

if __name__ == "__main__":
    main()
