from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import sqlite3
import pandas as pd
import numpy as np
import os
import math
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="APIx Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'flights.db')
STATIC_DATA_DIR = os.path.join(BASE_DIR, 'data')

# Serve the frontend HTML from root
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

AIRPORT_TO_CITY = {
    "DEL": "DELHI", "BOM": "MUMBAI", "BLR": "BENGALURU", "HYD": "HYDERABAD",
    "MAA": "CHENNAI", "CCU": "KOLKATA", "AMD": "AHMEDABAD", "PNQ": "PUNE",
    "SXR": "SRINAGAR", "GAU": "GUWAHATI", "GOI": "DABOLIM", "PAT": "PATNA",
    "COK": "KOCHI", "LKO": "LUCKNOW", "BBI": "BHUBANESWAR", "ATQ": "AMRITSAR",
    "IXB": "BAGDOGRA", "JAI": "JAIPUR", "IDR": "INDORE", "VNS": "VARANASI",
    "CJB": "COIMBATORE", "IXC": "CHANDIGARH", "TIR": "TIRUPATI", "IXA": "AGARTALA",
    "RPR": "RAIPUR", "IXL": "LEH", "NAG": "NAGPUR", "DED": "DEHRADUN",
    "UDR": "UDAIPUR", "IXJ": "JAMMU"
}

# Known airlines vs OTAs
AIRLINES = {"IndiGo", "Air India", "Air India Express", "Akasa Air", "SpiceJet"}
OTAS = {"MakeMyTrip", "Goibibo", "Yatra", "EaseMyTrip", "Cleartrip", "Ixigo"}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_weights():
    df = pd.read_csv(os.path.join(STATIC_DATA_DIR, 'route_weights.csv'))
    return dict(zip(df['ROUTE'], df['WEIGHT']))

def get_tariffs():
    df = pd.read_csv(os.path.join(STATIC_DATA_DIR, 'tariff_base_prices.csv'))
    tariffs = {}
    for _, row in df.iterrows():
        tariffs[(row['ROUTE'], row['FARE_CLASS'], int(row['ADVANCE_PURCHASE_WINDOW']))] = row['TOTAL_FARE']
    return tariffs

def route_key(origin, destination):
    """Build a route key matching route_weights.csv format (e.g., DELHI-MUMBAI)"""
    orig = AIRPORT_TO_CITY.get(origin, origin)
    dest = AIRPORT_TO_CITY.get(destination, destination)
    return f"{sorted([orig, dest])[0]}-{sorted([orig, dest])[1]}"

def normalize_window(w):
    """Normalize window values like 'T+15' -> 15, '15' -> 15"""
    s = str(w).replace('T+', '').strip()
    try:
        return int(s)
    except ValueError:
        return None

def normalize_carrier(c):
    """Normalize variations in airline names from different OTAs."""
    if not c or not isinstance(c, str): return "Other"
    cu = c.upper()
    if 'INDIGO' in cu or cu == '6E': return 'IndiGo'
    if 'AKASA' in cu or cu == 'QP': return 'Akasa Air'
    if 'AIR INDIA EXPRESS' in cu or cu == 'IX': return 'Air India Express'
    if 'AIR INDIA' in cu or cu == 'AI': return 'Air India'
    if 'SPICEJET' in cu or cu == 'SG' or 'SG ' in cu: return 'SpiceJet'
    return "Other"

def load_all_flights():
    """Load all flights into a DataFrame with computed columns."""
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM flights WHERE total_fare IS NOT NULL AND total_fare > 0", conn)
    conn.close()
    df['window_int'] = df['advance_purchase_window'].apply(normalize_window)
    df['route_iata'] = df['origin'] + '-' + df['destination']
    df['route_city'] = df.apply(lambda r: route_key(r['origin'], r['destination']), axis=1)
    df['carrier'] = df['carrier'].apply(normalize_carrier)
    return df


