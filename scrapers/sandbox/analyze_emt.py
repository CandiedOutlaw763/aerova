from bs4 import BeautifulSoup

def analyze():
    with open("emt_test.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    # EaseMyTrip uses a div with class 'flt-result' or something for flight listings.
    # Let's just find the divs containing the text 'IndiGo' or 'Air India' or 'SpiceJet'.
    
    flight_nodes = soup.find_all(text=lambda t: t and t.strip() in ['IndiGo', 'Air India', 'SpiceJet', 'Akasa Air'])
    
    print(f"Found {len(flight_nodes)} flight names.")
    if flight_nodes:
        # Get the parent div of the first flight
        parent = flight_nodes[0].parent
        # Go up a few levels to get the row
        for i in range(5):
            parent = parent.parent
        print("Flight Row HTML:")
        print(str(parent)[:500])
        
if __name__ == "__main__":
    analyze()
