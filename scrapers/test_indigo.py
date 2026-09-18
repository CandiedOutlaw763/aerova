import json
from engine.spiders.indigo import Spider as IndiGoSpider

def run():
    print("Testing IndiGo Direct API Scraper...")
    spider = IndiGoSpider()
    # Testing for DEL -> BOM on 30-Sep-2026 as per user's prompt
    flights = spider.scrape("DEL", "BOM", "T+15", "Economy", "30-Sep-2026")
    
    if flights:
        print(f"\nSuccessfully extracted {len(flights)} flights from IndiGo!")
        for i, f in enumerate(flights[:5]):
            print(f"Flight {i+1}: {f['origin']} -> {f['destination']} | Departure: {f['departure_time']} | Arrival: {f['arrival_time']} | Base Fare: {f['base_fare']} | Taxes: {f['taxes']} | Total Fare: {f['total_fare']}")
    else:
        print("\nNo flights extracted or scraping failed.")

if __name__ == "__main__":
    run()
