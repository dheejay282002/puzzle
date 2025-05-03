from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('puzzle_royale.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_photo TEXT,
        level INTEGER DEFAULT 1
    )''')
    conn.commit()
    conn.close()

def generate_user_id(username):
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{username}_{suffix}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        profile_photo = request.files['profile_photo']

        if not name or not username or not password or not profile_photo:
            flash('Please fill in all fields.')
            return redirect(url_for('register'))

        filename = secure_filename(profile_photo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_photo.save(filepath)

        hashed_password = generate_password_hash(password)
        user_id = generate_user_id(username)

        conn = sqlite3.connect('puzzle_royale.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (user_id, name, username, password, profile_photo) VALUES (?, ?, ?, ?, ?)',
                      (user_id, name, username, hashed_password, filename))
            conn.commit()
            flash(f'Registration successful! Your User ID is {user_id}. You can now log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
            return redirect(url_for('register'))
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('puzzle_royale.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[4], password):
            session['user_id'] = user[1]
            session['username'] = user[3]
            session['name'] = user[2]
            session['profile_photo'] = user[5]
            session['level'] = user[6]
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
