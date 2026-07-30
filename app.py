import os
import random
import string
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)

# SECURITY CONFIGURATION
app.secret_key = 'super_secret_session_key_change_me_if_you_want'
ADMIN_USERNAME = "hellhell1a"
ADMIN_PASSWORD = "ajepkako"

DATABASE_FILE = 'links.db'

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, short_code TEXT UNIQUE, long_url TEXT, clicks INTEGER)''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# 1. LOGIN PAGE TEMPLATE
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="monetag" content="0027698ee828f90192299fe2c7f97d5f">
    <title>Admin Login</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; text-align: center; margin-top: 100px; background: #1a1a2e; color: #fff; }
        .login-box { max-width: 400px; margin: 0 auto; background: #162447; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.3); }
        h2 { color: #e43f5a; }
        input { width: 90%; padding: 12px; margin: 10px 0; border: none; border-radius: 6px; background: #1f4068; color: #fff; font-size: 16px; }
        button { width: 95%; padding: 12px; background: #e43f5a; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { background: #b93246; }
        .error { color: #ff4757; margin-bottom: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Private Link Manager Login</h2>
        {% if error %} <div class="error">{{ error }}</div> {% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Log In</button>
        </form>
    </div>
</body>
</html>
"""

# 2. PRIVATE DASHBOARD TEMPLATE
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Private Link Manager</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; text-align: center; margin-top: 50px; background: #1a1a2e; color: #fff; }
        .container { max-width: 500px; margin: 0 auto; background: #162447; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.3); }
        h2 { color: #e43f5a; margin-bottom: 20px; }
        input[type="url"] { width: 90%; padding: 12px; margin: 15px 0; border: none; border-radius: 6px; background: #1f4068; color: #fff; font-size: 16px; }
        button { width: 95%; padding: 12px; background: #e43f5a; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { background: #b93246; }
        .result { margin-top: 25px; font-weight: bold; background: #1f4068; padding: 15px; border-radius: 6px; border: 1px solid #e43f5a; word-break: break-all; }
        a { color: #00fff0; text-decoration: none; }
        .logout { display: block; margin-top: 20px; color: #bbb; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Private Link Shortener</h2>
        <p>Logged in as: <strong>hellhell1a</strong></p>
        <form method="POST" action="/generate-short-link">
            <input type="url" name="long_url" placeholder="Paste target long URL here..." required>
            <br>
            <button type="submit">Shorten URL</button>
        </form>
        {% if short_url %}
        <div class="result">
            <strong>Your Short Link:</strong><br>
            <a href="{{ short_url }}" target="_blank">{{ short_url }}</a>
        </div>
        {% endif %}
        <a href="/logout" class="logout">Logout</a>
    </div>
</body>
</html>
"""

# 3. INTERSTITIAL AD PAGE TEMPLATE (For your link clickers)
AD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Link is Loading...</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 80px; background: #f4f6f9; color: #333; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .timer-text { font-size: 20px; font-weight: bold; margin-bottom: 20px; }
        .countdown { color: #ff4757; font-size: 24px; }
        .ad-space { width: 300px; height: 250px; background: #eaeaea; margin: 20px auto; padding: 15px; border: 2px dashed #bbb; font-weight: bold; }
        .btn { padding: 14px 28px; font-size: 18px; color: white; background: #2ed573; border: none; border-radius: 6px; cursor: not-allowed; opacity: 0.5; font-weight: bold; }
        .btn.active { cursor: pointer; opacity: 1; background: #26af5f; }
    </style>
</head>
<body>
    <div class="container">
        <div class="timer-text">Your link is unlocking in <span id="timer" class="countdown">10</span> seconds...</div>
        
        <div class="ad-space">
            <h3>Test Advertisement</h3>
            <p>Clicking this keeps the site active.</p>
            <a href="https://google.com" target="_blank" style="color: blue; text-decoration: underline;">Visit Sponsor</a>
        </div>

        <br>
        <button id="skip-btn" class="btn" disabled onclick="window.location.href='/redirect/{{ code }}'">Please Wait...</button>
    </div>

    <script>
        let secondsLeft = 10;
        const timerDisplay = document.getElementById('timer');
        const actionButton = document.getElementById('skip-btn');

        const countdownInterval = setInterval(() => {
            secondsLeft--;
            timerDisplay.textContent = secondsLeft;
            
            if (secondsLeft <= 0) {
                clearInterval(countdownInterval);
                timerDisplay.parentElement.innerHTML = "Your link is ready!";
                actionButton.disabled = false;
                actionButton.classList.add('active');
                actionButton.textContent = "Skip Ad & Continue";
            }
        }, 1000);
    </script>
</body>
</html>
"""

# ROUTING LOGIC

@app.route('/')
def home():
    if 'logged_in' in session:
        return render_template_string(DASHBOARD_HTML)
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template_string(LOGIN_HTML, error="Invalid username or password.")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/generate-short-link', methods=['POST'])
def shorten():
    if 'logged_in' not in session:
        return redirect(url_for('home'))
        
    long_url = request.form['long_url']
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO urls (short_code, long_url, clicks) VALUES (?, ?, ?)', (code, long_url, 0))
    conn.commit()
    conn.close()
    
    short_url = request.host_url + code
    return render_template_string(DASHBOARD_HTML, short_url=short_url)

@app.route('/<code>')
def ad_page(code):
    if code == 'favicon.ico':
        return '', 204
        
    conn = get_db_connection()
    url_entry = conn.execute('SELECT * FROM urls WHERE short_code = ?', (code,)).fetchone()
    conn.close()
    
    if url_entry:
        return render_template_string(AD_HTML, code=code)
    return "Invalid Link Address", 404

@app.route('/redirect/<code>')
def final_redirect(code):
    conn = get_db_connection()
    url_entry = conn.execute('SELECT * FROM urls WHERE short_code = ?', (code,)).fetchone()
    
    if url_entry:
        conn.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', (code,))
        conn.commit()
        conn.close()
        return redirect(url_entry['long_url'])
        
    conn.close()
    return "Invalid Target Link", 404

init_db()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    