# ──────────────────────────────────────────────────────────
# 1. SUMMARY / KPI ENDPOINT — powers the Home page top KPIs
# ──────────────────────────────────────────────────────────
@app.get("/api/summary")
def get_summary():
    df = load_all_flights()
    weights = get_weights()
    tariffs = get_tariffs()
    
    total_obs = len(df)
    avg_fare = float(df['total_fare'].mean())
    median_fare = float(df['total_fare'].median())
    routes_covered = df['route_iata'].nunique()
    
    # Compute national APIx (Jevons + Laspeyres)
    route_relatives = {}
    for _, row in df.iterrows():
        route = row['route_city']
        fc = row['fare_class'] if row['fare_class'] else 'Economy'
        if fc != 'Economy': continue
        win = row.get('window_int')
        tariff = tariffs.get((route, fc, win))
        if tariff and route in weights:
            if route not in route_relatives:
                route_relatives[route] = []
            route_relatives[route].append((row['total_fare'] / tariff) * 100)
    
    route_indices = {}
    for route, rels in route_relatives.items():
        if rels:
            log_sum = sum(math.log(x) for x in rels if x > 0)
            route_indices[route] = math.exp(log_sum / len(rels))
    
    national_apix = 0.0
    used_weight = 0.0
    for route, idx in route_indices.items():
        w = weights.get(route, 0)
        national_apix += idx * w
        used_weight += w
    if used_weight > 0:
        national_apix /= used_weight
    
    return {
        "apix": round(national_apix, 1),
        "avg_fare": round(avg_fare),
        "median_fare": round(median_fare),
        "routes_covered": routes_covered,
        "total_observations": total_obs,
        "route_indices": {r: round(v, 1) for r, v in route_indices.items()},
        "scraped_at": df['scraped_at'].max()
    }


# ──────────────────────────────────────────────────────────
# 2. INDEX ENDPOINT — powers the Airfare Price Index page
# ──────────────────────────────────────────────────────────
@app.get("/api/index/daily")
def get_daily_index():
    df = load_all_flights()
    weights = get_weights()
    tariffs = get_tariffs()
    
    route_relatives = {}
    for _, row in df.iterrows():
        route = row['route_city']
        fc = row['fare_class'] if row['fare_class'] else 'Economy'
        if fc != 'Economy': continue
        win = row.get('window_int')
        tariff = tariffs.get((route, fc, win))
        if tariff and route in weights:
            if route not in route_relatives:
                route_relatives[route] = []
            route_relatives[route].append((row['total_fare'] / tariff) * 100)
    
    route_indices = {}
    for route, rels in route_relatives.items():
        if rels:
            log_sum = sum(math.log(x) for x in rels if x > 0)
            route_indices[route] = math.exp(log_sum / len(rels))
    
    national_apix = 0.0
    used_weight = 0.0
    route_details = []
    for route, idx in route_indices.items():
        w = weights.get(route, 0)
        national_apix += idx * w
        used_weight += w
        route_details.append({
            "route": route,
            "raw_w": w,
            "route_apix": round(idx, 1)
        })
        
    if used_weight > 0:
        national_apix /= used_weight
        for r in route_details:
            norm_w = r['raw_w'] / used_weight
            r['weight'] = round(norm_w * 100, 1)
            r['contribution'] = round(r['route_apix'] * norm_w, 2)
            del r['raw_w']
    else:
        for r in route_details:
            r['weight'] = 0.0
            r['contribution'] = 0.0
            del r['raw_w']
            
    route_details.sort(key=lambda x: x.get('weight', 0), reverse=True)
    
    return {
        "current_apix": round(national_apix, 1),
        "route_details": route_details,
    }


# ──────────────────────────────────────────────────────────
# 3. FARE OBSERVATIONS — powers the Fare Data table
# ──────────────────────────────────────────────────────────
@app.get("/api/fares")
def get_fares(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    carrier: Optional[str] = None,
    platform: Optional[str] = None,
    fare_class: Optional[str] = None,
    window: Optional[str] = None,
    limit: int = 50,
    page: int = 1
):
    conn = get_db()
    query = "SELECT platform, origin, destination, carrier, advance_purchase_window, fare_class, base_fare, taxes, total_fare, scraped_at FROM flights WHERE total_fare IS NOT NULL"
    params = []
    if origin:
        query += " AND origin=?"
        params.append(origin)
    if destination:
        query += " AND destination=?"
        params.append(destination)
    if carrier:
        query += " AND carrier=?"
        params.append(carrier)
    if platform:
        query += " AND platform=?"
        params.append(platform)
    if fare_class:
        query += " AND fare_class=?"
        params.append(fare_class)
    if window:
        w_norm = window.replace('T+', '')
        query += " AND (advance_purchase_window=? OR advance_purchase_window=?)"
        params.extend([window, w_norm])
    
    offset = (page - 1) * limit
    # Fetch limit + 1 to check if there is a next page
    query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
    params.extend([limit + 1, offset])
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    has_more = len(rows) > limit
    rows = rows[:limit]
    
    data = []
    for r in rows:
        d = dict(r)
        d['carrier'] = normalize_carrier(d.get('carrier'))
        data.append(d)
    return {
        "data": data,
        "has_more": has_more,
        "page": page
    }


