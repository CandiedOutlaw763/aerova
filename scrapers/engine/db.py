import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'flights.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            origin TEXT,
            destination TEXT,
            carrier TEXT,
            advance_purchase_window TEXT,
            fare_class TEXT,
            booking_class TEXT,
            base_fare INTEGER,
            taxes INTEGER,
            total_fare INTEGER,
            scraped_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_flights(platform, origin, destination, advance_window, fare_class, flights_list):
    """
    flights_list should be a list of dicts:
    [{'carrier': 'IndiGo', 'base_fare': 4000, 'taxes': 1000, 'total_fare': 5000}, ...]
    """
    if not flights_list:
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    
    for f in flights_list:
        base_fare = f.get('base_fare')
        taxes = f.get('taxes')
        total_fare = f.get('total_fare')
        
        base_fare = int(base_fare) if base_fare else None
        taxes = int(taxes) if taxes else None
        total_fare = int(total_fare) if total_fare else 0

        cursor.execute('''
            INSERT INTO flights (
                platform, origin, destination, carrier, 
                advance_purchase_window, fare_class, booking_class, base_fare, taxes, total_fare, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            platform, origin, destination, f.get('carrier', ''),
            advance_window, fare_class, f.get('booking_class', ''),
            base_fare, taxes, total_fare, now
        ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
