import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

def search_ddg(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to search: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('a', class_='result__url')
    snippets = soup.find_all('a', class_='result__snippet')
    
    print(f"--- Results for: {query} ---")
    for r, s in zip(results[:5], snippets[:5]):
        print(f"URL: {r.get('href')}")
        print(f"Snippet: {s.text}")
        print("-" * 50)

search_ddg('site:github.com "makemytrip" "api" flight search')
search_ddg('site:github.com "goindigo" "api" flight')
