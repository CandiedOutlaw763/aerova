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

if __name__ == "__main__":
    import sys
    # Essential on Windows to avoid freezing when starting new processes
    multiprocessing.freeze_support()
    
    # Test run: DEL->BOM, T+15, Economy and Business, 28 Sep 2026
    # Optional spider testing from cmd line
    if len(sys.argv) > 1:
        spiders_arg = sys.argv[1].split(',')
        run_orchestrator("DEL", "BOM", "15", ["Economy", "Business"], "28/09/2026", spider_filter=spiders_arg)
    else:
        run_orchestrator("DEL", "BOM", "15", ["Economy", "Business"], "28/09/2026")
