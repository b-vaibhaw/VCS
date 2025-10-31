"""
Initialize MeetingInsight database with default schema
Creates all required tables and default admin account
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.utils import init_database
from modules.auth import init_user_db

def main():
    """Initialize database and create default accounts"""
    
    print("=" * 60)
    print("MeetingInsight Database Initialization")
    print("=" * 60)
    print()
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print(f"✅ Created data directory: {data_dir.absolute()}")
    
    # Initialize database tables
    print("\n📊 Initializing database tables...")
    init_database()
    print("✅ Created tables: meetings, users, speaker_mappings, audit_logs")
    
    # Initialize user database with admin account
    print("\n👤 Creating default admin account...")
    init_user_db()
    
    print("\n" + "=" * 60)
    print("✅ Database initialized successfully!")
    print("=" * 60)
    print()
    print("Default Admin Account:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  Email: aditya.dev@projectmail.com")
    print()
    print("⚠️  IMPORTANT: Change the default password immediately!")
    print()
    print("Next steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. Login with admin credentials")
    print("  3. Change password in settings")
    print("  4. Create additional user accounts")
    print()
    print("For complete setup, see: MANUAL_SETUP_CHECKLIST.md")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
