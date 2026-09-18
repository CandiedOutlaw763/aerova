import os
import re
import math
import sqlite3
import pandas as pd
import PyPDF2
from collections import defaultdict
import json

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'engine', 'flights.db')
STATIC_DIR = os.path.join(BASE_DIR, 'pipeline', 'static_data')
WEIGHTS_CSV = os.path.join(STATIC_DIR, 'route_weights.csv')
TARIFF_CSV = os.path.join(STATIC_DIR, 'tariff_base_prices.csv')

# Mappings
# Removed ASF and UDF_MAP since total fare is pre-calculated

# 3. Calculate Total Fares & APIx
def build_index():
    print("Loading Static Data (Weights & Tariffs)...")
    
    weights_df = pd.read_csv(WEIGHTS_CSV)
    weights = dict(zip(weights_df['ROUTE'], weights_df['WEIGHT']))
    
    tariff_df = pd.read_csv(TARIFF_CSV)
    tariffs = dict(zip(tariff_df['ROUTE'], tariff_df['TOTAL_FARE']))
    
    # Map Airport Codes to City Names for matching
    # (Simplified matching: if we have DEL-BOM, it matches DELHI-MUMBAI)
    airport_to_city = {
        'DEL': 'DELHI', 'BOM': 'MUMBAI', 'BLR': 'BENGALURU', 'HYD': 'HYDERABAD',
        'MAA': 'CHENNAI', 'CCU': 'KOLKATA', 'AMD': 'AHMEDABAD', 'PNQ': 'PUNE'
    }
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM flights WHERE total_fare IS NOT NULL", conn)
    conn.close()
    
    # Process scraped data
    route_relatives = defaultdict(list)
    
    for _, row in df.iterrows():
        orig_code = row['origin']
        dest_code = row['destination']
        if not orig_code or not dest_code:
            continue
            
        orig_city = airport_to_city.get(orig_code, orig_code)
        dest_city = airport_to_city.get(dest_code, dest_code)
        route_city = f"{orig_city}-{dest_city}"
        
        # Check if route is in top 55
        if route_city not in weights:
            route_city = f"{dest_city}-{orig_city}"
            if route_city not in weights:
                continue
                
        # Find tariff total fare
        tariff_total_fare = tariffs.get(route_city, None)
        if not tariff_total_fare:
            continue
            
        # Calculate Price Relative
        scraped_total = row['total_fare']
        price_relative = (scraped_total / tariff_total_fare) * 100
        
        route_relatives[route_city].append(price_relative)
        
    # Apply Jevons Geometric Mean for each Route using logarithms to prevent overflow
    route_indices = {}
    for route, relatives in route_relatives.items():
        if relatives:
            # e ^ (sum(ln(x)) / n)
            log_sum = sum(math.log(x) for x in relatives if x > 0)
            geo_mean = math.exp(log_sum / len(relatives))
            route_indices[route] = geo_mean
            
    # Apply Laspeyres Weighting
    final_apix = 0
    used_weight_sum = 0
    
    print("\n--- Route Indices ---")
    for route, index_val in route_indices.items():
        w = weights[route]
        used_weight_sum += w
        final_apix += index_val * w
        print(f"{route}: {index_val:.2f} (Weight: {w:.3f})")
        
    # Re-normalize if some routes were missing from DB
    if used_weight_sum > 0:
        final_apix = final_apix / used_weight_sum
        
    print(f"\n=============================")
    print(f"NATIONAL DAILY APIx: {final_apix:.2f}")
    print(f"Routes mapped: {len(route_indices)} / 55")
    print(f"=============================")
    
    # Save to a json for backtesting script
    output = {
        "apix": final_apix,
        "date": "2026-09-18",
        "routes": route_indices
    }
    with open(os.path.join(BASE_DIR, 'pipeline', 'apix_result.json'), 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    build_index()
