import os
import re
import sqlite3
import pandas as pd
import PyPDF2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(os.path.dirname(BASE_DIR), 'TARIFF-SHEET-AS-ON-01APR26.pdf')
DB_PATH = os.path.join(BASE_DIR, 'engine', 'flights.db')
WEIGHTS_CSV = os.path.join(BASE_DIR, 'pipeline', 'static_data', 'route_weights.csv')

# Mappings
ASF = 236
UDF_MAP = {
    "DELHI": 150, "MUMBAI": 150, "BENGALURU": 350, "HYDERABAD": 300, 
    "CHENNAI": 200, "KOLKATA": 250, "AHMEDABAD": 200, "PUNE": 200, "DEFAULT": 200
}

def parse_dgca_fares():
    tariff = {}
    text = ""
    with open(PDF_PATH, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        # Economy fares are on pages 2 and 3 in the 01APR26 sheet
        for i in range(2, 4):
            text += reader.pages[i].extract_text() + "\n"
            
    pattern = re.compile(r'^(\d+)\s+([A-Za-z\s]+?)\s+([A-Za-z\s]+?)\s+(\d+)\s+(Minimum|Maximum)\s+([\d\s]+)$', re.MULTILINE)
    
    aliases = {
        "GOA": "DABOLIM",
        "VIZAG": "VISAKHAPATNAM",
        "MANGALURU": "MANGALORE"
    }
    
    temp_tariff = {}
    for match in pattern.finditer(text):
        origin = match.group(2).strip().upper()
        dest = match.group(3).strip().upper()
        min_max = match.group(5).lower()
        prices_str = match.group(6).strip()
        prices = [int(p) for p in prices_str.split()]
        
        origin_mapped = aliases.get(origin, origin)
        dest_mapped = aliases.get(dest, dest)
        
        cities = sorted([origin_mapped, dest_mapped])
        route = f"{cities[0]}-{cities[1]}"
        
        if prices:
            avg_price = sum(prices) / len(prices)
            if route not in temp_tariff:
                temp_tariff[route] = {'min_avg': 0, 'max_avg': 0, 'origin': origin_mapped}
            if min_max == 'minimum':
                temp_tariff[route]['min_avg'] = avg_price
            else:
                temp_tariff[route]['max_avg'] = avg_price
                
    for route, data in temp_tariff.items():
        if data['min_avg'] > 0 and data['max_avg'] > 0:
            base_fare = (data['min_avg'] + data['max_avg']) / 2
            
            # Add taxes to get DGCA Total Fare
            orig_city = data['origin']
            udf = UDF_MAP.get(orig_city, UDF_MAP["DEFAULT"])
            fixed_fees = ASF + udf
            gst_rate = 0.05
            
            total_fare = (base_fare * (1 + gst_rate)) + fixed_fees
            tariff[route] = total_fare
            
    return tariff

def backtest():
    print("Parsing DGCA Monthly Average Fares (01 APR 26)...")
    dgca_fares = parse_dgca_fares()
    
    # Load Basket Routes
    if not os.path.exists(WEIGHTS_CSV):
        print("Error: route_weights.csv not found.")
        return
    weights_df = pd.read_csv(WEIGHTS_CSV)
    basket_routes = set(weights_df['ROUTE'].tolist())
    
    print("Loading Scraped Data...")
    conn = sqlite3.connect(DB_PATH)
    scraped_df = pd.read_sql_query("SELECT origin, destination, total_fare FROM flights WHERE total_fare IS NOT NULL", conn)
    conn.close()
    
    airport_to_city = {
        'DEL': 'DELHI', 'BOM': 'MUMBAI', 'BLR': 'BENGALURU', 'HYD': 'HYDERABAD',
        'MAA': 'CHENNAI', 'CCU': 'KOLKATA', 'AMD': 'AHMEDABAD', 'PNQ': 'PUNE'
    }
    
    scraped_averages = {}
    temp_scraped = {}
    
    for _, row in scraped_df.iterrows():
        orig = airport_to_city.get(row['origin'], row['origin'])
        dest = airport_to_city.get(row['destination'], row['destination'])
        cities = sorted([orig, dest])
        route = f"{cities[0]}-{cities[1]}"
        
        if route in basket_routes:
            if route not in temp_scraped:
                temp_scraped[route] = []
            temp_scraped[route].append(row['total_fare'])
            
    for route, fares in temp_scraped.items():
        scraped_averages[route] = sum(fares) / len(fares)
        
    print("\n=========================================")
    print("       DGCA BACK-TESTING VALIDATION      ")
    print("=========================================")
    
    total_scraped = 0
    total_dgca = 0
    routes_compared = 0
    
    for route in scraped_averages.keys():
        if route in dgca_fares:
            s_fare = scraped_averages[route]
            d_fare = dgca_fares[route]
            total_scraped += s_fare
            total_dgca += d_fare
            routes_compared += 1
            
            var_pct = ((s_fare - d_fare) / d_fare) * 100
            print(f"{route}: Scraped=Rs.{s_fare:.0f} | DGCA=Rs.{d_fare:.0f} | Var={var_pct:+.1f}%")
            
    print("-----------------------------------------")
    if routes_compared > 0:
        avg_var = ((total_scraped - total_dgca) / total_dgca) * 100
        print(f"Overall Scraped vs DGCA Variance: {avg_var:+.2f}%")
        print(f"Routes Validated: {routes_compared} / {len(basket_routes)}")
    else:
        print("No intersecting routes found in scraped data yet.")
    print("=========================================")
    print("Note: Run orchestrator to scrape all 55 routes to achieve full 30-day validation.")

if __name__ == "__main__":
    backtest()
