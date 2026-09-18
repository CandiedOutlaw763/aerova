import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine')))
from spiders.easemytrip import Spider

class MySpider(Spider):
    def _parse(self, origin, destination, advance_window, fare_class, logs):
        for entry in logs:
            try:
                log = json.loads(entry['message'])['message']
                if log['method'] == 'Network.responseReceived':
                    resp = log['params']['response']
                    url = resp['url']
                    if 'AirAvail_Lights' in url:
                        body_data = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': log['params']['requestId']})
                        data = json.loads(body_data['body'])
                        if 'j' in data and data['j'] and 's' in data['j'][0]:
                            print(json.dumps(data['j'][0]['s'][0], indent=2))
                            # find one with high fare
                            for f in data['j'][0]['s']:
                                if f.get('TF', 0) > 20000:
                                    print("HIGH FARE FLIGHT:")
                                    print(json.dumps(f, indent=2))
                                    break
                            return super()._parse(origin, destination, advance_window, fare_class, logs)
            except Exception:
                pass
        return super()._parse(origin, destination, advance_window, fare_class, logs)

spider = MySpider()
flights = spider.scrape("DEL", "BOM", "T+15", "Economy", "28/09/2026")
print(f"Total flights: {len(flights)}")
