from flask import Flask, jsonify, request
import pyodbc
import json

app = Flask(__name__)

# --- 1. CONFIGURE YOUR DATABASE CONNECTION ---
# IMPORTANT: Check your 'server' name. 'localhost\SQLEXPRESS' is common,
# but it must exactly match your SQL Server instance name.
DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}', # Verify this driver is installed
    'server': 'localhost\SQLEXPRESS',
    'database': 'AdminDB',
    'trusted_connection': 'yes' # Uses the Windows login of the account running this Flask script
}

# Simple function to create the connection string
def get_connection_string():
    conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};"
    if 'trusted_connection' in DB_CONFIG:
        conn_str += f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    elif 'uid' in DB_CONFIG:
        # Fallback for SQL Server Authentication (not recommended if Windows Auth works)
        conn_str += f"UID={DB_CONFIG['uid']};PWD={DB_CONFIG['pwd']};"
    return conn_str

# --- 2. DEFINE THE API ENDPOINT ---
@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_readings():
    # API Key check (Matches the one in your Flutter ApiService.dart)
    api_key = request.args.get('api_key')
    REQUIRED_KEY = "FgO00DsmQB14oV5QCy6OCiqwYjXm_hivzi4Zu4PIkS0" 
    
    if api_key != REQUIRED_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = pyodbc.connect(get_connection_string())
        cursor = conn.cursor()
        
        # --- EXPLICIT QUERY TO FETCH ALL RECORDS (MAX 100K) ---
        # This is the most powerful SQL query to bypass hidden limits.
        # It orders by Id (newest first) and explicitly requests a large number of rows.
        sql_query = "SELECT * FROM SensorReadings3 ORDER BY Id DESC OFFSET 0 ROWS FETCH NEXT 100000 ROWS ONLY"
        cursor.execute(sql_query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Fetch all rows and map them to dictionaries
# Fetch all rows by iterating through the cursor (often safer for large/unlimited results)
        data = []
        for row in cursor:
            data.append(dict(zip(columns, row)))
        # --- DEBUG LINE: THIS IS THE CRITICAL INFORMATION ---
        print(f"\n[INFO] Flask retrieved {len(data)} records from SQL Server.")

        cursor.close()
        conn.close()
        
        # Send the complete JSON data back to Flutter
        return jsonify(data), 200

    except Exception as e:
        # Log the detailed error on the server side
        print(f"\n[ERROR] Database or Pyodbc error: {e}")
        # Send a generic error response to the client (Flutter)
        return jsonify({"error": "Failed to retrieve data"}), 500

# --- 3. RUN THE FLASK SERVER ---
if __name__ == '__main__':
    print("Starting Flask server on 127.0.0.1:8000")
    # Setting debug=True restarts the server automatically on code changes
    app.run(host='127.0.0.1', port=8000, debug=True)