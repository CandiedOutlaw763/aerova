import pandas as pd, sqlite3, math

conn = sqlite3.connect('scrapers/engine/flights.db')
df = pd.read_sql_query("SELECT fare_class, total_fare, advance_purchase_window, (origin || '-' || destination) as route_city FROM flights WHERE fare_class='Economy' AND total_fare IS NOT NULL", conn)
conn.close()

tariffs = {}
tdf = pd.read_csv('scrapers/pipeline/static_data/tariff_base_prices.csv')
for _, row in tdf.iterrows():
    tariffs[(row['ROUTE'], row['FARE_CLASS'], int(row['ADVANCE_PURCHASE_WINDOW']))] = row['TOTAL_FARE']

rels = []
for _, row in df.iterrows():
    w = str(row['advance_purchase_window']).replace('T+','')
    try:
        win = int(w)
    except:
        continue
    
    # Map back origin/dest to correct city names
    o, d = row['route_city'].split('-')
    city_map = {"DEL": "DELHI", "BOM": "MUMBAI", "BLR": "BENGALURU", "HYD": "HYDERABAD", "PNQ": "PUNE"}
    route_key = f"{city_map.get(o, o)}-{city_map.get(d, d)}"
    if o > d: # alphabetical sorting for key
        route_key = f"{city_map.get(d, d)}-{city_map.get(o, o)}"
        
    t = tariffs.get((route_key, row['fare_class'], win))
    if t:
        rels.append(row['total_fare'] / t * 100)

if rels:
    log_sum = sum(math.log(x) for x in rels if x > 0)
    print(f'Geometric mean APIx: {math.exp(log_sum / len(rels))}')
    print(f'Count of valid records: {len(rels)}')
    print(f'Min relative: {min(rels)}, Max relative: {max(rels)}')
    
    rels_sort = sorted(rels)
    print(f'Median relative: {rels_sort[len(rels)//2]}')
