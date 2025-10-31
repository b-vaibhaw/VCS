"""
Utility functions used across modules
"""
import sqlite3
from datetime import datetime
from pathlib import Path

def init_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    
    # Meetings table
    c.execute('''CREATE TABLE IF NOT EXISTS meetings
                 (id TEXT PRIMARY KEY,
                  title TEXT,
                  date TEXT,
                  host TEXT,
                  participants TEXT,
                  audio_path TEXT,
                  transcript_path TEXT,
                  summary_path TEXT,
                  pdf_path TEXT,
                  storage_type TEXT,
                  web_link TEXT,
                  google_notes TEXT,
                  created_at TEXT)''')
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY,
                  password TEXT,
                  email TEXT,
                  is_developer INTEGER,
                  approved INTEGER,
                  created_at TEXT)''')
    
    # Speaker mappings table
    c.execute('''CREATE TABLE IF NOT EXISTS speaker_mappings
                 (meeting_id TEXT,
                  speaker_label TEXT,
                  real_name TEXT,
                  PRIMARY KEY (meeting_id, speaker_label))''')
    
    # Audit logs table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  action TEXT,
                  meeting_id TEXT,
                  timestamp TEXT,
                  details TEXT)''')
    
    conn.commit()
    conn.close()

def format_timestamp_ms(seconds):
    """Format timestamp with milliseconds: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

def log_audit(username, action, meeting_id="", details=""):
    """Log user action to audit table"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("""INSERT INTO audit_logs 
                 (username, action, meeting_id, timestamp, details) 
                 VALUES (?, ?, ?, ?, ?)""",
              (username, action, meeting_id, datetime.now().isoformat(), details))
    conn.commit()
    conn.close()

def save_speaker_mapping(meeting_id, speaker_label, real_name):
    """Save speaker label to real name mapping"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO speaker_mappings 
                 (meeting_id, speaker_label, real_name) 
                 VALUES (?, ?, ?)""",
              (meeting_id, speaker_label, real_name))
    conn.commit()
    conn.close()

def get_speaker_mapping(meeting_id):
    """Retrieve speaker mapping for a meeting"""
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("SELECT speaker_label, real_name FROM speaker_mappings WHERE meeting_id=?", 
              (meeting_id,))
    mappings = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return mappings