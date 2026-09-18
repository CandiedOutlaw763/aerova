import json
from engine.spiders.indigo import Spider as IndigoSpider
from engine.spiders.akasa_air import Spider as AkasaSpider
from engine.spiders.spicejet import Spider as SpiceJetSpider
from engine.spiders.air_india import Spider as AirIndiaSpider
from engine.spiders.air_india_express import Spider as AirIndiaExpressSpider

def run_tests():
    spiders = [
        IndigoSpider(),
        AkasaSpider(),
        SpiceJetSpider(),
        AirIndiaSpider(),
        AirIndiaExpressSpider()
    ]
    
    results = {}
    print(f"Testing 5 Airlines for DEL -> BOM, 28/10/2026")
    
    for spider in spiders:
        try:
            print(f"Running {spider.name}...")
            flights = spider.scrape("DEL", "BOM", "T+15", "Economy", "28/10/2026")
            print(f"[{spider.name}] Extracted {len(flights)} flights")
            results[spider.name] = flights
        except Exception as e:
            print(f"[{spider.name}] Failed with error: {e}")
            
    with open("airline_results_sample.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("Done! Saved to airline_results_sample.json")

if __name__ == "__main__":
    run_tests()