# ──────────────────────────────────────────────────────────
# 4. ROUTE ANALYSIS — powers the Route Analysis page
# ──────────────────────────────────────────────────────────
@app.get("/api/route-analysis")
def get_route_analysis(
    origin: str = "DEL",
    destination: str = "BOM",
    fare_class: str = "Economy"
):
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT carrier, platform, advance_purchase_window, base_fare, taxes, total_fare FROM flights WHERE origin=? AND destination=? AND fare_class=? AND total_fare IS NOT NULL AND total_fare > 0",
        conn, params=(origin, destination, fare_class)
    )
    conn.close()
    
    if df.empty:
        return {"error": "No data for this route/class combination"}
    
    df['window_int'] = df['advance_purchase_window'].apply(normalize_window)
    df['carrier'] = df['carrier'].apply(normalize_carrier)
    
    # Route-level KPIs
    median_fare = float(df['total_fare'].median())
    avg_fare = float(df['total_fare'].mean())
    min_fare = float(df['total_fare'].min())
    max_fare = float(df['total_fare'].max())
    obs = len(df)
    
    # Airline comparison (group by carrier)
    airline_stats = []
    for carrier, grp in df.groupby('carrier'):
        # Filter out non-real carrier names
        if carrier in ('Recommended', '2nd Fastest', '3rd Fastest'):
            continue
        airline_stats.append({
            "carrier": carrier,
            "median": round(float(grp['total_fare'].median())),
            "average": round(float(grp['total_fare'].mean())),
            "min": round(float(grp['total_fare'].min())),
            "max": round(float(grp['total_fare'].max())),
            "count": len(grp)
        })
    airline_stats.sort(key=lambda x: (x['carrier'] == 'Other', x['median']))
    
    # Lead-time comparison
    lead_stats = []
    for w, grp in df.groupby('window_int'):
        if w is None:
            continue
        lead_stats.append({
            "window": f"T+{w}",
            "window_int": int(w),
            "median": round(float(grp['total_fare'].median())),
            "average": round(float(grp['total_fare'].mean())),
            "min": round(float(grp['total_fare'].min())),
            "max": round(float(grp['total_fare'].max())),
        })
    lead_stats.sort(key=lambda x: x['window_int'])
    
    return {
        "origin": origin,
        "destination": destination,
        "fare_class": fare_class,
        "median_fare": round(median_fare),
        "avg_fare": round(avg_fare),
        "min_fare": round(min_fare),
        "max_fare": round(max_fare),
        "observations": obs,
        "airline_stats": airline_stats,
        "lead_stats": lead_stats
    }


# ──────────────────────────────────────────────────────────
# 5. HEATMAP — powers the sector heatmap on Route page
# ──────────────────────────────────────────────────────────
@app.get("/api/heatmap")
def get_heatmap(fare_class: str = "Economy"):
    df = load_all_flights()
    df = df[df['fare_class'] == fare_class]
    tariffs = get_tariffs()
    
    routes = sorted(df['route_city'].unique().tolist())
    windows = [1, 7, 15, 30, 45]
    
    matrix = {}
    for r in routes:
        matrix[r] = {}
        route_df = df[df['route_city'] == r]
        for w in windows:
            grp = route_df[route_df['window_int'] == w]
            if len(grp) > 0:
                median = float(grp['total_fare'].median())
                base = tariffs.get((r, fare_class, w), median)
                idx = round((median / base) * 100, 1)
                matrix[r][f"T+{w}"] = idx
            else:
                matrix[r][f"T+{w}"] = None
                
    return {"routes": routes, "windows": [f"T+{w}" for w in windows], "heatmap": matrix}


# ──────────────────────────────────────────────────────────
# 6. AIRLINE / OTA COMPARISON — powers the Airline & OTA page
# ──────────────────────────────────────────────────────────
@app.get("/api/source-analysis")
def get_source_analysis(mode: str = "airline"):
    df = load_all_flights()
    
    results = []
    if mode == "airline":
        for carrier, grp in df.groupby('carrier'):
            if carrier in ('Recommended', '2nd Fastest', '3rd Fastest'):
                continue
            results.append({
                "name": carrier,
                "avg_fare": round(float(grp['total_fare'].mean())),
                "median": round(float(grp['total_fare'].median())),
                "min": round(float(grp['total_fare'].min())),
                "max": round(float(grp['total_fare'].max())),
                "routes": grp['route_iata'].nunique(),
                "observations": len(grp)
            })
    else:
        # Known airlines that act as direct booking platforms
        direct_channels = {'IndiGo', 'Akasa Air', 'Air India Express', 'Air India', 'SpiceJet', 'Other'}
        for platform, grp in df.groupby('platform'):
            if platform in direct_channels:
                continue
            results.append({
                "name": platform,
                "avg_fare": round(float(grp['total_fare'].mean())),
                "median": round(float(grp['total_fare'].median())),
                "min": round(float(grp['total_fare'].min())),
                "max": round(float(grp['total_fare'].max())),
                "routes": grp['route_iata'].nunique(),
                "observations": len(grp)
            })
    
    results.sort(key=lambda x: (x['name'] != 'Other', x['observations']), reverse=True)
    return results


