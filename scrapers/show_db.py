import sqlite3
import pandas as pd

def show_results():
    conn = sqlite3.connect('c:/Users/siddh/OneDrive/Desktop/sih 2026/scrapers/engine/flights.db')
    query = """
    SELECT platform, carrier, origin, destination, base_fare, taxes, total_fare 
    FROM flights
    """
    df = pd.read_sql_query(query, conn)
    
    if len(df) == 0:
        print("No flights found in DB.")
        return
        
    print(f"Total flights found: {len(df)}")
    
    # Sort by total_fare
    df = df.sort_values(by=['platform', 'total_fare'])
    
    with open("results.md", "w", encoding="utf-8") as f:
        f.write("\n| Platform | Carrier | Origin | Dest | Base Fare | Taxes | Total Fare |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        
        for _, row in df.iterrows():
            f.write(f"| {row['platform']} | {row['carrier']} | {row['origin']} | {row['destination']} | ₹{row['base_fare']} | ₹{row['taxes']} | **₹{row['total_fare']}** |\n")
    
    print("Results saved to results.md")
        
    conn.close()

if __name__ == "__main__":
    show_results()
