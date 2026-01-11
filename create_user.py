# create_user.py
import sqlite3
import bcrypt
from datetime import datetime

def create_user(username, password, email, approved=True):
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Insert user
    c.execute("""INSERT INTO users 
                 (username, password, email, is_developer, approved, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (username, hashed.decode('utf-8'), email, 0, approved, 
               datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"✅ User '{username}' created successfully!")
# Example usage
#create_user( "adii", "a1b2c3@", "adii@company.com", approved=True )