# ──────────────────────────────────────────────────────────
# 7. LEAD-TIME ANALYSIS — powers the Lead-Time page
# ──────────────────────────────────────────────────────────
@app.get("/api/leadtime")
def get_leadtime(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    carrier: Optional[str] = None,
    fare_class: str = "Economy"
):
    df = load_all_flights()
    if fare_class and fare_class != "All":
        df = df[df['fare_class'] == fare_class]
    
    if origin:
        df = df[df['origin'] == origin]
    if destination:
        df = df[df['destination'] == destination]
    if carrier and carrier != "All":
        df = df[df['carrier'] == carrier]
    
    results = []
    for w, grp in df.groupby('window_int'):
        results.append({
            "window": f"T+{int(w)}",
            "window_int": int(w),
            "median": round(float(grp['total_fare'].median())),
            "average": round(float(grp['total_fare'].mean())),
            "min": round(float(grp['total_fare'].min())),
            "max": round(float(grp['total_fare'].max())),
            "count": len(grp)
        })
    results.sort(key=lambda x: x['window_int'])
    return results




# ──────────────────────────────────────────────────────────
# 9. SYSTEM STATUS — powers the System Status page
# ──────────────────────────────────────────────────────────
@app.get("/api/system-status")
def get_system_status():
    results = []
    results.append({
        "source": "DGCA Passenger Traffic Data",
        "type": "Static Database",
        "status": "Operational",
        "last_collection": "2026-09-29T10:00:00",
        "records": 48200,
        "coverage": "Historical"
    })
    
    results.append({
        "source": "Airline Tariff Sheet PDFs",
        "type": "Static Document",
        "status": "Operational",
        "last_collection": "2026-09-29T10:00:00",
        "records": 85,
        "coverage": "Base Fares"
    })
    return results

import os
import pandas as pd
from fastapi.staticfiles import StaticFiles

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(root_dir):
    app.mount("/pdfs", StaticFiles(directory=root_dir), name="pdfs")

@app.get("/api/static/pdfs")
def get_pdf_list():
    return ["TARIFF-SHEET-AS-ON-28-NOV-24.pdf"]

traffic_dir = os.path.join(root_dir, "data", "dgca-data")
if os.path.exists(traffic_dir):
    app.mount("/dgca-data", StaticFiles(directory=traffic_dir), name="dgca-data")

@app.get("/api/static/dgca")
def get_dgca_data():
    if not os.path.exists(traffic_dir):
        return []
    
    # We only used the .csv files from this folder
    csv_files = [f for f in os.listdir(traffic_dir) if f.endswith('.csv')]
    csv_files.sort()
    return csv_files


