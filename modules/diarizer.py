"""
Speaker diarization module with multiple backends
Primary: pyannote.audio (accurate but requires GPU/HF token)
Fallback: Energy-based clustering (CPU-friendly, no dependencies)
"""
import torch
import numpy as np
from pathlib import Path
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import pyannote
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
    logger.info("pyannote.audio available")
except ImportError:
    PYANNOTE_AVAILABLE = False
    logger.warning("pyannote.audio not available. Using fallback diarization.")

def diarize_audio_file(audio_path, num_speakers=None, method='auto'):
    """
    Perform speaker diarization
    
    Args:
        audio_path: Path to audio file
        num_speakers: Expected number of speakers (None for auto-detect)
        method: 'pyannote', 'fallback', or 'auto' (tries pyannote first)
    
    Returns:
        List of diarization segments:
        [
            {
                'start': start time in seconds,
                'end': end time in seconds,
                'speaker': speaker label (e.g., 'SPEAKER_0'),
                'duration': segment duration
            },
            ...
        ]
    """
    logger.info(f"Starting diarization: {audio_path}, method={method}")
    
    if method == 'auto':
        if PYANNOTE_AVAILABLE and os.getenv('HF_TOKEN'):
            method = 'pyannote'
        else:
            method = 'fallback'
            logger.info("Using fallback diarization (pyannote not available or no HF_TOKEN)")
    
    if method == 'pyannote':
        return diarize_with_pyannote(audio_path, num_speakers)
    else:
        return diarize_fallback(audio_path, num_speakers)

def diarize_with_pyannote(audio_path, num_speakers=None):
    """
    Use pyannote.audio for accurate speaker diarization
    
    Requires:
    - HF_TOKEN environment variable
    - Accept terms at: https://huggingface.co/pyannote/speaker-diarization
    """
    hf_token = os.getenv('HF_TOKEN')
    
    if not hf_token:
        logger.warning("HF_TOKEN not set. Falling back to energy-based diarization.")
        return diarize_fallback(audio_path, num_speakers)
    
    try:
        # Load pre-trained pipeline
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        
        # Use CPU or GPU based on availability
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        pipeline.to(device)
        logger.info(f"Running pyannote on {device}")
        
        # Perform diarization
        diarization = pipeline(
            audio_path,
            num_speakers=num_speakers,
            min_speakers=1 if num_speakers is None else num_speakers,
            max_speakers=10 if num_speakers is None else num_speakers
        )
        
        # Convert to our format
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': f"SPEAKER_{speaker}",
                'duration': turn.end - turn.start
            })
        
        logger.info(f"Pyannote diarization complete: {len(segments)} segments")
        return segments
        
    except Exception as e:
        logger.error(f"Pyannote diarization failed: {str(e)}")
        logger.info("Falling back to energy-based diarization")
        return diarize_fallback(audio_path, num_speakers)

