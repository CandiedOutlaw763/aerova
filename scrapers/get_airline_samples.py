from engine.spiders.goibibo import Spider as GoibiboSpider

def run():
    print("Fetching flight data for DEL -> BOM for the 5 target airlines...")
    spider = GoibiboSpider()
    # Using T+15 window (14-Oct-2026 is approx T+15 from end of sept)
    flights = spider.scrape("DEL", "BOM", "T+15", "Economy", "14-Oct-2026")
    
    target_carriers = {"IndiGo": [], "Air India": [], "Air India Express": [], "Akasa Air": [], "SpiceJet": []}
    
    for f in flights:
        c = f['carrier']
        if "IndiGo" in c: target_carriers["IndiGo"].append(f)
        elif "Air India" == c: target_carriers["Air India"].append(f)
        elif "Air India Express" in c: target_carriers["Air India Express"].append(f)
        elif "Akasa" in c: target_carriers["Akasa Air"].append(f)
        elif "SpiceJet" in c: target_carriers["SpiceJet"].append(f)
        
    print("\n--- FLIGHT RESULTS FOR 5 DIRECT AIRLINES ---")
    for name, flists in target_carriers.items():
        if flists:
            f = flists[0]
            print(f"[{name}] {f['origin']} -> {f['destination']} | Base Fare: {f.get('base_fare', 'N/A')} | Total Fare: {f['total_fare']}")
        else:
            print(f"[{name}] No flights found in this OTA scrape.")

if __name__ == "__main__":
    run()
