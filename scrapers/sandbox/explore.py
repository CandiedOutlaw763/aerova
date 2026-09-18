import json
import re

def explore():
    with open('mmt_flight_data_intercepted.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    keys = set()
    def extract_keys(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if 'fare' in k.lower() or 'tax' in k.lower() or 'price' in k.lower():
                    keys.add(k)
                extract_keys(v)
        elif isinstance(d, list):
            for item in d:
                extract_keys(item)
                
    extract_keys(data)
    print("Keys found:", keys)

if __name__ == "__main__":
    explore()
