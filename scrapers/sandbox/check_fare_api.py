import json

data = json.load(open('yatra_parsed.json'))
url = 'https://flight.yatra.com/lowest-fare-service/dom2/get-fare?origin=DEL&destination=BOM&from=18-09-2026&to=08-10-2026&tripType=O&airlines=all&_i=1169578981570&src=srp'
val = json.loads(data[url])
day = val['day']['2026-09-28']
print("Airlines found:", list(day['af'].keys()))
for airline, info in day['af'].items():
    ow = info['ow'][0]
    print(f"{airline}: bf={info['bf']}, tf={info['tf']}, flight={ow['fl']}, dep={ow['ddt']}, arr={ow['adt']}")
