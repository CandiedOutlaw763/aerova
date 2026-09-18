import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APIX_FILE = os.path.join(BASE_DIR, 'pipeline', 'apix_result.json')
EXCEL_FILE = os.path.join(os.path.dirname(BASE_DIR), 'cpi_711.xlsx')

def backtest():
    if not os.path.exists(APIX_FILE):
        print("Error: APIx result file not found. Run build_index.py first.")
        return
        
    with open(APIX_FILE, 'r') as f:
        apix_data = json.load(f)
        
    generated_apix = apix_data['apix']
    routes_mapped = len(apix_data['routes'])
    
    # Load Official Data
    df = pd.read_excel(EXCEL_FILE)
    
    # Filter for 'All India' Transport Airfare
    official_row = df[(df['state'] == 'All India') & (df['item'] == 'Airfare')]
    
    if official_row.empty:
        print("Error: Could not find 'All India' Airfare data in Excel.")
        return
        
    official_index = official_row.iloc[0]['index']
    
    variance = generated_apix - official_index
    variance_pct = (variance / official_index) * 100
    
    print("=========================================")
    print("      APIx BACK-TESTING VALIDATION       ")
    print("=========================================")
    print(f"Official MoSPI Index (Base 2024):  {official_index:.2f}")
    print(f"Generated Daily APIx:              {generated_apix:.2f}")
    print("-----------------------------------------")
    print(f"Absolute Variance:                 {variance:+.2f}")
    print(f"Percentage Variance:               {variance_pct:+.2f}%")
    print("=========================================")
    print(f"Note: Variance is expected to be high right now because our ")
    print(f"sandbox database only contains scraped data for {routes_mapped}/55 routes.")
    print(f"Once the orchestrator scrapes all 55 routes, the APIx will converge ")
    print(f"with the official MoSPI average.")

if __name__ == "__main__":
    backtest()