# ──────────────────────────────────────────────────────────
# 10. DATA QUALITY — powers the Data Quality page
# ──────────────────────────────────────────────────────────
@app.get("/api/data-quality")
def get_data_quality():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
    with_fare = conn.execute("SELECT COUNT(*) FROM flights WHERE total_fare IS NOT NULL AND total_fare > 0").fetchone()[0]
    with_base = conn.execute("SELECT COUNT(*) FROM flights WHERE base_fare IS NOT NULL AND base_fare > 0").fetchone()[0]
    with_taxes = conn.execute("SELECT COUNT(*) FROM flights WHERE taxes IS NOT NULL AND taxes > 0").fetchone()[0]
    
    # Source-level quality
    rows = conn.execute(
        "SELECT platform, COUNT(*) as cnt, MAX(scraped_at) as last_scraped, "
        "SUM(CASE WHEN total_fare IS NOT NULL AND total_fare > 0 THEN 1 ELSE 0 END) as valid "
        "FROM flights GROUP BY platform ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    
    source_quality = []
    for r in rows:
        coverage = round(r['valid'] / r['cnt'] * 100, 1) if r['cnt'] > 0 else 0
        source_quality.append({
            "source": r['platform'],
            "coverage": f"{coverage}%",
            "last_collection": r['last_scraped'],
            "records": r['cnt'],
            "issues": "—" if coverage > 95 else "Some missing values"
        })
    
    return {
        "total_records": total,
        "fare_completeness": round(with_fare / total * 100, 1) if total > 0 else 0,
        "base_fare_completeness": round(with_base / total * 100, 1) if total > 0 else 0,
        "tax_completeness": round(with_taxes / total * 100, 1) if total > 0 else 0,
        "source_quality": source_quality
    }


# ──────────────────────────────────────────────────────────
# 11. FILTER OPTIONS — powers dropdown population
# ──────────────────────────────────────────────────────────
@app.get("/api/filters")
def get_filters():
    conn = get_db()
    origins = [r[0] for r in conn.execute("SELECT DISTINCT origin FROM flights ORDER BY origin").fetchall()]
    destinations = [r[0] for r in conn.execute("SELECT DISTINCT destination FROM flights ORDER BY destination").fetchall()]
    carriers = [r[0] for r in conn.execute("SELECT DISTINCT carrier FROM flights WHERE carrier NOT IN ('Recommended','2nd Fastest','3rd Fastest') ORDER BY carrier").fetchall()]
    platforms = [r[0] for r in conn.execute("SELECT DISTINCT platform FROM flights ORDER BY platform").fetchall()]
    fare_classes = [r[0] for r in conn.execute("SELECT DISTINCT fare_class FROM flights ORDER BY fare_class").fetchall()]
    windows = [r[0] for r in conn.execute("SELECT DISTINCT advance_purchase_window FROM flights ORDER BY advance_purchase_window").fetchall()]
    conn.close()
    return {
        "origins": origins,
        "destinations": destinations,
        "carriers": carriers,
        "platforms": platforms,
        "fare_classes": fare_classes,
        "windows": windows
    }


# ──────────────────────────────────────────────────────────
# 12. PRICES (existing, kept for backward compat)
# ──────────────────────────────────────────────────────────
@app.get("/api/prices")
def get_prices(fare_class: str = "Economy"):
    weights = get_weights()
    tariffs = get_tariffs()
    
    conn = get_db()
    df = pd.read_sql_query("SELECT origin, destination, total_fare FROM flights WHERE total_fare IS NOT NULL AND fare_class=?", conn, params=(fare_class,))
    conn.close()
    
    route_fares = {}
    for _, row in df.iterrows():
        route = route_key(row['origin'], row['destination'])
        if route in weights:
            if route not in route_fares:
                route_fares[route] = []
            route_fares[route].append(row['total_fare'])
    
    results = []
    for route, fares in route_fares.items():
        avg_scraped = sum(fares) / len(fares)
        dgca = tariffs.get((route, fare_class, 15), 0)
        variance = ((avg_scraped - dgca) / dgca) * 100 if dgca > 0 else 0
        results.append({
            "route": route,
            "scraped_avg": avg_scraped,
            "dgca_avg": dgca,
            "variance_pct": variance
        })
    
    for route in weights.keys():
        if route not in route_fares:
            results.append({
                "route": route,
                "scraped_avg": None,
                "dgca_avg": tariffs.get((route, fare_class, 15), 0),
                "variance_pct": None
            })
    return results


# ──────────────────────────────────────────────────────────
# 13. ROUTES (existing, kept for backward compat)
# ──────────────────────────────────────────────────────────
@app.get("/api/routes")
def get_routes():
    weights = get_weights()
    tariffs = get_tariffs()
    return [{"route": r, "weight": w, "dgca_avg": tariffs.get((r, "Economy", 15), None)} for r, w in weights.items()]


# ──────────────────────────────────────────────────────────
# 14. ELASTICITY (existing, kept for backward compat)
# ──────────────────────────────────────────────────────────
@app.get("/api/elasticity")
def get_elasticity(route: str, fare_class: str = "Economy"):
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT origin, destination, advance_purchase_window, total_fare FROM flights WHERE total_fare IS NOT NULL AND fare_class=?",
        conn, params=(fare_class,)
    )
    conn.close()
    
    fares_by_window = {}
    for _, row in df.iterrows():
        r = route_key(row['origin'], row['destination'])
        if r == route:
            w = normalize_window(row['advance_purchase_window'])
            if w is not None:
                if w not in fares_by_window:
                    fares_by_window[w] = []
                fares_by_window[w].append(row['total_fare'])
    
    results = []
    for w, fares in fares_by_window.items():
        results.append({"window": w, "avg_fare": sum(fares) / len(fares)})
    results.sort(key=lambda x: x['window'])
    return {"route": route, "data": results}
