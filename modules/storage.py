"""
Audio storage handler - local, Google Drive, or temporary links
Supports multiple storage backends with fallback
"""
import os
from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_audio_storage(audio_path, storage_type):
    """
    Handle audio file storage based on user preference
    
    Args:
        audio_path: Path to local audio file
        storage_type: 'Local', 'Google Drive', or 'Temporary Link (ngrok)'
    
    Returns:
        str: Web link or local path to audio
    """
    logger.info(f"Handling audio storage: {storage_type}")
    
    if storage_type == "Local":
        return f"file://{Path(audio_path).absolute()}"
    elif storage_type == "Google Drive":
        return upload_to_google_drive(audio_path)
    elif storage_type == "Temporary Link (ngrok)":
        return create_ngrok_link(audio_path)
    else:
        logger.warning(f"Unknown storage type: {storage_type}, using local")
        return f"file://{Path(audio_path).absolute()}"

def upload_to_google_drive(audio_path):
    """
    Upload audio to Google Drive and return shareable link
    
    Requires:
    - Google Drive API enabled
    - OAuth credentials in tokens/google_drive_token.json
    """
    logger.info("Uploading to Google Drive...")
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Check if credentials exist
        creds_path = 'tokens/google_drive_token.json'
        if not os.path.exists(creds_path):
            logger.warning("Google Drive credentials not found. Using local storage.")
            return f"file://{Path(audio_path).absolute()}"
        
        # Load credentials
        creds = Credentials.from_authorized_user_file(creds_path)
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare file metadata
        file_metadata = {
            'name': os.path.basename(audio_path),
            'mimeType': 'audio/mpeg',
            'description': f'Meeting recording uploaded by MeetingInsight on {datetime.now().strftime("%Y-%m-%d")}'
        }
        
        # Upload file
        media = MediaFileUpload(
            audio_path,
            mimetype='audio/mpeg',
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()
        
        # Make file publicly accessible (optional)
        try:
            service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            logger.info("File made publicly accessible")
        except Exception as e:
            logger.warning(f"Could not set public permissions: {str(e)}")
        
        web_link = file.get('webViewLink') or file.get('webContentLink')
        logger.info(f"Upload successful: {web_link}")
        
        return web_link
    
    except ImportError:
        logger.error("Google API client not installed. Run: pip install google-api-python-client")
        return f"file://{Path(audio_path).absolute()}"
    except Exception as e:
        logger.error(f"Google Drive upload failed: {str(e)}")
        return f"file://{Path(audio_path).absolute()}"

def create_ngrok_link(audio_path):
    """
    Create temporary public link using ngrok
    
    Requires:
    - ngrok installed
    - NGROK_AUTH_TOKEN in .env
    """
    logger.info("Creating ngrok public link...")
    
    try:
        from pyngrok import ngrok
        from dotenv import load_dotenv
        import http.server
        import socketserver
        import threading
        
        load_dotenv()
        
        # Set ngrok auth token
        ngrok_token = os.getenv('NGROK_AUTH_TOKEN')
        if ngrok_token:
            ngrok.set_auth_token(ngrok_token)
        else:
            logger.warning("NGROK_AUTH_TOKEN not set. Free tier has limitations.")
        
        # Start simple HTTP server in background
        audio_dir = os.path.dirname(audio_path)
        os.chdir(audio_dir)
        
        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler
        
        # Suppress server logs
        class QuietHandler(Handler):
            def log_message(self, format, *args):
                pass
        
        httpd = socketserver.TCPServer(("", PORT), QuietHandler)
        
        # Start server in daemon thread
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        
        logger.info(f"HTTP server started on port {PORT}")
        
        # Create ngrok tunnel
        public_url = ngrok.connect(PORT, bind_tls=True)
        
        filename = os.path.basename(audio_path)
        full_url = f"{public_url}/{filename}"
        
        logger.info(f"ngrok link created: {full_url}")
        logger.warning("⚠️ This link will expire when the application stops!")
        
        return full_url
    
    except ImportError:
        logger.error("pyngrok not installed. Run: pip install pyngrok")
        return f"file://{Path(audio_path).absolute()}"
    except Exception as e:
        logger.error(f"ngrok link creation failed: {str(e)}")
        return f"file://{Path(audio_path).absolute()}"

def get_audio_link(meeting_id):
    """Retrieve audio link for a meeting from database"""
    import sqlite3
    
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("SELECT web_link, audio_path FROM meetings WHERE id=?", (meeting_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return result[0] or result[1]
    return None

def cleanup_old_audio_files(days=30):
    """
    Clean up audio files older than specified days
    Part of data retention policy
    """
    import time
    from datetime import datetime, timedelta
    
    audio_dir = Path("data")
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    
    for meeting_dir in audio_dir.glob("meeting_*"):
        if not meeting_dir.is_dir():
            continue
        
        # Check directory modification time
        dir_mtime = datetime.fromtimestamp(meeting_dir.stat().st_mtime)
        
        if dir_mtime < cutoff_date:
            try:
                shutil.rmtree(meeting_dir)
                deleted_count += 1
                logger.info(f"Deleted old meeting directory: {meeting_dir.name}")
            except Exception as e:
                logger.error(f"Failed to delete {meeting_dir.name}: {str(e)}")
    
    logger.info(f"Cleanup complete: {deleted_count} old meetings deleted")
    return deleted_count