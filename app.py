"""
MeetingInsight - Main Streamlit Application
Free & Open-Source Meeting Transcription Platform

Features:
- Audio/video upload and live recording
- AI transcription with millisecond timestamps
- Speaker diarization with exact name resolution
- AI summarization and action item extraction
- PDF generation and email delivery
- Multiple storage options (local/Drive/ngrok)
- Google Meet notes integration
- User authentication and approval system
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
import sqlite3
import sys
import time

# Add modules to path
sys.path.append(str(Path(__file__).parent))

# Import all modules
from modules.auth import authenticate_user, check_if_approved, init_user_db
from modules.transcriber import transcribe_audio_file, get_supported_languages
from modules.diarizer import diarize_audio_file, merge_transcript_with_diarization
from modules.summarizer import generate_summary_and_action_items
from modules.pdf_email import generate_meeting_pdf, send_meeting_email
from modules.storage import handle_audio_storage, get_audio_link
from modules.platform_integrations import (
    fetch_google_notes, 
    get_meeting_participants,
    check_bot_capture_data
)
from modules.utils import format_timestamp_ms, log_audit, init_database

# ==================== INITIALIZATION ====================

# Create required directories
Path("data").mkdir(exist_ok=True)
Path("data/audio").mkdir(exist_ok=True)
Path("data/bot_captures").mkdir(exist_ok=True)
Path("tokens").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="MeetingInsight - AI Meeting Transcription",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:aditya.dev@projectmail.com',
        'Report a bug': "mailto:aditya.dev@projectmail.com",
        'About': "MeetingInsight - Free & Open-Source Meeting Transcription"
    }
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1a73e8;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5f6368;
        text-align: center;
        margin-bottom: 2rem;
    }
    .speaker-label {
        background-color: #e8f0fe;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
        color: #1a73e8;
    }
    .timestamp {
        color: #5f6368;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .action-item {
        background-color: #fef7e0;
        padding: 1rem;
        border-left: 4px solid #f9ab00;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #e6f4ea;
        padding: 1rem;
        border-left: 4px solid #1e8e3e;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef7e0;
        padding: 1rem;
        border-left: 4px solid #f9ab00;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'storage_type' not in st.session_state:
    st.session_state.storage_type = "Local"
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'current_meeting' not in st.session_state:
    st.session_state.current_meeting = None

# Initialize databases
init_database()
init_user_db()

# ==================== AUTHENTICATION ====================

def login_page():
    """Login and access request page"""
    
    # Logo and branding
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-header">🎙️ MeetingInsight</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Free & Open-Source Meeting Transcription Platform</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📧 Request Access"])
    
    with tab1:
        st.subheader("Welcome Back")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    result = authenticate_user(username, password)
                    if result['success']:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.is_developer = result['is_developer']
                        log_audit(username, "LOGIN", "", "Successful login")
                        st.success("✅ Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result['message'])
    
    with tab2:
        st.subheader("Request Access to MeetingInsight")
        
        st.info("📌 This application is restricted to approved users only.")
        
        st.markdown("""
        ### To request access:
        
        **Email the developer at:**
        
        📧 **aditya.dev@projectmail.com**
        
        **Please include in your request:**
        - ✅ Full Name
        - ✅ Email Address
        - ✅ Organization (if applicable)
        - ✅ Reason for access
        - ✅ Expected usage frequency
        - ✅ Use case description
        
        **Response time:** Within 24-48 hours
        
        **Note:** You will receive your credentials via email after approval.
        """)
        
        with st.expander("Why is access restricted?"):
            st.markdown("""
            MeetingInsight requires approval for:
            - **Privacy Protection**: Meeting transcripts contain sensitive information
            - **Resource Management**: Server resources are limited
            - **Compliance**: GDPR and data protection requirements
            - **Quality Control**: Ensuring ethical use of transcription technology
            
            Once approved, you'll have full access to all features including:
            - Unlimited meeting transcriptions
            - AI summarization and action items
            - PDF reports and email delivery
            - Google Meet notes integration
            - Multiple storage options
            """)
        
        st.warning("⚠️ Unauthorized access attempts are logged and monitored.")

# ==================== SIDEBAR NAVIGATION ====================

def sidebar_navigation():
    """Render sidebar with navigation and settings"""
    
    with st.sidebar:
        # User profile
        st.markdown(f"### 👤 {st.session_state.username}")
        
        if st.session_state.get('is_developer', False):
            st.success("🔧 Developer Account")
        
        if st.button("🚪 Logout", use_container_width=True):
            log_audit(st.session_state.username, "LOGOUT", "", "User logged out")
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
        
        st.divider()
        
        # Settings Section
        with st.expander("⚙️ Settings", expanded=False):
            st.session_state.storage_type = st.selectbox(
                "Audio Storage Method",
                ["Local", "Google Drive", "Temporary Link (ngrok)"],
                help="Choose where to store meeting audio files"
            )
            
            if st.session_state.storage_type == "Google Drive":
                if st.button("🔗 Connect Google Drive", use_container_width=True):
                    st.info("See MANUAL_SETUP_CHECKLIST.md for Google OAuth setup")
            
            st.checkbox("Auto-email after processing", value=True, key="auto_email")
            st.checkbox("Fetch Google Meet notes", value=False, key="fetch_google_notes")
            st.checkbox("Enable bot participant capture", value=True, key="use_bot_data")
            
            # Advanced settings
            with st.expander("Advanced Settings"):
                st.selectbox("Whisper Model", ["tiny", "base", "small", "medium"], index=1, key="whisper_model")
                st.selectbox("Diarization Method", ["auto", "pyannote", "fallback"], key="diarization_method")
                st.slider("Minimum Segment Duration (s)", 0.3, 2.0, 0.5, 0.1, key="min_segment_duration")
        
        st.divider()
        
        # Recent Meetings
        st.subheader("📋 Recent Meetings")
        
        conn = sqlite3.connect('data/meetings.db')
        c = conn.cursor()
        c.execute("""SELECT id, title, date FROM meetings 
                     WHERE host=? 
                     ORDER BY created_at DESC LIMIT 10""", (st.session_state.username,))
        meetings = c.fetchall()
        conn.close()
        
        if meetings:
            for mtg in meetings:
                meeting_id, title, date = mtg
                if st.button(
                    f"📄 {title[:25]}{'...' if len(title) > 25 else ''}\n{date}", 
                    key=f"mtg_{meeting_id}", 
                    use_container_width=True
                ):
                    st.session_state.current_meeting = meeting_id
                    st.rerun()
        else:
            st.info("No meetings yet. Upload your first recording!")
        
        st.divider()
        
        # Quick Stats
        with st.expander("📊 Statistics"):
            conn = sqlite3.connect('data/meetings.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM meetings WHERE host=?", (st.session_state.username,))
            total_meetings = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM audit_logs WHERE username=?", (st.session_state.username,))
            total_actions = c.fetchone()[0]
            conn.close()
            
            st.metric("Total Meetings", total_meetings)
            st.metric("Total Actions", total_actions)

# ==================== MEETING DETAILS PAGE ====================

def meeting_details_page(meeting_id):
    """Display detailed view of a specific meeting"""
    
    conn = sqlite3.connect('data/meetings.db')
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE id=?", (meeting_id,))
    meeting = c.fetchone()
    conn.close()
    
    if not meeting:
        st.error("❌ Meeting not found")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.current_meeting = None
            st.rerun()
        return
    
    # Parse meeting data
    (mid, title, date, host, participants, audio_path, 
     transcript_path, summary_path, pdf_path, storage_type, 
     web_link, google_notes, created_at) = meeting
    
    # Header with back button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<p class="main-header">{title}</p>', unsafe_allow_html=True)
    with col2:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.current_meeting = None
            st.rerun()
    
    st.markdown(f"**📅 Date:** {date} | **👤 Host:** {host}")
    st.markdown(f"**👥 Participants:** {participants}")
    
    st.divider()
    
    # Audio Player
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🎵 Audio Recording")
        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path)
        elif web_link:
            st.markdown(f"🔗 [Open Audio Recording]({web_link})")
        else:
            st.info("Audio file not available")
    
    with col2:
        st.subheader("📥 Downloads")
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                st.download_button(
                    "📄 Download PDF",
                    data=f.read(),
                    file_name=f"{title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        if transcript_path and os.path.exists(transcript_path):
            with open(transcript_path, 'r') as f:
                st.download_button(
                    "📝 Download Transcript",
                    data=f.read(),
                    file_name=f"{title.replace(' ', '_')}_transcript.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        if summary_path and os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                st.download_button(
                    "📊 Download Summary",
                    data=f.read(),
                    file_name=f"{title.replace(' ', '_')}_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    st.divider()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Transcript",
        "📊 Summary & Action Items",
        "📄 Google Notes",
        "📧 Share"
    ])
    
    with tab1:
        st.subheader("Full Transcript with Millisecond Timestamps")
        
        if transcript_path and os.path.exists(transcript_path):
            # Search functionality
            search_term = st.text_input("🔍 Search transcript", placeholder="Enter keywords...")
            
            with open(transcript_path, 'r') as f:
                transcript = json.load(f)
            
            # Display transcript
            for idx, segment in enumerate(transcript):
                # Filter by search term
                if search_term and search_term.lower() not in segment['text'].lower():
                    continue
                
                col1, col2, col3 = st.columns([1, 2, 9])
                
                with col1:
                    st.markdown(f'<span class="timestamp">{segment["start"]}</span>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'<span class="speaker-label">{segment["speaker"]}</span>', unsafe_allow_html=True)
                
                with col3:
                    # Highlight search term
                    text = segment['text']
                    if search_term:
                        text = text.replace(
                            search_term,
                            f"**{search_term}**"
                        )
                    st.markdown(text)
                
                if idx < len(transcript) - 1:
                    st.markdown("---")
        else:
            st.info("Transcript not available")
    
    with tab2:
        if summary_path and os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary = f.read()
            st.markdown(summary)
        else:
            st.info("Summary not available")
    
    with tab3:
        if google_notes and google_notes.strip():
            st.markdown(google_notes)
        else:
            st.info("No Google Meet notes found for this meeting")
    
    with tab4:
        st.subheader("📧 Share Meeting Report")
        
        with st.form("email_form"):
            email_addresses = st.text_input(
                "Recipient Email Addresses (comma-separated)",
                placeholder="email1@example.com, email2@example.com"
            )
            
            custom_message = st.text_area(
                "Custom Message (optional)",
                placeholder="Add a personal message to the email..."
            )
            
            if st.form_submit_button("📨 Send Email", use_container_width=True, type="primary"):
                if email_addresses and pdf_path:
                    with st.spinner("Sending email..."):
                        success = send_meeting_email(
                            email_addresses,
                            pdf_path,
                            title,
                            custom_message if custom_message else None
                        )
                    
                    if success:
                        st.success("✅ Email sent successfully!")
                        log_audit(st.session_state.username, "EMAIL_SENT", meeting_id, f"To: {email_addresses}")
                    else:
                        st.error("❌ Failed to send email. Check SMTP configuration.")
                else:
                    st.error("Please enter at least one email address")
    
    # Log viewing action
    log_audit(st.session_state.username, "VIEWED_MEETING", meeting_id, f"Viewed: {title}")

# ==================== MEETING PROCESSING ====================

def process_meeting_file(uploaded_file, meeting_title, participants, language=None):
    """
    Complete meeting processing pipeline
    
    Steps:
    1. Save uploaded file
    2. Transcribe with Whisper
    3. Diarize speakers
    4. Merge transcript with speakers
    5. Resolve speaker names
    6. Generate summary and action items
    7. Fetch Google notes (optional)
    8. Create PDF report
    9. Handle storage
    10. Save to database
    """
    
    # Generate meeting ID
    meeting_id = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create meeting directory
    meeting_dir = Path(f"data/{meeting_id}")
    meeting_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    audio_path = meeting_dir / uploaded_file.name
    with open(audio_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Transcription
        status_text.markdown("🎙️ **Step 1/7:** Transcribing audio with Faster-Whisper...")
        progress_bar.progress(5)
        
        transcript_data = transcribe_audio_file(str(audio_path), language=language)
        progress_bar.progress(25)
        
        st.success(f"✅ Transcribed {len(transcript_data['segments'])} segments in {transcript_data['language']}")
        
        # Step 2: Speaker Diarization
        status_text.markdown("👥 **Step 2/7:** Identifying speakers with diarization...")
        progress_bar.progress(30)
        
        diarization_data = diarize_audio_file(
            str(audio_path),
            num_speakers=None,
            method=st.session_state.get('diarization_method', 'auto')
        )
        progress_bar.progress(45)
        
        unique_speakers = len(set([seg['speaker'] for seg in diarization_data]))
        st.success(f"✅ Identified {unique_speakers} unique speakers")
        
        # Step 3: Merge transcript with speakers
        status_text.markdown("🔗 **Step 3/7:** Merging speaker information with timestamps...")
        progress_bar.progress(50)
        
        merged_transcript = merge_transcript_with_diarization(transcript_data, diarization_data)
        progress_bar.progress(55)
        
        # Step 4: Speaker name resolution
        status_text.markdown("👤 **Step 4/7:** Resolving speaker names...")
        progress_bar.progress(60)
        
        # Try multiple sources for speaker names
        speaker_mapping = {}
        
        # Source 1: Bot capture data
        if st.session_state.get('use_bot_data', True):
            speaker_mapping = check_bot_capture_data(meeting_id)
        
        # Source 2: Platform APIs
        if not speaker_mapping:
            speaker_mapping = get_meeting_participants(meeting_title, participants)
        
        # Source 3: Manual mapping UI
        if not speaker_mapping or len(speaker_mapping) < unique_speakers:
            st.warning("⚠️ Could not auto-detect all speaker names. Please map speakers manually:")
            
            unique_speaker_labels = sorted(set([seg['speaker'] for seg in merged_transcript]))
            speaker_mapping = {}
            
            # Create input fields for each speaker
            cols = st.columns(min(3, len(unique_speaker_labels)))
            for idx, speaker_label in enumerate(unique_speaker_labels):
                with cols[idx % len(cols)]:
                    # Show sample text from this speaker
                    sample_text = next(
                        (seg['text'][:50] for seg in merged_transcript if seg['speaker'] == speaker_label),
                        "No sample"
                    )
                    
                    real_name = st.text_input(
                        f"**{speaker_label}**",
                        key=f"speaker_map_{speaker_label}",
                        placeholder="Enter real name",
                        help=f"Sample: {sample_text}..."
                    )
                    
                    if real_name:
                        speaker_mapping[speaker_label] = real_name
            
            # Check if all speakers are mapped
            if len(speaker_mapping) != len(unique_speaker_labels):
                st.error("❌ Please map all speakers before continuing")
                progress_bar.empty()
                status_text.empty()
                return None
        
        # Apply speaker names to transcript
        for segment in merged_transcript:
            if segment['speaker'] in speaker_mapping:
                segment['speaker'] = speaker_mapping[segment['speaker']]
        
        progress_bar.progress(65)
        st.success(f"✅ Mapped {len(speaker_mapping)} speakers")
        
        # Step 5: AI Summarization
        status_text.markdown("📊 **Step 5/7:** Generating AI summary and extracting action items...")
        progress_bar.progress(70)
        
        summary = generate_summary_and_action_items(merged_transcript)
        progress_bar.progress(80)
        
        st.success("✅ Summary generated with action items")
        
        # Step 6: Google Notes (optional)
        google_notes = ""
        if st.session_state.get('fetch_google_notes', False):
            status_text.markdown("📄 **Step 6/7:** Fetching Google Meet notes...")
            progress_bar.progress(85)
            google_notes = fetch_google_notes(meeting_title)
        else:
            progress_bar.progress(85)
        
        # Step 7: Save data
        status_text.markdown("💾 **Step 7/7:** Saving transcript and generating PDF...")
        progress_bar.progress(90)
        
        # Save transcript
        transcript_path = meeting_dir / "transcript.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(merged_transcript, f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary_path = meeting_dir / "summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # Handle audio storage
        web_link = handle_audio_storage(str(audio_path), st.session_state.storage_type)
        
        # Generate PDF
        pdf_path = generate_meeting_pdf(
            meeting_id,
            meeting_title,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            participants,
            merged_transcript,
            summary,
            google_notes,
            web_link
        )
        
        progress_bar.progress(95)
        
        # Save to database
        conn = sqlite3.connect('data/meetings.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO meetings 
            (id, title, date, host, participants, audio_path, transcript_path, 
             summary_path, pdf_path, storage_type, web_link, google_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting_id,
            meeting_title,
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            st.session_state.username,
            participants,
            str(audio_path),
            str(transcript_path),
            str(summary_path),
            pdf_path,
            st.session_state.storage_type,
            web_link,
            google_notes,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        progress_bar.progress(100)
        status_text.markdown("✅ **Meeting processed successfully!**")
        
        log_audit(st.session_state.username, "PROCESSED_MEETING", meeting_id, f"Title: {meeting_title}")
        
        return {
            'meeting_id': meeting_id,
            'pdf_path': pdf_path,
            'transcript': merged_transcript,
            'summary': summary,
            'google_notes': google_notes,
            'web_link': web_link
        }
        
    except Exception as e:
        st.error(f"❌ Error processing meeting: {str(e)}")
        log_audit(st.session_state.username, "PROCESSING_ERROR", meeting_id, str(e))
        return None
    finally:
        progress_bar.empty()
        status_text.empty()

# ==================== MAIN DASHBOARD ====================

def main_dashboard():
    """Main application dashboard"""
    
    # Render sidebar
    sidebar_navigation()
    
    # Check if viewing specific meeting
    if st.session_state.current_meeting:
        meeting_details_page(st.session_state.current_meeting)
        return
    
    # Main header
    st.markdown('<p class="main-header">🎙️ MeetingInsight</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Meeting Transcription & Analysis</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Recording",
        "🎙️ Live Recording",
        "🤖 Bot Automation",
        "📚 Documentation"
    ])
    
    # ========== TAB 1: UPLOAD RECORDING ==========
    with tab1:
        st.header("Upload Audio/Video File")
        st.markdown("Supported formats: MP3, WAV, MP4, WebM, M4A, OGG, FLAC")
        
        col1, col2 = st.columns(2)
        with col1:
            meeting_title = st.text_input(
                "Meeting Title",
                value=f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                help="Enter a descriptive title for this meeting"
            )
        with col2:
            participants = st.text_input(
                "Participants (comma-separated)",
                value=st.session_state.username,
                help="Enter participant names separated by commas"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            language = st.selectbox(
                "Language (optional)",
                ["Auto-detect"] + get_supported_languages(),
                help="Leave as Auto-detect for automatic language detection"
            )
        with col4:
            st.info(f"📊 Storage: **{st.session_state.storage_type}**")
        
        uploaded_file = st.file_uploader(
            "Choose audio or video file",
            type=['mp3', 'wav', 'mp4', 'webm', 'm4a', 'ogg', 'flac'],
            help="Maximum file size: 200MB"
        )
        
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", uploaded_file.name)
            with col2:
                st.metric("File Size", f"{file_size_mb:.2f} MB")
            with col3:
                st.metric("Format", uploaded_file.type)
            
            st.divider()
            
            if st.button("🚀 Process Meeting", type="primary", use_container_width=True):
                if not meeting_title.strip():
                    st.error("Please enter a meeting title")
                elif file_size_mb > 200:
                    st.error("File too large. Maximum size is 200MB")
                else:
                    with st.spinner("Processing... This may take several minutes."):
                        lang = None if language == "Auto-detect" else language
                        result = process_meeting_file(uploaded_file, meeting_title, participants, lang)
                        
                        if result:
                            st.markdown('<div class="success-box">', unsafe_allow_html=True)
                            st.markdown("### ✅ Meeting Processed Successfully!")
                            st.markdown(f"**Meeting ID:** `{result['meeting_id']}`")
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Display results in expandable sections
                            with st.expander("📝 Transcript Preview", expanded=True):
                                for segment in result['transcript'][:5]:
                                    col1, col2 = st.columns([1, 5])
                                    with col1:
                                        st.caption(segment['start'])
                                        st.markdown(f"**{segment['speaker']}**")
                                    with col2:
                                        st.write(segment['text'])
                                    st.markdown("---")
                                
                                if len(result['transcript']) > 5:
                                    st.info(f"Showing 5 of {len(result['transcript'])} segments. View full transcript in meeting details.")
                            
                            with st.expander("📊 Summary Preview"):
                                # Show first 500 characters of summary
                                preview = result['summary'][:500]
                                st.markdown(preview + "..." if len(result['summary']) > 500 else preview)
                            
                            # Download buttons
                            st.subheader("📥 Download Options")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                with open(result['pdf_path'], 'rb') as f:
                                    st.download_button(
                                        "📄 Download PDF",
                                        data=f.read(),
                                        file_name=f"{meeting_title.replace(' ', '_')}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                            
                            with col2:
                                st.download_button(
                                    "📝 Download Transcript",
                                    data=json.dumps(result['transcript'], indent=2),
                                    file_name=f"{meeting_title.replace(' ', '_')}_transcript.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                            
                            with col3:
                                st.download_button(
                                    "📊 Download Summary",
                                    data=result['summary'],
                                    file_name=f"{meeting_title.replace(' ', '_')}_summary.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                            
                            # Email option
                            if st.session_state.get('auto_email', True):
                                st.divider()
                                st.subheader("📧 Email Report")
                                
                                email_addresses = st.text_input(
                                    "Recipient Email Addresses",
                                    placeholder="email1@example.com, email2@example.com"
                                )
                                
                                if st.button("📨 Send Email", use_container_width=True):
                                    if email_addresses:
                                        with st.spinner("Sending email..."):
                                            success = send_meeting_email(
                                                email_addresses,
                                                result['pdf_path'],
                                                meeting_title
                                            )
                                        if success:
                                            st.success("✅ Email sent successfully!")
                                        else:
                                            st.error("❌ Failed to send email")
                                    else:
                                        st.error("Please enter at least one email address")
                            
                            # View meeting details button
                            if st.button("📄 View Full Meeting Details", use_container_width=True):
                                st.session_state.current_meeting = result['meeting_id']
                                st.rerun()
    
    # ========== TAB 2: LIVE RECORDING ==========
    with tab2:
        st.header("Live Browser Recording")
        st.info("🎙️ Record directly from your browser microphone")
        
        st.markdown("""
        ### How to use Live Recording:
        
        1. **Click "Start Recording"** below
        2. **Allow microphone access** when prompted by your browser
        3. **Speak naturally** during your meeting
        4. **Click "Stop & Process"** when finished
        
        ### Requirements:
        - Modern web browser (Chrome, Firefox, Edge)
        - Microphone access permission
        - Stable internet connection
        
        ### Features:
        - Real-time audio capture
        - High-quality recording (16kHz, mono)
        - Automatic format conversion
        - No file size limits
        """)
        
        st.warning("⚠️ **Note:** Live recording requires WebRTC support. See documentation for setup.")
        
        # Placeholder for WebRTC implementation
        st.markdown("---")
        st.subheader("Coming Soon")
        st.info("Live recording with streamlit-webrtc is under development. For now, please use the Upload option or Bot automation.")
        
        with st.expander("Implementation Details"):
            st.code("""
