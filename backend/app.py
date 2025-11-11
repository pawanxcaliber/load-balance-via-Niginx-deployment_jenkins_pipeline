import os
import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Configurable DB Path ---
DB_FILE = os.getenv("DATABASE_PATH", "/data/names.db")

app = Flask(__name__)
CORS(app)

# --- Database Initialization ---
def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- API Endpoints ---
@app.route('/store', methods=['POST'])
def store_name():
    try:
        data = request.get_json()
        name = data['name']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO names (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return jsonify({'message': f'Name {name} stored successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/names', methods=['GET'])
def get_names():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM names")
    names = cursor.fetchall()
    conn.close()
    return jsonify(names), 200

def run_init_db():
    init_db()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
