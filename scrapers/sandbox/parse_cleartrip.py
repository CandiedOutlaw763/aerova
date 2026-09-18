import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def parse_cleartrip():
    try:
        with open('doms/Cleartrip.html', 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        script = soup.find('script', id='__NEXT_DATA__')
        if not script:
            print("Could not find __NEXT_DATA__")
            return
            
        data = json.loads(script.string)
        print("Successfully loaded __NEXT_DATA__ JSON!")
        
        # In Next.js, the page props are usually under props.pageProps
        props = data.get('props', {}).get('pageProps', {})
        
        with open('cleartrip_next_data.json', 'w', encoding='utf-8') as out_f:
            json.dump(props, out_f, indent=2)
        print("Dumped pageProps to cleartrip_next_data.json")
                
    except Exception as e:
        print(f"Error parsing Cleartrip JSON: {e}")

if __name__ == "__main__":
    parse_cleartrip()
