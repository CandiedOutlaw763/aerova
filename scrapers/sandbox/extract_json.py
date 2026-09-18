import json
import re
from bs4 import BeautifulSoup

def extract_json_from_cleartrip(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Cleartrip uses window.CT = {...} or something similar for initial state
    # Let's search for script tags containing JSON data
    scripts = soup.find_all('script')
    for s in scripts:
        if s.string and 'window.__INITIAL_STATE__' in s.string:
            # Extract the JSON payload
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', s.string, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                print("Successfully parsed __INITIAL_STATE__ JSON!")
                # To find flight prices, we would traverse the JSON tree here
                return data
                
        # Alternative pattern for Cleartrip: window.SEARCH_PARAMS or similar
        elif s.string and '"flights"' in s.string and '"price"' in s.string:
            # Heuristic fallback: try to find any large JSON object assigned to a variable
            match = re.search(r'=\s*(\{.*?"flights".*?\});', s.string, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    print("Successfully parsed flight JSON object!")
                    return data
                except:
                    pass

    print("Could not find structured JSON in Cleartrip DOM.")
    return None

if __name__ == "__main__":
    extract_json_from_cleartrip("doms/Cleartrip.html")
