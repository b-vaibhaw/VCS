"""
Create additional admin/developer accounts
Interactive script for adding new users
"""
import sqlite3
import bcrypt
from datetime import datetime
import getpass
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def create_admin():
    """Interactive admin user creation"""
    
    print("=" * 60)
    print("Create MeetingInsight Admin User")
    print("=" * 60)
    print()
    
    # Get username
    while True:
        username = input("Username: ").strip()
        if username:
            break
        print("❌ Username cannot be empty")
    
    # Check if user exists
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    
    if c.fetchone():
        print(f"❌ Error: User '{username}' already exists")
        conn.close()
        return
    
    # Get password
    while True:
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match. Try again.")
            continue
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            continue
        
        break
    
    # Get email
    while True:
        email = input("Email: ").strip()
        if email and '@' in email:
            break
        print("❌ Invalid email address")
    
    # Check if developer
    is_dev_input = input("Is developer account? (y/n): ").lower()
    is_developer = is_dev_input in ['y', 'yes']
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Insert user
    try:
        c.execute("""INSERT INTO users 
                     (username, password, email, is_developer, approved, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (username, hashed.decode('utf-8'), email, 
                   1 if is_developer else 0, 1, datetime.now().isoformat()))
        conn.commit()
        
        print()
        print("=" * 60)
        print("✅ User created successfully!")
        print("=" * 60)
        print()
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Developer: {'Yes' if is_developer else 'No'}")
        print(f"  Approved: Yes")
        print()
        print("User can now login to MeetingInsight.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error creating user: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)