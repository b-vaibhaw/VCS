"""
Authentication and user management module
"""
import sqlite3
import bcrypt
from datetime import datetime
from pathlib import Path

def init_user_db():
    """Initialize user database with developer account"""
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY,
                  password TEXT,
                  email TEXT,
                  is_developer INTEGER,
                  approved INTEGER,
                  created_at TEXT)''')
    
    # Check if developer account exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        # Create default developer account
        # Password: admin123 (CHANGE THIS IN PRODUCTION)
        hashed = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        c.execute("""INSERT INTO users 
                     (username, password, email, is_developer, approved, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  ('admin', hashed.decode('utf-8'), 'aditya.dev@projectmail.com', 
                   1, 1, datetime.now().isoformat()))
        conn.commit()
    
    conn.close()

def authenticate_user(username, password):
    """Authenticate user credentials"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("SELECT password, approved, is_developer FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return {'success': False, 'message': '❌ User not found'}
    
    stored_password, approved, is_developer = result
    
    if not approved:
        return {'success': False, 'message': '⏳ Account pending approval. Contact aditya.dev@projectmail.com'}
    
    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        return {'success': True, 'is_developer': bool(is_developer)}
    else:
        return {'success': False, 'message': '❌ Incorrect password'}

def check_if_approved(username):
    """Check if user is approved"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("SELECT approved FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def register_user(username, password, email):
    """Register new user (pending approval)"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return {'success': False, 'message': 'Username already exists'}
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        c.execute("""INSERT INTO users 
                     (username, password, email, is_developer, approved, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (username, hashed.decode('utf-8'), email, 0, 0, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return {'success': True, 'message': 'Registration successful. Awaiting approval.'}
    except Exception as e:
        conn.close()
        return {'success': False, 'message': f'Registration failed: {str(e)}'}
