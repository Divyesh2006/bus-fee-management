import sqlite3
import csv

# Connect to (or create) the database file
conn = sqlite3.connect('transport.db')
cursor = conn.cursor()

print("--- Database 'transport.db' opened ---")

# --- 1. Create the Fares Table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS fares (
    distance_km REAL PRIMARY KEY,
    zone_name TEXT NOT NULL,
    semester_fare REAL NOT NULL
)
''')
print("Table 'fares' checked/created.")

# --- 2. Create the Logs Table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date TEXT NOT NULL,
    bus_id TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    cost REAL NOT NULL
)
''')
print("Table 'logs' checked/created.")

# --- 3. Create the Fuel Prices Table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS fuel_prices (
    month_year TEXT PRIMARY KEY,
    price REAL NOT NULL
)
''')
print("Table 'fuel_prices' checked/created.")

# --- 4. Create the Semester Costs Table (NEW) ---
# This table will store the components of the total cost calculation
cursor.execute('''
CREATE TABLE IF NOT EXISTS semester_costs (
    cost_key TEXT PRIMARY KEY,
    cost_value REAL NOT NULL
)
''')
print("Table 'semester_costs' checked/created.")


# --- Populate Tables with Default Data ---

# Default fares
default_fares = [
    (8.0, "Pallipalayam", 15000.0),
    (10.0, "SPB Colony", 18000.0),
    (19.0, "KSR College", 29000.0),
    (24.0, "Tiruchengode", 35000.0),
    (55.0, "Namakkal", 58000.0)
]
cursor.executemany("INSERT OR IGNORE INTO fares (distance_km, zone_name, semester_fare) VALUES (?, ?, ?)", default_fares)
print(f"Populated 'fares' with default entries.")

# Default logs (check if logs table is empty first)
cursor.execute("SELECT COUNT(*) FROM logs")
if cursor.fetchone()[0] == 0:
    default_logs = [
        ('2025-10-30', 'VCET-BUS-06', 'Maintenance', 'Scheduled oil change', 7500),
        ('2025-10-31', 'VCET-BUS-09', 'Fuel', 'Diesel fill-up (150 Ltrs)', 14200)
    ]
    cursor.executemany("INSERT INTO logs (log_date, bus_id, category, description, cost) VALUES (?, ?, ?, ?, ?)", default_logs)
    print(f"Populated 'logs' with default entries.")

# Populate Fuel Prices
try:
    with open('Diesel dataset.txt', mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader) # Skip the header
        fuel_data = []
        for row in reader:
            if row:
                month_year = row[0].strip().replace('"', '')
                price = float(row[1])
                fuel_data.append((month_year, price))
        cursor.executemany("INSERT OR IGNORE INTO fuel_prices (month_year, price) VALUES (?, ?)", fuel_data)
        print(f"Populated 'fuel_prices' with {len(fuel_data)} entries.")
except FileNotFoundError:
    print("WARNING: 'Diesel dataset.txt' not found. Skipping fuel price population.")
except Exception as e:
    print(f"An error occurred while reading fuel data: {e}")

# Default semester costs
default_costs = [
    ('total_semester_cost', 600000.0),
    ('total_fuel_cost_sem', 250000.0),
    ('total_maint_cost_sem', 100000.0),
    ('total_salary_cost_sem', 102000.0),
    ('total_insurance_cost_sem', 42000.0),
    ('total_contingency_cost', 54400.0),
    ('total_usage_units', 100000.0),
    ('cost_per_usage_unit', 6.0)
]
cursor.executemany("INSERT OR IGNORE INTO semester_costs (cost_key, cost_value) VALUES (?, ?)", default_costs)
print("Populated 'semester_costs' with default entries.")


# Save changes and close
conn.commit()
conn.close()

print("--- Database setup complete and connection closed. ---")