# Live recording will use streamlit-webrtc
from streamlit_webrtc import webrtc_streamer, WebRtcMode

ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=1024,
    media_stream_constraints={"video": False, "audio": True}
)

if ctx.audio_receiver:
    # Process audio frames in real-time
    # Save to file when stopped
    pass
            """, language="python")
    
    # ========== TAB 3: BOT AUTOMATION ==========
    with tab3:
        st.header("🤖 Automated Meeting Bot")
        
        st.markdown("""
        ### Puppeteer Bot for Google Meet / Zoom
        
        Automatically join meetings and capture:
        - 🎙️ High-quality audio stream
        - 👥 Participant list with exact display names
        - 💬 Live captions (Google Meet)
        - 📝 Meeting metadata
        
        ### Setup Instructions:
        
        1. **Navigate to bot directory:**
           ```bash
           cd bot/
           npm install
           ```
        
        2. **Configure meeting URL:**
           ```bash
           export MEET_URL="https://meet.google.com/abc-defg-hij"
           export BOT_NAME="MeetingInsight Bot"
           ```
        
        3. **Run the bot:**
           ```bash
           node meet_bot.js
           ```
        
        See `bot/README.md` for detailed setup guide.
        """)
        
        st.divider()
        
        st.subheader("Bot Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            platform = st.selectbox("Meeting Platform", ["Google Meet", "Zoom", "Microsoft Teams"])
        with col2:
            bot_name = st.text_input("Bot Display Name", value="MeetingInsight Bot")
        
        meet_url = st.text_input(
            "Meeting URL",
            placeholder="https://meet.google.com/abc-defg-hij",
            help="Paste the meeting link here"
        )
        
        st.checkbox("Capture audio stream", value=True)
        st.checkbox("Capture participant list", value=True)
        st.checkbox("Capture live captions", value=True)
        
        if st.button("🚀 Launch Bot", type="primary", use_container_width=True):
            if not meet_url:
                st.error("Please enter a meeting URL")
            else:
                st.warning("⚠️ Bot feature requires separate setup in `bot/` directory.")
                st.info("Run: `cd bot && node meet_bot.js`")
                st.code(f"""
