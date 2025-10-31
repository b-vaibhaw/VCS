"""
Audio transcription module using faster-whisper
CPU-optimized for Jetson Nano and similar devices
Supports word-level millisecond timestamps
"""
from faster_whisper import WhisperModel
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_SIZE = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large-v2
DEVICE = os.getenv('WHISPER_DEVICE', 'cpu')
COMPUTE_TYPE = os.getenv('WHISPER_COMPUTE_TYPE', 'int8')  # int8 for CPU, float16 for GPU

def get_whisper_model():
    """
    Load and cache Whisper model
    CPU optimizations applied automatically
    """
    logger.info(f"Loading Whisper model: {MODEL_SIZE} on {DEVICE}")
    
    model = WhisperModel(
        MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        cpu_threads=int(os.getenv('CPU_THREADS', '4')),
        num_workers=1,
        download_root=os.getenv('MODEL_CACHE_DIR', None)
    )
    
    logger.info("Whisper model loaded successfully")
    return model

def transcribe_audio_file(audio_path, language=None, initial_prompt=None):
    """
    Transcribe audio file with word-level timestamps
    
    Args:
        audio_path: Path to audio file (mp3, wav, mp4, etc.)
        language: Force specific language (None for auto-detect)
        initial_prompt: Custom prompt for context (e.g., technical terms)
    
    Returns:
        dict: {
            'language': detected/specified language,
            'duration': audio duration in seconds,
            'segments': [
                {
                    'start': start time in seconds,
                    'end': end time in seconds,
                    'text': transcribed text,
                    'words': [
                        {
                            'word': word text,
                            'start': word start time,
                            'end': word end time,
                            'probability': confidence score
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    logger.info(f"Transcribing: {audio_path}")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Load model
    model = get_whisper_model()
    
    # Transcribe with all optimizations
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,  # Balance between speed and accuracy
        best_of=5,
        temperature=0.0,  # Deterministic output
        word_timestamps=True,  # CRITICAL: Enable word-level timestamps
        vad_filter=True,  # Voice Activity Detection - removes silence
        vad_parameters=dict(
            min_silence_duration_ms=500,  # Minimum silence to split on
            speech_pad_ms=400  # Padding around speech segments
        ),
        initial_prompt=initial_prompt,  # Custom vocabulary context
        condition_on_previous_text=True,  # Use context from previous segments
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
        no_speech_threshold=0.6
    )
    
    # Build result structure
    result = {
        'language': info.language,
        'language_probability': info.language_probability,
        'duration': info.duration,
        'segments': []
    }
    
    # Process each segment
    for segment in segments:
        segment_data = {
            'id': segment.id,
            'seek': segment.seek,
            'start': segment.start,
            'end': segment.end,
            'text': segment.text.strip(),
            'tokens': segment.tokens,
            'temperature': segment.temperature,
            'avg_logprob': segment.avg_logprob,
            'compression_ratio': segment.compression_ratio,
            'no_speech_prob': segment.no_speech_prob,
            'words': []
        }
        
        # Extract word-level timestamps with millisecond precision
        if segment.words:
            for word in segment.words:
                segment_data['words'].append({
                    'word': word.word.strip(),
                    'start': word.start,
                    'end': word.end,
                    'probability': word.probability
                })
        
        result['segments'].append(segment_data)
    
    logger.info(f"Transcription complete: {len(result['segments'])} segments, "
                f"{info.duration:.2f}s duration, language: {info.language}")
    
    return result

def transcribe_audio_streaming(audio_path, callback=None):
    """
    Transcribe audio with streaming results (for real-time display)
    
    Args:
        audio_path: Path to audio file
        callback: Function to call with each segment as it's processed
    
    Returns:
        Same as transcribe_audio_file
    """
    model = get_whisper_model()
    
    segments_list = []
    segments, info = model.transcribe(audio_path, word_timestamps=True, vad_filter=True)
    
    for segment in segments:
        segment_data = {
            'start': segment.start,
            'end': segment.end,
            'text': segment.text.strip(),
            'words': [
                {
                    'word': w.word.strip(),
                    'start': w.start,
                    'end': w.end,
                    'probability': w.probability
                }
                for w in segment.words
            ] if segment.words else []
        }
        
        segments_list.append(segment_data)
        
        # Call callback for real-time updates
        if callback:
            callback(segment_data)
    
    return {
        'language': info.language,
        'duration': info.duration,
        'segments': segments_list
    }

def get_supported_languages():
    """Return list of supported languages"""
    return [
        'en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr', 'pl', 'ca', 'nl',
        'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi', 'he', 'uk', 'el', 'ms', 'cs', 'ro',
        'da', 'hu', 'ta', 'no', 'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy',
        'sk', 'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk', 'br', 'eu',
        'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw', 'gl', 'mr', 'pa', 'si', 'km',
        'sn', 'yo', 'so', 'af', 'oc', 'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo',
        'uz', 'fo', 'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl', 'mg',
        'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su'
    ]