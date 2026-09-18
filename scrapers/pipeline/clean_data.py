import sqlite3
import os
import math

# Paths
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine', 'flights.db'))

# Aviation Security Fee (ASF) - standard domestic
ASF = 236

# User Development Fee (UDF) approximations for major airports (Origin based)
# Can be refined with exact AAI tariffs later
UDF_MAP = {
    "DEL": 150,
    "BOM": 150,
    "BLR": 350,
    "HYD": 300,
    "MAA": 200,
    "CCU": 250,
    "DEFAULT": 200
}

def get_gst_rate(fare_class: str) -> float:
    fare_class = (fare_class or "Economy").lower()
    if "business" in fare_class or "premium" in fare_class or "first" in fare_class:
        return 0.12
    return 0.05

def impute_missing_taxes():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Select rows where base_fare or taxes is missing (NULL) but total_fare exists
    cursor.execute('''
        SELECT id, origin, fare_class, total_fare 
        FROM flights 
        WHERE (base_fare IS NULL OR taxes IS NULL OR base_fare = 0 OR taxes = 0) 
        AND total_fare IS NOT NULL AND total_fare > 0
    ''')
    rows = cursor.fetchall()
    
    if not rows:
        print("No flights found with missing tax breakdown.")
        return
        
    print(f"Found {len(rows)} flights with missing base_fare/taxes. Imputing...")
    
    updates = []
    for row_id, origin, fare_class, total_fare in rows:
        origin_code = origin.upper() if origin else ""
        udf = UDF_MAP.get(origin_code, UDF_MAP["DEFAULT"])
        fixed_fees = ASF + udf
        
        gst_rate = get_gst_rate(fare_class)
        
        # total_fare = taxable_base + (taxable_base * gst) + fixed_fees
        # taxable_base * (1 + gst) = total_fare - fixed_fees
        
        # Safeguard: if total_fare is weirdly low (e.g. less than fixed fees)
        if total_fare <= fixed_fees:
            base_fare = total_fare
            taxes = 0
        else:
            taxable_base = (total_fare - fixed_fees) / (1 + gst_rate)
            base_fare = math.floor(taxable_base)
            taxes = total_fare - base_fare # Total taxes = fixed_fees + GST
            
        updates.append((base_fare, taxes, row_id))
        
    # Batch update
    cursor.executemany('''
        UPDATE flights 
        SET base_fare = ?, taxes = ? 
        WHERE id = ?
    ''', updates)
    
    conn.commit()
    conn.close()
    
    print(f"Successfully imputed and updated {len(updates)} records in the database.")

def remove_duplicates():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SQLite logic to delete exact duplicates on the same day
    # We keep the row with the lowest ID (the first one scraped)
    delete_query = '''
        DELETE FROM flights 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM flights 
            GROUP BY 
                platform, origin, destination, carrier, 
                advance_purchase_window, fare_class, 
                total_fare, substr(scraped_at, 1, 10)
        )
    '''
    
    cursor.execute("SELECT COUNT(*) FROM flights")
    initial_count = cursor.fetchone()[0]
    
    cursor.execute(delete_query)
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Deduplication complete. Removed {deleted_count} duplicate rows (Started with {initial_count}).")

if __name__ == "__main__":
    remove_duplicates()
    impute_missing_taxes()
