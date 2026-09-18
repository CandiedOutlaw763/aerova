import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
}

print("Fetching IndiGo...")
try:
    response = requests.get('https://www.goindigo.in/', headers=headers, timeout=15)
    text = response.text
    print("Fetched successfully. Searching for keys...")
    
    matches = re.finditer(r'["\']?(Ocp-Apim-Subscription-Key|apiKey|api_key|token|auth)["\']?\s*[:=]\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
    found = False
    for m in matches:
        print(f"Match: {m.group(1)} = {m.group(2)}")
        found = True
        
    if not found:
        print("No keys found in main HTML.")
        
except Exception as e:
    print(f"Error: {e}")