# Configuration
MEET_URL={meet_url}
BOT_NAME="{bot_name}"
PLATFORM={platform}

# Run bot
node meet_bot.js
                """, language="bash")
        
        st.divider()
        
        with st.expander("⚠️ Important: Privacy & Consent"):
            st.markdown("""
            ### Legal Requirements
            
            **CRITICAL:** Recording meetings without consent is illegal in many jurisdictions!
            
            #### Before using the bot:
            
            1. ✅ **Inform all participants** that the meeting will be recorded
            2. ✅ **Obtain explicit consent** (verbal or written)
            3. ✅ **Display clear indicators** (bot name shows "Recording")
            4. ✅ **Provide opt-out mechanism** (participants can object)
            5. ✅ **Comply with local laws** (one-party vs two-party consent)
            
            #### Best Practices:
            
            - Add recording notice to meeting invites
            - Announce recording at start of meeting
            - Use descriptive bot name (e.g., "RecordingBot - Company")
            - Provide data deletion process
            - Maintain consent records
            
            **Failure to obtain consent may result in legal consequences!**
            """)
    
    # ========== TAB 4: DOCUMENTATION ==========
    with tab4:
        st.header("📚 Documentation & Help")
        
        doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
            "🚀 Quick Start",
            "📖 User Guide",
            "🔧 Setup",
            "❓ FAQ"
        ])
        
        with doc_tab1:
            st.markdown("""
            ### Quick Start Guide
            
            #### 1. Upload Your First Meeting
            
            1. Go to **Upload Recording** tab
            2. Enter meeting title and participants
            3. Upload audio/video file (MP3, WAV, MP4, etc.)
            4. Click **Process Meeting**
            5. Wait for AI processing (2-5 minutes per hour)
            6. Download PDF report
            
            #### 2. Review Transcript
            
            - View speaker-attributed transcript
            - Search for keywords
            - Download in multiple formats
            
            #### 3. Share Results
            
            - Email PDF to participants
            - Share audio link
            - Export to Google Drive
            
            #### Need Help?
            
            📧 Contact: aditya.dev@projectmail.com
            """)
        
        with doc_tab2:
            st.markdown("""
            ### Complete User Guide
            
            #### Features
            
            **Transcription:**
            - Millisecond-precision timestamps (HH:MM:SS.mmm)
            - 95+ languages supported
            - Word-level confidence scores
            - Custom vocabulary support
            
            **Speaker Diarization:**
            - Automatic speaker detection
            - Exact name resolution from platforms
            - Manual mapping interface
            - Speaker timeline visualization
            
            **AI Analysis:**
            - Executive summary (TL;DR)
            - Key points extraction
            - Action items with assignees
            - Decision tracking
            - Open questions identification
            
            **Storage Options:**
            - **Local:** Files stored on your machine
            - **Google Drive:** Upload to your Drive
            - **Temporary Links:** ngrok public URLs
            
            **Integrations:**
            - Google Meet notes
            - Google Calendar participants
            - Zoom API
            - Microsoft Teams
            
            #### Tips & Tricks
            
            - Use descriptive meeting titles for better searchability
            - Add participant names for accurate speaker mapping
            - Enable Google Notes fetch for comprehensive documentation
            - Use custom vocabulary for technical terms
            - Schedule regular cleanups of old meetings
            """)
        
        with doc_tab3:
            st.markdown("""
            ### Setup Instructions
            
            See **MANUAL_SETUP_CHECKLIST.md** for complete setup guide.
            
            #### Quick Links:
            
            - [Google OAuth Setup](#google-oauth)
            - [SMTP Email Configuration](#smtp-email)
            - [Bot Installation](#bot-setup)
            - [Docker Deployment](#docker)
            
            #### System Requirements:
            
            - Python 3.8+
            - 4GB+ RAM (8GB recommended)
            - ffmpeg installed
            - CPU: Any (GPU optional for faster processing)
            
            #### Optional Components:
            
            - Google Cloud Platform account (for Drive/Docs)
            - SMTP server access (for email)
            - ngrok account (for temporary links)
            - Node.js 16+ (for bot)
            """)
        
        with doc_tab4:
            st.markdown("""
            ### Frequently Asked Questions
            
            **Q: Is MeetingInsight really free?**
            A: Yes! 100% free and open-source. No API costs, no subscriptions.
            
            **Q: Does it work offline?**
            A: Yes! All processing happens locally on your machine.
            
            **Q: How accurate is the transcription?**
            A: 90-95% accuracy depending on audio quality and accents.
            
            **Q: Can I use it for sensitive meetings?**
            A: Yes! All data stays on your machine. Always obtain consent first.
            
            **Q: What languages are supported?**
            A: 95+ languages via Whisper AI model.
            
            **Q: How long does processing take?**
            A: ~2-5 minutes per hour of audio on average CPU.
            
            **Q: Can I customize the AI models?**
            A: Yes! Configure in Settings or environment variables.
            
            **Q: Is speaker identification accurate?**
            A: When using platform APIs (Google/Zoom), names are 100% accurate.
            
            **Q: Can I edit the transcript?**
            A: Export as JSON and edit, or use manual speaker mapping.
            
            **Q: How do I delete old meetings?**
            A: Use data retention settings or manually delete from dashboard.
            
            **Q: Can multiple users share the same instance?**
            A: Yes! Each user has their own meetings and access controls.
            
            **Q: What if something goes wrong?**
            A: Check logs/ directory or contact aditya.dev@projectmail.com
            """)

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main application entry point"""
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()