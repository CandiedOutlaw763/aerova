import re
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def debug_prices(filename):
    with open(f'doms/{filename}', 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    price_pattern = re.compile(r'(?:₹|Rs\.?)\s*([\d,]+)')
    texts = soup.find_all(string=price_pattern)
    for t in texts:
        m = price_pattern.search(t)
        if m:
            val = int(m.group(1).replace(',', ''))
            if val > 1000:
                parent_class = t.parent.get('class')
                print(f"{filename}: Found {val} | Tag: {t.parent.name} | Class: {parent_class} | Text: '{t.strip()[:50]}'")

debug_prices('IndiGo.html')
debug_prices('SpiceJet.html')
