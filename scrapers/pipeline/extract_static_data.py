import os
import re
import pandas as pd
import PyPDF2
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAFFIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'india-aviation-traffic', '2025_data')
PDF_PATH = os.path.join(os.path.dirname(BASE_DIR), 'TARIFF-SHEET-AS-ON-28-NOV-24.pdf')

OUT_DIR = os.path.join(BASE_DIR, 'pipeline', 'static_data')
os.makedirs(OUT_DIR, exist_ok=True)

ASF = 236
UDF_MAP = {
    "DELHI": 150, "MUMBAI": 150, "BENGALURU": 350, "HYDERABAD": 300, 
    "CHENNAI": 200, "KOLKATA": 250, "AHMEDABAD": 200, "PUNE": 200, "DEFAULT": 200
}

def extract_weights():
    print("Extracting Traffic Weights...")
    all_data = []
    for file in os.listdir(TRAFFIC_DIR):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(TRAFFIC_DIR, file), header=2)
            if 'CITY 1' in df.columns and 'PASSENGERS \nTO CITY 2' in df.columns:
                sub = df[['CITY 1', 'CITY 2', 'PASSENGERS \nTO CITY 2', 'PASSENGERS \nFROM CITY 2']].copy()
                sub.columns = ['ORIGIN', 'DEST', 'PAX_TO', 'PAX_FROM']
                sub = sub.dropna(subset=['ORIGIN', 'DEST'])
                for col in ['PAX_TO', 'PAX_FROM']:
                    sub[col] = sub[col].astype(str).str.replace(',', '', regex=False)
                    sub[col] = pd.to_numeric(sub[col], errors='coerce').fillna(0)
                sub['PAX'] = sub['PAX_TO'] + sub['PAX_FROM']
                all_data.append(sub[['ORIGIN', 'DEST', 'PAX']])
    
    combined = pd.concat(all_data)
    combined['ROUTE'] = combined['ORIGIN'].str.strip().str.upper() + "-" + combined['DEST'].str.strip().str.upper()
    route_traffic = combined.groupby('ROUTE')['PAX'].sum().reset_index()
    route_traffic = route_traffic.sort_values(by='PAX', ascending=False)
    
    top_55 = route_traffic.head(55).copy()
    total_top_pax = top_55['PAX'].sum()
    top_55['WEIGHT'] = top_55['PAX'] / total_top_pax
    
    out_path = os.path.join(OUT_DIR, 'route_weights.csv')
    top_55[['ROUTE', 'WEIGHT']].to_csv(out_path, index=False)
    print(f"Saved {len(top_55)} weights to {out_path}")

def extract_tariffs():
    print("Extracting Tariffs from PDF...")
    
    # Read the 55 allowed routes
    weights_path = os.path.join(OUT_DIR, 'route_weights.csv')
    if os.path.exists(weights_path):
        valid_routes = set(pd.read_csv(weights_path)['ROUTE'].tolist())
    else:
        valid_routes = set()
        
    tariff = defaultdict(dict)
    text = ""
    with open(PDF_PATH, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        # Economy Fares span pages 2, 3, and 4 (0-indexed). 
        # Page 5 starts Premium Economy.
        for i in range(2, 5):
            text += reader.pages[i].extract_text() + "\n"
            
    pattern = re.compile(r'^(\d+)\s+([A-Za-z\s]+?)\s+([A-Za-z\s]+?)\s+(\d+)\s+(Minimum|Maximum)\s+([\d\s]+)$', re.MULTILINE)
    
    for match in pattern.finditer(text):
        origin = match.group(2).strip().upper()
        dest = match.group(3).strip().upper()
        min_max = match.group(5).lower()
        prices_str = match.group(6).strip()
        prices = [int(p) for p in prices_str.split()]
        
        # Apply Aliases to match DGCA traffic names
        aliases = {
            "GOA": "DABOLIM",
            "VIZAG": "VISAKHAPATNAM",
            "MANGALURU": "MANGALORE"
        }
        mapped_origin = aliases.get(origin, origin)
        mapped_dest = aliases.get(dest, dest)
        
        route = f"{mapped_origin}-{mapped_dest}"
        # We only care about the top 55 routes
        if route not in valid_routes:
            # Check the flipped route
            flipped = f"{mapped_dest}-{mapped_origin}"
            if flipped not in valid_routes:
                continue
            else:
                route = flipped
                
        if prices:
            # Average all the Levels (Booking Classes) for this Min/Max row
            avg_price = sum(prices) / len(prices)
            
            if route not in tariff:
                tariff[route] = {'min_avg': 0, 'max_avg': 0, 'origin': origin}
            
            if min_max == 'minimum':
                tariff[route]['min_avg'] = avg_price
            else:
                tariff[route]['max_avg'] = avg_price
                
    final_data = []
    for route, data in tariff.items():
        if data['min_avg'] > 0 and data['max_avg'] > 0:
            # Midpoint of the Minimum and Maximum average
            base_fare = (data['min_avg'] + data['max_avg']) / 2
            
            # Forward calculate Total Fare
            origin_city = data['origin']
            udf = UDF_MAP.get(origin_city, UDF_MAP["DEFAULT"])
            fixed_fees = ASF + udf
            gst_rate = 0.05  # Economy GST
            
            total_fare = (base_fare * (1 + gst_rate)) + fixed_fees
            
            final_data.append({
                'ROUTE': route, 
                'BASE_FARE': base_fare,
                'TOTAL_FARE': total_fare
            })
            
    df = pd.DataFrame(final_data)
    out_path = os.path.join(OUT_DIR, 'tariff_base_prices.csv')
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} tariffs to {out_path}")

if __name__ == "__main__":
    extract_weights()
    extract_tariffs()
