"""
Platform integrations for Google Meet, Zoom, Microsoft Teams
Includes participant list fetching and Google Docs notes retrieval
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== GOOGLE MEET INTEGRATION ====================

def fetch_google_notes(meeting_title):
    """
    Fetch Google Meet notes from Google Docs
    
    Process:
    1. Search Google Drive for document matching meeting title
    2. Retrieve document content via Docs API
    3. Extract and format text
    
    Requires:
    - Google Docs API enabled
    - OAuth tokens in tokens/google_docs_token.json
    """
    logger.info(f"Fetching Google notes for: {meeting_title}")
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from dotenv import load_dotenv
        
        load_dotenv()
        
        creds_path = 'tokens/google_docs_token.json'
        if not os.path.exists(creds_path):
            logger.warning("Google Docs credentials not configured")
            return "Google Docs integration not configured. See MANUAL_SETUP_CHECKLIST.md"
        
        # Load credentials
        creds = Credentials.from_authorized_user_file(creds_path)
        
        # Build services
        drive_service = build('drive', 'v3', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        
        # Search Drive for document with meeting title
        query = f"name contains '{meeting_title}' and mimeType='application/vnd.google-apps.document'"
        results = drive_service.files().list(
            q=query,
            pageSize=10,
            fields="files(id, name, createdTime, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            logger.info("No Google Docs notes found for this meeting")
            return "No Google Docs notes found for this meeting."
        
        # Get content from first (most recent) matching document
        doc_id = files[0]['id']
        doc_name = files[0]['name']
        
        logger.info(f"Found Google Doc: {doc_name} (ID: {doc_id})")
        
        # Retrieve document content
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        # Extract text content
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_run in element['paragraph'].get('elements', []):
                    if 'textRun' in text_run:
                        text = text_run['textRun'].get('content', '')
                        if text.strip():
                            content.append(text)
        
        full_content = ''.join(content)
        
        logger.info(f"Retrieved {len(full_content)} characters from Google Doc")
        return full_content
        
    except ImportError:
        logger.error("Google API client not installed")
        return "Google API client not installed. Run: pip install google-api-python-client"
    except Exception as e:
        logger.error(f"Error fetching Google notes: {str(e)}")
        return f"Error fetching Google notes: {str(e)}"

def get_meeting_participants(meeting_title, default_participants):
    """
    Attempt to retrieve participant list from meeting platform
    
    Priority order:
    1. Google Calendar API (attendees from calendar event)
    2. Zoom API (meeting participants)
    3. Microsoft Teams API
    4. Manual parsing from default_participants string
    
    Returns:
        dict: Mapping of speaker labels to real names
        Example: {'SPEAKER_0': 'Alice Smith', 'SPEAKER_1': 'Bob Jones'}
    """
    logger.info("Attempting to retrieve meeting participants")
    
    # Try Google Calendar first
    participants = get_google_calendar_participants(meeting_title)
    if participants:
        logger.info(f"Retrieved {len(participants)} participants from Google Calendar")
        return participants
    
    # Try Zoom API
    participants = get_zoom_participants(meeting_title)
    if participants:
        logger.info(f"Retrieved {len(participants)} participants from Zoom")
        return participants
    
    # Try Teams API
    participants = get_teams_participants(meeting_title)
    if participants:
        logger.info(f"Retrieved {len(participants)} participants from Teams")
        return participants
    
    # Fallback: parse from default_participants string
    if default_participants:
        logger.info("Using manually provided participant list")
        names = [name.strip() for name in default_participants.split(',')]
        mapping = {}
        for i, name in enumerate(names):
            mapping[f"SPEAKER_{i}"] = name
        return mapping
    
    logger.warning("No participant metadata available")
    return {}

def get_google_calendar_participants(meeting_title):
    """
    Fetch participant list from Google Calendar event
    
    Process:
    1. Search calendar for events matching title
    2. Extract attendee list from event
    3. Map to speaker labels
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds_path = 'tokens/google_calendar_token.json'
        if not os.path.exists(creds_path):
            return None
        
        creds = Credentials.from_authorized_user_file(creds_path)
        service = build('calendar', 'v3', credentials=creds)
        
        # Search for event by title (past week to tomorrow)
        now = datetime.utcnow()
        time_min = (now - timedelta(days=7)).isoformat() + 'Z'
        time_max = (now + timedelta(days=1)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            q=meeting_title,
            singleEvents=True,
            orderBy='startTime',
            maxResults=10
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            logger.info("No matching calendar events found")
            return None
        
        # Use first matching event
        event = events[0]
        attendees = event.get('attendees', [])
        
        if not attendees:
            logger.info("No attendees found in calendar event")
            return None
        
        # Map attendees to speaker labels
        mapping = {}
        for i, attendee in enumerate(attendees):
            # Try to get display name, fall back to email username
            name = attendee.get('displayName')
            if not name:
                email = attendee.get('email', '')
                name = email.split('@')[0].replace('.', ' ').title()
            
            mapping[f"SPEAKER_{i}"] = name
        
        logger.info(f"Mapped {len(mapping)} attendees from Google Calendar")
        return mapping
        
    except Exception as e:
        logger.error(f"Error fetching Google Calendar participants: {str(e)}")
        return None

def get_zoom_participants(meeting_id):
    """
    Fetch participants from Zoom API
    
    Requires:
    - Zoom OAuth app setup
    - Server-to-Server OAuth credentials
    - Access token in environment
    
    API: https://marketplace.zoom.us/docs/api-reference/zoom-api/methods/#operation/pastMeetingParticipants
    """
    try:
        import requests
        from dotenv import load_dotenv
        
        load_dotenv()
        
        zoom_access_token = os.getenv('ZOOM_ACCESS_TOKEN')
        if not zoom_access_token:
            logger.info("Zoom access token not configured")
            return None
        
        # Extract meeting ID from title or use provided ID
        # Format: xxx-xxxx-xxxx or xxxxxxxxxx
        if not meeting_id.replace('-', '').isdigit():
            logger.warning("Invalid Zoom meeting ID format")
            return None
        
        # API endpoint
        url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/participants"
        
        headers = {
            'Authorization': f'Bearer {zoom_access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            participants = data.get('participants', [])
            
            mapping = {}
            for i, participant in enumerate(participants):
                name = participant.get('name', f'Participant {i+1}')
                mapping[f"SPEAKER_{i}"] = name
            
            logger.info(f"Retrieved {len(mapping)} participants from Zoom")
            return mapping
        else:
            logger.error(f"Zoom API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Zoom participants: {str(e)}")
        return None

def get_teams_participants(meeting_id):
    """
    Fetch participants from Microsoft Teams via Graph API
    
    Requires:
    - Microsoft Graph API app registration
    - Calendar.Read, OnlineMeetings.Read permissions
    - Access token
    
    API: https://docs.microsoft.com/en-us/graph/api/onlinemeeting-get
    """
    try:
        import requests
        from dotenv import load_dotenv
        
        load_dotenv()
        
        teams_access_token = os.getenv('TEAMS_ACCESS_TOKEN')
        if not teams_access_token:
            logger.info("Teams access token not configured")
            return None
        
        # API endpoint
        url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}"
        
        headers = {
            'Authorization': f'Bearer {teams_access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            participants = data.get('participants', {}).get('attendees', [])
            
            mapping = {}
            for i, participant in enumerate(participants):
                identity = participant.get('identity', {})
                name = identity.get('displayName', f'Participant {i+1}')
                mapping[f"SPEAKER_{i}"] = name
            
            logger.info(f"Retrieved {len(mapping)} participants from Teams")
            return mapping
        else:
            logger.error(f"Teams API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Teams participants: {str(e)}")
        return None

# ==================== PUPPETEER BOT INTEGRATION ====================

def check_bot_capture_data(meeting_id):
    """
    Check if Puppeteer bot has captured participant data
    Bot stores data in data/bot_captures/
    """
    bot_data_dir = Path("data/bot_captures")
    
    if not bot_data_dir.exists():
        return None
    
    # Look for participant JSON file
    participant_file = bot_data_dir / f"{meeting_id}_participants.json"
    
    if participant_file.exists():
        try:
            with open(participant_file, 'r') as f:
                participants = json.load(f)
            
            # Map to speaker labels
            mapping = {}
            for i, name in enumerate(participants):
                mapping[f"SPEAKER_{i}"] = name
            
            logger.info(f"Loaded {len(mapping)} participants from bot capture")
            return mapping
        except Exception as e:
            logger.error(f"Error loading bot capture data: {str(e)}")
    
    return None

def get_bot_audio_file(meeting_id):
    """
    Check if bot captured audio file
    """
    bot_data_dir = Path("data/bot_captures")
    
    if not bot_data_dir.exists():
        return None
    
    # Look for audio file
    audio_file = bot_data_dir / f"{meeting_id}_audio.mp3"
    
    if audio_file.exists():
        logger.info(f"Found bot-captured audio: {audio_file}")
        return str(audio_file)
    
    return None

def get_bot_captions(meeting_id):
    """
    Retrieve live captions captured by bot
    Can be used as fallback or comparison with Whisper
    """
    bot_data_dir = Path("data/bot_captures")
    
    if not bot_data_dir.exists():
        return None
    
    captions_file = bot_data_dir / f"{meeting_id}_captions.json"
    
    if captions_file.exists():
        try:
            captions = []
            with open(captions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        captions.append(json.loads(line))
            
            logger.info(f"Loaded {len(captions)} caption entries from bot")
            return captions
        except Exception as e:
            logger.error(f"Error loading bot captions: {str(e)}")
    
    return None

# ==================== OAUTH TOKEN MANAGEMENT ====================

def refresh_google_token(token_path):
    """
    Refresh expired Google OAuth token
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        
        if not os.path.exists(token_path):
            logger.error(f"Token file not found: {token_path}")
            return False
        
        creds = Credentials.from_authorized_user_file(token_path)
        
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google token...")
            creds.refresh(Request())
            
            # Save refreshed token
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            logger.info("Token refreshed successfully")
            return True
        
        return True
        
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        return False

def validate_oauth_tokens():
    """
    Validate all OAuth tokens and refresh if needed
    """
    token_dir = Path("tokens")
    
    if not token_dir.exists():
        return False
    
    tokens_valid = True
    
    for token_file in token_dir.glob("*.json"):
        if not refresh_google_token(str(token_file)):
            tokens_valid = False
            logger.warning(f"Invalid token: {token_file.name}")
    
    return tokens_valid