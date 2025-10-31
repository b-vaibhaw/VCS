"""
Generate Google OAuth tokens for Drive, Docs, and Calendar APIs
Interactive OAuth flow with browser-based authentication
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Required scopes for MeetingInsight
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly',
]

def generate_tokens():
    """Generate and save Google OAuth tokens"""
    
    print("=" * 60)
    print("Google OAuth Token Generator")
    print("=" * 60)
    print()
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ Error: credentials.json not found!")
        print()
        print("Please follow these steps:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. Create a new project or select existing")
        print("  3. Enable the following APIs:")
        print("     - Google Drive API")
        print("     - Google Docs API")
        print("     - Google Calendar API")
        print("  4. Create OAuth 2.0 credentials (Desktop app)")
        print("  5. Download credentials as 'credentials.json'")
        print("  6. Place in project root directory")
        print()
        print("See MANUAL_SETUP_CHECKLIST.md for detailed instructions")
        return
    
    creds = None
    token_dir = Path('tokens')
    token_dir.mkdir(exist_ok=True)
    
    token_path = token_dir / 'google_tokens.json'
    
    # Check if token already exists
    if token_path.exists():
        print("📄 Found existing token file")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Refresh failed: {str(e)}")
                print("Starting new OAuth flow...")
                creds = None
        
        if not creds:
            print()
            print("🌐 Starting OAuth flow...")
            print("📌 A browser window will open")
            print("📌 Please authorize the application")
            print()
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    SCOPES
                )
                creds = flow.run_local_server(port=8080)
                print("\n✅ Authorization successful!")
            except Exception as e:
                print(f"\n❌ OAuth flow failed: {str(e)}")
                return
        
        # Save the credentials
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print(f"💾 Tokens saved to: {token_path}")
    else:
        print("✅ Valid tokens already exist")
    
    # Create copies for different services
    drive_token = token_dir / 'google_drive_token.json'
    docs_token = token_dir / 'google_docs_token.json'
    calendar_token = token_dir / 'google_calendar_token.json'
    
    for service_token in [drive_token, docs_token, calendar_token]:
        with open(service_token, 'w') as f:
            f.write(creds.to_json())
    
    print()
    print("=" * 60)
    print("✅ Google OAuth setup complete!")
    print("=" * 60)
    print()
    print("You can now:")
    print("  ✅ Upload audio to Google Drive")
    print("  ✅ Fetch Google Meet notes")
    print("  ✅ Access Calendar participant lists")
    print()
    print("Token files created:")
    print(f"  - {token_path}")
    print(f"  - {drive_token}")
    print(f"  - {docs_token}")
    print(f"  - {calendar_token}")
    print()

if __name__ == '__main__':
    try:
        generate_tokens()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)