import importlib
import multiprocessing
import time
from db import init_db, save_flights

SPIDERS = [
    "mmt",              # MakeMyTrip
    "goibibo",          # Goibibo
    "yatra",            # Yatra
    "easemytrip",       # EaseMyTrip
    "cleartrip",        # Cleartrip
    "ixigo",            # Ixigo
    "indigo",           # IndiGo (direct)
    "air_india",        # Air India (direct)
    "spicejet",         # SpiceJet (direct)
    "akasa_air",        # Akasa Air (direct)
    "air_india_express",# Air India Express (direct)
]

def load_spider(name):
    module = importlib.import_module(f"spiders.{name}")
    return module.Spider()

def _run_single_spider(spider_name, origin, destination, advance_window, fare_class, date_str):
    """
    Function to run a single spider (intended to be run in a subprocess).
    It writes to the database directly.
    """
    try:
        spider = load_spider(spider_name)
        flights = []
        for attempt in range(3):
            # The scraping includes its own timeout logic, plus the utils patch limits CDP buffering
            flights = spider.scrape(origin, destination, advance_window, fare_class, date_str)
            if flights:
                break
            print(f"[{spider_name}] Attempt {attempt+1} yielded 0 flights. Retrying...")
            time.sleep(2)
            
        if flights:
            save_flights(spider.name, origin, destination, advance_window, fare_class, flights)
            print(f"Saved {len(flights)} flights from {spider_name}.")
        else:
            print(f"No flights found from {spider_name} after 3 attempts.")
    except Exception as e:
        print(f"Error running {spider_name} spider: {e}")
        import traceback
        traceback.print_exc()

def run_orchestrator(origin, destination, advance_window, fare_classes, date_str, spider_filter=None):
    """
    Run all (or a subset of) spiders for one route/date, isolating each in a subprocess
    to prevent hung Chrome instances from stalling the entire queue.
    """
    start_time = time.time()
    init_db()
    
    spiders_to_run = spider_filter if spider_filter else SPIDERS
    
    # 5 minutes max wall-time per spider process (3 attempts * ~60s + margin)
    PROCESS_TIMEOUT = 300 
    BATCH_SIZE = 1
    
    if isinstance(fare_classes, str):
        fare_classes = [fare_classes]
        
    for fc in fare_classes:
        print(f"\n======================================")
        print(f"  STARTING FARE CLASS: {fc}")
        print(f"======================================")
        
        for i in range(0, len(spiders_to_run), BATCH_SIZE):
            batch = spiders_to_run[i:i+BATCH_SIZE]
            print(f"\n--- Running Batch: {', '.join(batch)} for {fc} ---")
            
            processes = []
            for spider_name in batch:
                p = multiprocessing.Process(
                    target=_run_single_spider, 
                    args=(spider_name, origin, destination, advance_window, fc, date_str)
                )
                p.start()
                processes.append((spider_name, p))
                # Stagger browser launches to prevent undetected_chromedriver patching collision
                time.sleep(2)
                
            for spider_name, p in processes:
                p.join(PROCESS_TIMEOUT)
                if p.is_alive():
                    print(f"[{spider_name}] Timeout ({PROCESS_TIMEOUT}s) reached! Force killing subprocess.")
                    p.terminate()
                    p.join()
                    try:
                        p.kill() # Hard kill just in case
                    except Exception:
                        pass
                    
    total_time = time.time() - start_time
    print(f"\n[Orchestrator] Finished! Total time taken: {total_time:.2f} seconds.")

CITY_TO_IATA = {
    "DELHI": "DEL", "MUMBAI": "BOM", "BENGALURU": "BLR", "HYDERABAD": "HYD",
    "CHENNAI": "MAA", "KOLKATA": "CCU", "AHMEDABAD": "AMD", "PUNE": "PNQ",
    "SRINAGAR": "SXR", "GUWAHATI": "GAU", "DABOLIM": "GOI", "PATNA": "PAT",
    "KOCHI": "COK", "LUCKNOW": "LKO", "BHUBANESWAR": "BBI", "AMRITSAR": "ATQ",
    "BAGDOGRA": "IXB", "JAIPUR": "JAI", "INDORE": "IDR", "VARANASI": "VNS",
    "COIMBATORE": "CJB", "CHANDIGARH": "IXC", "TIRUPATI": "TIR", "AGARTALA": "IXA",
    "RAIPUR": "RPR", "LEH": "IXL", "NAGPUR": "NAG", "DEHRADUN": "DED",
    "UDAIPUR": "UDR", "JAMMU": "IXJ"
}

if __name__ == "__main__":
    import sys
    import argparse
    import os
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Essential on Windows to avoid freezing when starting new processes
    multiprocessing.freeze_support()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Run full scrape using top 5 routes from route_weights.csv")
    parser.add_argument("--target-class", type=str, default="Economy", help="Target fare class to scrape")
    parser.add_argument("--spiders", type=str, help="Comma separated list of spiders to run")
    args = parser.parse_args()
    
    spider_filter = args.spiders.split(',') if args.spiders else None
    
    if args.full:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        weights_path = os.path.join(BASE_DIR, 'pipeline', 'static_data', 'route_weights.csv')
        df = pd.read_csv(weights_path)
        top_5 = df.head(5)['ROUTE'].tolist()
        
        windows = [1, 7, 15, 30, 45, 60]
        base_date = datetime.now()
        
        for route in top_5:
            orig_city, dest_city = route.split('-')
            orig_iata = CITY_TO_IATA.get(orig_city)
            dest_iata = CITY_TO_IATA.get(dest_city)
            
            if not orig_iata or not dest_iata:
                print(f"Skipping route {route} due to missing IATA mapping.")
                continue
                
            for w in windows:
                target_date = base_date + timedelta(days=w)
                date_str = target_date.strftime("%d/%m/%Y")
                
                print(f"\n======================================")
                print(f" FULL SCRAPE: {orig_iata}->{dest_iata} | Window: T+{w} | Class: {args.target_class}")
                print(f"======================================")
                
                run_orchestrator(orig_iata, dest_iata, str(w), [args.target_class], date_str, spider_filter=spider_filter)
    else:
        # Default test run
        run_orchestrator("DEL", "BOM", "15", [args.target_class], "28/09/2026", spider_filter=spider_filter)
