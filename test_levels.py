import pandas as pd, sqlite3, math, os
conn = sqlite3.connect('scrapers/engine/flights.db')
df = pd.read_sql_query("SELECT advance_purchase_window, total_fare, (origin || '-' || destination) as route_city FROM flights WHERE fare_class='Economy' AND total_fare IS NOT NULL", conn)
conn.close()

def get_pdf_levels():
    import re
    from collections import defaultdict
    import PyPDF2
    PDF_PATH = 'TARIFF-SHEET-AS-ON-28-NOV-24.pdf'
    tariff = defaultdict(dict)
    valid_routes = set(['DELHI-MUMBAI', 'BENGALURU-DELHI', 'BENGALURU-MUMBAI', 'DELHI-HYDERABAD', 'DELHI-PUNE'])
    page_classes = {2: 'Economy', 3: 'Economy', 4: 'Economy'}
    
    with open(PDF_PATH, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for i in range(2, 5):
            text = reader.pages[i].extract_text()
            pattern = re.compile(r'^(\d+)\s+([A-Za-z\s]+?)\s+([A-Za-z\s]+?)\s+(?:(\d+)\s+)?(Minimum|Maximum)\s+([\d\s]+)$', re.MULTILINE)
            for match in pattern.finditer(text):
                o, d = match.group(2).strip().upper(), match.group(3).strip().upper()
                route = f'{o}-{d}'
                if route not in valid_routes:
                    if f'{d}-{o}' in valid_routes:
                        route = f'{d}-{o}'
                    else: continue
                min_max = match.group(5).lower()
                prices = [int(p) for p in match.group(6).strip().split()]
                if route not in tariff:
                    tariff[route] = {'min': [], 'max': [], 'origin': o}
                if min_max == 'minimum':
                    tariff[route]['min'] = prices
                else:
                    tariff[route]['max'] = prices
    return tariff

tariff = get_pdf_levels()

for test_level in range(0, 10):
    tariffs = {}
    for route, data in tariff.items():
        min_p = sorted(data['min'])
        max_p = sorted(data['max'])
        l = min(len(min_p), len(max_p))
        if l == 0: continue
        
        idx = test_level
        if idx >= l: idx = l - 1
        
        base_fare = (min_p[idx] + max_p[idx]) / 2
        
        UDF_MAP = {'DELHI': 150, 'MUMBAI': 150, 'BENGALURU': 350, 'HYDERABAD': 300, 'PUNE': 200, 'DEFAULT': 200}
        udf = UDF_MAP.get(data['origin'], 200)
        total_fare = (base_fare * 1.05) + 236 + udf
        
        for w in [1, 7, 15, 30, 45]:
            tariffs[(route, w)] = total_fare
            
    rels = []
    for _, row in df.iterrows():
        w = str(row['advance_purchase_window']).replace('T+','')
        try: win = int(w)
        except: continue
        
        o, d = row['route_city'].split('-')
        city_map = {'DEL': 'DELHI', 'BOM': 'MUMBAI', 'BLR': 'BENGALURU', 'HYD': 'HYDERABAD', 'PNQ': 'PUNE'}
        route_key = f'{city_map.get(o, o)}-{city_map.get(d, d)}'
        if o > d: route_key = f'{city_map.get(d, d)}-{city_map.get(o, o)}'
            
        t = tariffs.get((route_key, win))
        if t: rels.append(row['total_fare'] / t * 100)
        
    if rels:
        log_sum = sum(math.log(x) for x in rels if x > 0)
        print(f'Level {test_level + 1} APIx: {math.exp(log_sum / len(rels))}')
