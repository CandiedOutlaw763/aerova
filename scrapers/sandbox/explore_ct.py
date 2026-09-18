import json
import re

def explore():
    with open('cleartrip_next_data.json', 'r', encoding='utf-8') as f:
        data = f.read()
    
    # Let's search for "base" or "tax" near numbers
    matches = re.findall(r'"([^"]*(?:base|tax|fee|fare|price)[^"]*)"\s*:\s*([\d\.]+)', data, re.IGNORECASE)
    print("Fare keys found in Cleartrip:")
    for m in list(set(matches))[:30]:
        print(f"Key: {m[0]}, Value: {m[1]}")

if __name__ == "__main__":
    explore()
