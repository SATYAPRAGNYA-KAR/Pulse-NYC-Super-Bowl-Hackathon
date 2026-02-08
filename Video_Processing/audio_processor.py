"""
Audio processing module
Handles audio extraction from video and amplitude analysis
"""

import os
import subprocess
import logging
import numpy as np
from scipy.io import wavfile
import librosa

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio extraction and analysis"""
    
    def __init__(self):
        self.audio_folder = 'audio'
        os.makedirs(self.audio_folder, exist_ok=True)
    
    def extract_audio(self, video_path, chunk_index):
        """
        Extract audio from video chunk to MP3 and WAV formats
        
        Args:
            video_path: Path to video chunk
            chunk_index: Chunk index for naming
            
        Returns:
            Path to extracted audio file (WAV for processing)
        """
        try:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            mp3_path = os.path.join(self.audio_folder, f'{base_name}.mp3')
            wav_path = os.path.join(self.audio_folder, f'{base_name}.wav')
            
            # Extract to MP3 (for compatibility)
            cmd_mp3 = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-ar', '44100',
                '-y',
                mp3_path
            ]
            
            subprocess.run(cmd_mp3, check=True, capture_output=True)
            
            # Extract to WAV (for processing/transcription)
            cmd_wav = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz for transcription
                '-ac', '1',  # Mono
                '-y',
                wav_path
            ]
            
            subprocess.run(cmd_wav, check=True, capture_output=True)
            
            logger.info(f"Audio extracted: {wav_path}")
            return wav_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return None
    
    def get_amplitudes(self, audio_path, sample_rate=100):
        """
        Get amplitude array from audio file
        
        Args:
            audio_path: Path to audio file
            sample_rate: Number of amplitude samples per second
            
        Returns:
            Array of amplitude values normalized to 0-1 range
        """
        try:
            # Load audio file using librosa
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate the hop length for desired sample rate
            duration = len(y) / sr
            n_samples = int(duration * sample_rate)
            hop_length = len(y) // n_samples if n_samples > 0 else len(y)
            
            # Calculate RMS (Root Mean Square) energy
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            
            # Normalize to 0-1 range
            if len(rms) > 0:
                rms_normalized = (rms - rms.min()) / (rms.max() - rms.min() + 1e-8)
            else:
                rms_normalized = np.array([])
            
            # Convert to list for JSON serialization
            amplitudes = rms_normalized.tolist()
            
            logger.info(f"Extracted {len(amplitudes)} amplitude samples")
            return amplitudes
            
        except Exception as e:
            logger.error(f"Error getting amplitudes: {str(e)}")
            return []
    
    def get_audio_features(self, audio_path):
        """
        Extract additional audio features that might be useful
        
        Returns:
            Dictionary with audio features
        """
        try:
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate various features
            features = {
                'duration': len(y) / sr,
                'sample_rate': sr,
                'rms_mean': float(np.mean(librosa.feature.rms(y=y))),
                'rms_std': float(np.std(librosa.feature.rms(y=y))),
                'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(y))),
            }
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            
            # Tempo estimation (could indicate exciting moments)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {str(e)}")
            return {}
    
    def detect_loud_moments(self, audio_path, threshold=0.7):
        """
        Detect timestamps of loud moments (potential exciting events)
        
        Args:
            audio_path: Path to audio file
            threshold: Amplitude threshold (0-1) for "loud"
            
        Returns:
            List of timestamps (in seconds) of loud moments
        """
        try:
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate RMS with fine granularity
            hop_length = 512
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            
            # Normalize
            rms_normalized = (rms - rms.min()) / (rms.max() - rms.min() + 1e-8)
            
            # Find moments above threshold
            loud_indices = np.where(rms_normalized > threshold)[0]
            
            # Convert to timestamps
            timestamps = librosa.frames_to_time(loud_indices, sr=sr, hop_length=hop_length)
            
            return timestamps.tolist()
            
        except Exception as e:
            logger.error(f"Error detecting loud moments: {str(e)}")
            return []