def diarize_fallback(audio_path, num_speakers=None):
    """
    Fallback speaker diarization using energy-based segmentation + MFCC clustering
    CPU-friendly, no external dependencies beyond scipy/sklearn
    """
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
    except ImportError:
        logger.error("pydub not available. Install with: pip install pydub")
        # Return single speaker as last resort
        return [{'start': 0, 'end': 100, 'speaker': 'SPEAKER_0', 'duration': 100}]
    
    try:
        import librosa
        from sklearn.cluster import AgglomerativeClustering
    except ImportError:
        logger.error("librosa or sklearn not available")
        return [{'start': 0, 'end': 100, 'speaker': 'SPEAKER_0', 'duration': 100}]
    
    logger.info("Using energy-based diarization with MFCC features")
    
    # Load audio
    audio = AudioSegment.from_file(audio_path)
    
    # Detect speech segments (non-silent parts)
    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=500,  # 500ms silence to split segments
        silence_thresh=-40,  # dB threshold
        seek_step=10
    )
    
    if not nonsilent_ranges:
        logger.warning("No speech detected in audio")
        return []
    
    # Load audio with librosa for feature extraction
    y, sr = librosa.load(audio_path, sr=16000)
    
    segments = []
    features = []
    
    # Extract features for each speech segment
    for start_ms, end_ms in nonsilent_ranges:
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0
        
        # Extract audio segment
        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        segment_audio = y[start_sample:end_sample]
        
        if len(segment_audio) > sr * 0.3:  # At least 0.3 seconds
            # Extract MFCC features (speaker characteristics)
            mfcc = librosa.feature.mfcc(y=segment_audio, sr=sr, n_mfcc=13)
            mfcc_delta = librosa.feature.delta(mfcc)
            mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
            
            # Combine features
            features_combined = np.concatenate([
                np.mean(mfcc, axis=1),
                np.std(mfcc, axis=1),
                np.mean(mfcc_delta, axis=1),
                np.mean(mfcc_delta2, axis=1)
            ])
            
            features.append(features_combined)
            
            segments.append({
                'start': start_sec,
                'end': end_sec,
                'duration': end_sec - start_sec
            })
    
    if not features:
        logger.warning("No valid segments for clustering")
        return []
    
    # Cluster segments by speaker
    if num_speakers is None:
        # Auto-detect number of speakers (max 5)
        num_speakers = min(5, max(2, len(segments) // 10))
    
    num_speakers = min(num_speakers, len(segments))
    
    if len(features) > 1:
        clustering = AgglomerativeClustering(n_clusters=num_speakers)
        labels = clustering.fit_predict(features)
        
        for i, label in enumerate(labels):
            segments[i]['speaker'] = f"SPEAKER_{label}"
    else:
        segments[0]['speaker'] = 'SPEAKER_0'
    
    logger.info(f"Fallback diarization complete: {len(segments)} segments, {num_speakers} speakers")
    return segments

def merge_transcript_with_diarization(transcript_data, diarization_data):
    """
    Merge transcription segments with speaker diarization
    Uses overlap detection to assign speakers to transcript segments
    
    Args:
        transcript_data: Output from transcribe_audio_file
        diarization_data: Output from diarize_audio_file
    
    Returns:
        List of merged segments with speaker labels and millisecond timestamps
    """
    from modules.utils import format_timestamp_ms
    
    merged = []
    
    for segment in transcript_data['segments']:
        # Find speaker for this timestamp
        speaker = find_speaker_at_time(
            segment['start'],
            segment['end'],
            diarization_data
        )
        
        merged.append({
            'start': format_timestamp_ms(segment['start']),
            'end': format_timestamp_ms(segment['end']),
            'start_seconds': segment['start'],
            'end_seconds': segment['end'],
            'speaker': speaker,
            'text': segment['text'],
            'words': segment.get('words', []),
            'confidence': 1.0 - segment.get('no_speech_prob', 0)
        })
    
    logger.info(f"Merged {len(merged)} segments with speaker labels")
    return merged

def find_speaker_at_time(start_time, end_time, diarization_data):
    """
    Find which speaker is active during given time range
    Uses maximum overlap method
    """
    if not diarization_data:
        return "SPEAKER_0"
    
    max_overlap = 0
    best_speaker = diarization_data[0]['speaker']
    
    for segment in diarization_data:
        # Calculate overlap
        overlap_start = max(start_time, segment['start'])
        overlap_end = min(end_time, segment['end'])
        overlap = max(0, overlap_end - overlap_start)
        
        if overlap > max_overlap:
            max_overlap = overlap
            best_speaker = segment['speaker']
    
    return best_speaker

def refine_speaker_boundaries(merged_segments, min_segment_duration=0.5):
    """
    Post-process speaker segments to remove very short switches
    Merges adjacent segments from same speaker
    """
    if not merged_segments:
        return []
    
    refined = [merged_segments[0]]
    
    for segment in merged_segments[1:]:
        last_segment = refined[-1]
        
        # If same speaker and close in time, merge
        if (segment['speaker'] == last_segment['speaker'] and
            segment['start_seconds'] - last_segment['end_seconds'] < min_segment_duration):
            
            # Merge segments
            last_segment['end'] = segment['end']
            last_segment['end_seconds'] = segment['end_seconds']
            last_segment['text'] += ' ' + segment['text']
            last_segment['words'].extend(segment['words'])
        else:
            refined.append(segment)
    
    return refined