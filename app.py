import math
import datetime
import sqlite3
from flask import Flask, render_template, request, jsonify

# --- 1. Initialize Flask App ---
app = Flask(__name__)
DATABASE_FILE = 'transport.db'

# --- 2. Database Helper Function ---
def get_db_connection():
    """Creates a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This lets us access columns by name
    return conn

# --- 3. Admin Dashboard Route ---
@app.route('/')
def index():
    """Serves the main Admin Dashboard (index.html)."""
    return render_template('index.html')


# --- 4. Student Dashboard Route ---
@app.route('/student')
def student_page():
    """Serves the Student Dashboard (student.html)."""
    conn = get_db_connection()
    stops_from_db = conn.execute("SELECT zone_name, distance_km FROM fares ORDER BY distance_km").fetchall()
    conn.close()
    available_stops = [(stop['zone_name'], stop['distance_km']) for stop in stops_from_db]
    return render_template('student.html', available_stops=available_stops)


# --- 5. API: Admin Calculates Fares ---
@app.route('/calculate_fare', methods=['POST'])
def calculate_fare():
    """
    Calculates fares and SAVES them to the 'fares' table AND the 'semester_costs' table.
    """
    try:
        data = request.json
        
        # --- A. Get New Inputs ---
        avg_route_km_day = float(data['avg_route_km_day'])
        bus_mileage = float(data['bus_mileage'])
        maint_cost_day = float(data['maint_cost_day'])
        
        driver_salary_day = float(data['driver_salary_day'])
        insurance_cost_day = float(data['insurance_cost_day']) 
        contingency_pct = float(data['contingency_pct']) 
        days_in_semester = float(data['days_in_semester'])
        stops = data['stops'] 

        # --- B. Calculate Detailed Costs ---
        conn = get_db_connection()
        # Get the latest fuel price from the DB
        fuel_price_row = conn.execute("SELECT price FROM fuel_prices ORDER BY month_year DESC LIMIT 1").fetchone()
        if not fuel_price_row:
            return jsonify({'error': 'No fuel price data in database. Please run setup_db.py.'}), 500
        latest_fuel_price = fuel_price_row['price']
        
        # Calculate daily and semester costs
        fuel_cost_day = (avg_route_km_day / bus_mileage) * latest_fuel_price
        
        total_fuel_cost_sem = fuel_cost_day * days_in_semester
        total_maint_cost_sem = maint_cost_day * days_in_semester
        total_salary_cost_sem = driver_salary_day * days_in_semester
        total_insurance_cost_sem = insurance_cost_day * days_in_semester
        
        # Calculate total and contingency
        subtotal = total_fuel_cost_sem + total_maint_cost_sem + total_salary_cost_sem + total_insurance_cost_sem
        total_contingency_cost = subtotal * (contingency_pct / 100)
        total_semester_cost = subtotal + total_contingency_cost

        # --- C. Student-KM (Usage Unit) Logic ---
        total_usage_units = 0
        for stop in stops:
            total_usage_units += float(stop['distance']) * float(stop['students'])
        if total_usage_units == 0:
            return jsonify({'error': 'Total usage units is zero.'}), 400

        cost_per_usage_unit = total_semester_cost / total_usage_units

        # --- D. Save Fares to 'fares' table ---
        fare_breakdown_table = []
        new_fares_to_save = []
        for stop in stops:
            distance = float(stop['distance'])
            name = stop['name']
            individual_fare = distance * cost_per_usage_unit
            rounded_fare = round(individual_fare, 2)
            
            fare_breakdown_table.append({
                'name': name, 'distance': distance, 'students': stop['students'], 'fare_per_student': rounded_fare
            })
            new_fares_to_save.append((distance, name, rounded_fare))

        cursor = conn.cursor()
        cursor.execute("DELETE FROM fares")
        cursor.executemany("INSERT INTO fares (distance_km, zone_name, semester_fare) VALUES (?, ?, ?)", new_fares_to_save)
        
        # --- E. Save Breakdown to 'semester_costs' table (NEW) ---
        costs_to_save = [
            ('total_semester_cost', round(total_semester_cost, 2)),
            ('total_fuel_cost_sem', round(total_fuel_cost_sem, 2)),
            ('total_maint_cost_sem', round(total_maint_cost_sem, 2)),
            ('total_salary_cost_sem', round(total_salary_cost_sem, 2)),
            ('total_insurance_cost_sem', round(total_insurance_cost_sem, 2)),
            ('total_contingency_cost', round(total_contingency_cost, 2)),
            ('total_usage_units', round(total_usage_units, 2)),
            ('cost_per_usage_unit', round(cost_per_usage_unit, 4)),
            ('latest_fuel_price', latest_fuel_price),
            ('total_semester_kms', avg_route_km_day * days_in_semester)
        ]
        cursor.execute("DELETE FROM semester_costs")
        cursor.executemany("INSERT INTO semester_costs (cost_key, cost_value) VALUES (?, ?)", costs_to_save)
        
        conn.commit()
        conn.close()
        
        print(f"--- Fares & Cost Breakdown saved to transport.db ---")

        # --- F. Send Admin Report ---
        return jsonify({
            'total_semester_cost': round(total_semester_cost, 2),
            'total_students': sum(stop['students'] for stop in stops),
            'avg_cost_per_student': round(total_semester_cost / sum(stop['students'] for stop in stops), 2),
            'cost_breakdown_data': {
                'base_cost': round(total_fuel_cost_sem + total_maint_cost_sem, 2),
                'fixed_costs': round(total_salary_cost_sem + total_insurance_cost_sem, 2),
                'contingency': round(total_contingency_cost, 2)
            },
            'fare_breakdown': fare_breakdown_table
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 6. API: Student Checks Fee ---
@app.route('/get_student_fee', methods=['GET'])
def get_student_fee():
    """
    Looks up the student's fee AND the full cost breakdown.
    """
    stop_km = request.args.get('stop_km', type=float)
    
    conn = get_db_connection()
    # 1. Get the student's specific fare
    fare_data = conn.execute("SELECT zone_name, semester_fare FROM fares WHERE distance_km = ?", (stop_km,)).fetchone()
    
    # 2. Get the full semester cost breakdown
    costs_data = conn.execute("SELECT cost_key, cost_value FROM semester_costs").fetchall()
    conn.close()
    
    if not fare_data:
        return jsonify({'error': f'Fee for stop {stop_km} KM not found.'}), 404

    # Convert cost breakdown rows to a simple dictionary
    cost_breakdown = {row['cost_key']: row['cost_value'] for row in costs_data}

    return jsonify({
        'route': 'Velalar to Namakkal',
        'boarding_point': f"{fare_data['zone_name']} ({stop_km} KM Zone)",
        'fee_details': {
            'semester_fare': fare_data['semester_fare'],
            'monthly_fare': round(fare_data['semester_fare'] / 4, 2)
        },
        'cost_breakdown': cost_breakdown # Send the new data
    })


# --- 7. API Endpoints for Digital Logs ---
@app.route('/get_logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    logs_from_db = conn.execute("SELECT log_date, bus_id, category, description, cost FROM logs ORDER BY log_date DESC").fetchall()
    conn.close()
    logs_list = [dict(log) for log in logs_from_db]
    return jsonify(logs_list)

@app.route('/add_log', methods=['POST'])
def add_log():
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO logs (log_date, bus_id, category, description, cost) VALUES (?, ?, ?, ?, ?)",
            (data.get('date', datetime.date.today().isoformat()), data['bus_id'], data['category'], data['description'], float(data['cost']))
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- 8. API for Analytics Dashboard ---
@app.route('/get_analytics_data', methods=['GET'])
def get_analytics_data():
    try:
        conn = get_db_connection()
        # 1. Get Fuel Price Data
        fuel_data_db = conn.execute("SELECT month_year, price FROM fuel_prices ORDER BY month_year").fetchall()
        fuel_data = { "labels": [row['month_year'] for row in fuel_data_db], "data": [row['price'] for row in fuel_data_db] }
        # 2. Get Log Cost Breakdown Data
        log_data_db = conn.execute("SELECT category, SUM(cost) as total_cost FROM logs GROUP BY category").fetchall()
        log_data = { "labels": [row['category'] for row in log_data_db], "data": [row['total_cost'] for row in log_data_db] }
        conn.close()
        return jsonify({ "fuel_chart_data": fuel_data, "log_chart_data": log_data })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 9. Run the Application ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)