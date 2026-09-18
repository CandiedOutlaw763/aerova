"""Integration test for IndiGo spider."""
import sys
sys.path.insert(0, '.')
from engine.spiders.indigo import Spider

def run():
    spider = Spider()
    print("Testing IndiGo Spider...")
    flights = spider.scrape(
        origin="DEL",
        destination="BOM",
        advance_window="15",
        fare_class="Y",
        date_str="2026-09-30"
    )
    
    print(f"\nTotal flights returned: {len(flights)}")
    for f in flights[:5]:
        print(f"  {f['carrier']} | {f['origin']}->{f['destination']} | {f['fare_class']} | INR {f['total_fare']}")

if __name__ == "__main__":
    run()
