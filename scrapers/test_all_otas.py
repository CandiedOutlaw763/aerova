import json
from engine.spiders import mmt, cleartrip, easemytrip, goibibo, ixigo, yatra

def run_all():
    print("Testing 6 OTAs for DEL -> BOM, 28/10/2026")
    results = {}
    
    # 1. MakeMyTrip
    try:
        print("Running MMT...")
        res = mmt.Spider().scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
        results['MMT'] = res[:3]
    except Exception as e:
        results['MMT'] = f"Error: {e}"

    # 2. Cleartrip
    try:
        print("Running Cleartrip...")
        res = cleartrip.Spider().scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
        results['Cleartrip'] = res[:3]
    except Exception as e:
        results['Cleartrip'] = f"Error: {e}"
        
    # 3. EaseMyTrip
    try:
        print("Running EaseMyTrip...")
        res = easemytrip.Spider().scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
        results['EaseMyTrip'] = res[:3]
    except Exception as e:
        results['EaseMyTrip'] = f"Error: {e}"
        
    # 4. Goibibo
    try:
        print("Running Goibibo...")
        res = goibibo.Spider().scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
        results['Goibibo'] = res[:3]
    except Exception as e:
        results['Goibibo'] = f"Error: {e}"

    # 5. Ixigo
    try:
        print("Running Ixigo...")
        res = ixigo.Spider().scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
        results['Ixigo'] = res[:3]
    except Exception as e:
        results['Ixigo'] = f"Error: {e}"

    # 6. Yatra
    try:
        print("Running Yatra...")
        res = yatra.Spider().scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
        results['Yatra'] = res[:3]
    except Exception as e:
        results['Yatra'] = f"Error: {e}"

    with open("ota_results_sample.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print("Done! Saved to ota_results_sample.json")

if __name__ == "__main__":
    run_all()
