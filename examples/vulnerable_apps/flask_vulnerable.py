"""Intentionally Vulnerable Flask Application for PIC Testing

WARNING: This application contains intentional security vulnerabilities.
DO NOT deploy to production or expose to the internet.
Use ONLY for testing PIC in controlled environments.
"""

from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import time

app = Flask(__name__)

# Intentionally insecure database setup
DB_PATH = "test_data/vulnerable_app.db"


def init_db():
    """Initialize vulnerable database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT
        )
    """)
    
    # Insert test data
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, password, email)
        VALUES (1, 'admin', 'admin123', 'admin@example.com')
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, password, email)
        VALUES (2, 'user', 'password', 'user@example.com')
    """)
    
    conn.commit()
    conn.close()


@app.route('/')
def index():
    """Home page."""
    return """
    <h1>Vulnerable Test Application</h1>
    <p>This application is intentionally vulnerable for testing purposes.</p>
    <ul>
        <li><a href="/search?q=test">Search (SQL Injection)</a></li>
        <li><a href="/login">Login (Timing Attack)</a></li>
        <li><a href="/render?template=hello">Template Rendering (SSTI)</a></li>
        <li><a href="/slow">Slow Endpoint (Slowloris)</a></li>
    </ul>
    """


@app.route('/search')
def search():
    """Vulnerable search endpoint - SQL Injection.
    
    PIC should detect:
    - Unusual string patterns in query parameter
    - High entropy in SQL injection attempts
    - Abnormal database query patterns
    """
    query = request.args.get('q', '')
    
    # VULNERABILITY: SQL Injection
    # Directly interpolating user input into SQL query
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Intentionally vulnerable query
        sql = f"SELECT * FROM users WHERE username LIKE '%{query}%'"
        cursor.execute(sql)
        results = cursor.fetchall()
        
        return jsonify({
            "query": query,
            "results": [
                {"id": r[0], "username": r[1], "email": r[3]}
                for r in results
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Vulnerable login endpoint - Timing Attack.
    
    PIC should detect:
    - Unusual timing patterns in authentication
    - Spike in failed login attempts
    - Abnormal request patterns
    """
    if request.method == 'GET':
        return """
        <form method="POST">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
        """
    
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # VULNERABILITY: Timing Attack
    # Different execution times reveal information
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        # Simulate character-by-character comparison (timing leak)
        stored_password = result[0]
        for i, (c1, c2) in enumerate(zip(password, stored_password)):
            if c1 != c2:
                time.sleep(0.01 * i)  # Timing leak
                return jsonify({"success": False, "message": "Invalid credentials"}), 401
            time.sleep(0.01)  # Simulate processing time
        
        if len(password) == len(stored_password):
            return jsonify({"success": True, "message": "Login successful"})
    
    return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route('/render')
def render():
    """Vulnerable template rendering - SSTI.
    
    PIC should detect:
    - Unusual template patterns
    - Abnormal string complexity
    - Suspicious execution patterns
    """
    template = request.args.get('template', 'Hello, World!')
    
    # VULNERABILITY: Server-Side Template Injection
    # Directly rendering user input as template
    try:
        rendered = render_template_string(template)
        return rendered
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/slow')
def slow():
    """Slow endpoint for Slowloris testing.
    
    PIC should detect:
    - Abnormal execution duration
    - Resource exhaustion patterns
    - Unusual request timing
    """
    # Simulate slow processing
    delay = float(request.args.get('delay', '5'))
    
    # VULNERABILITY: No timeout protection
    # Can be used for slowloris-style attacks
    time.sleep(min(delay, 30))  # Cap at 30 seconds
    
    return jsonify({"message": "Slow response", "delay": delay})


@app.route('/upload', methods=['POST'])
def upload():
    """Vulnerable file upload endpoint.
    
    PIC should detect:
    - Unusual file sizes
    - Suspicious file patterns
    - Abnormal upload behavior
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # VULNERABILITY: No file validation
    # Accepts any file type and size
    filename = file.filename
    filepath = os.path.join("test_data/uploads", filename)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    
    return jsonify({"message": "File uploaded", "filename": filename})


@app.route('/eval')
def eval_endpoint():
    """Extremely vulnerable eval endpoint.
    
    PIC should detect:
    - Code injection patterns
    - Abnormal execution behavior
    - High-risk operations
    """
    code = request.args.get('code', '1+1')
    
    # VULNERABILITY: Direct code execution
    # Extremely dangerous - allows arbitrary code execution
    try:
        result = eval(code)
        return jsonify({"code": code, "result": str(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("="*60)
    print("VULNERABLE TEST APPLICATION")
    print("="*60)
    print("WARNING: This application is intentionally insecure!")
    print("DO NOT expose to the internet or use in production!")
    print("Use ONLY for testing PIC in controlled environments.")
    print("="*60)
    print()
    
    init_db()
    
    # Run on localhost only
    app.run(host='127.0.0.1', port=5000, debug=True)
