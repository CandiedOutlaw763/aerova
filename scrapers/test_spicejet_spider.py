from engine.spiders.spicejet import SpiceJetSpider

def run():
    spider = SpiceJetSpider()
    flights = spider.scrape("DEL", "BOM", "15", "Economy", "2026-09-30")
    print(f"\nFinal Result: Found {len(flights)} flights")
    for flight in flights:
        print(f"[{flight['carrier']}] {flight['origin']}->{flight['destination']} | {flight['departure_time']} -> {flight['arrival_time']} | {flight['total_fare']} INR (Base: {flight['base_fare']}, Tax: {flight['taxes']})")

if __name__ == "__main__":
    run()
