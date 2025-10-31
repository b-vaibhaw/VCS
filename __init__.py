"""
MeetingInsight Core Modules
"""

__version__ = "1.0.0"
__author__ = "MeetingInsight Team"

from .auth import authenticate_user, init_user_db
from .transcriber import transcribe_audio_file
from .diarizer import diarize_audio_file, merge_transcript_with_diarization
from .summarizer import generate_summary_and_action_items
from .pdf_email import generate_meeting_pdf, send_meeting_email
from .storage import handle_audio_storage
from .utils import init_database, log_audit, format_timestamp_ms

__all__ = [
    'authenticate_user',
    'init_user_db',
    'transcribe_audio_file',
    'diarize_audio_file',
    'merge_transcript_with_diarization',
    'generate_summary_and_action_items',
    'generate_meeting_pdf',
    'send_meeting_email',
    'handle_audio_storage',
    'init_database',
    'log_audit',
    'format_timestamp_ms',
]