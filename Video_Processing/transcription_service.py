"""
Transcription service module
Supports multiple speech-to-text models optimized for deployment
"""

import os
import logging
import whisper
import torch
from transformers import pipeline
import subprocess

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Handles speech-to-text transcription
    Supports multiple models with PythonAnywhere compatibility
    """
    
    def __init__(self, model_type='whisper-tiny'):
        """
        Initialize transcription service
        
        Args:
            model_type: Options:
                - 'whisper-tiny': Fast, lightweight (OpenAI Whisper)
                - 'whisper-base': Better accuracy (OpenAI Whisper)
                - 'whisper-small': Good balance (OpenAI Whisper)
                - 'wav2vec2': Facebook's model (HuggingFace)
                - 'vosk': Offline model (lightweight)
        """
        self.model_type = model_type
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the selected transcription model"""
        try:
            if self.model_type.startswith('whisper'):
                # OpenAI Whisper models
                model_size = self.model_type.split('-')[1]  # tiny, base, small, etc.
                logger.info(f"Loading Whisper model: {model_size}")
                
                # Use CPU if CUDA not available (PythonAnywhere)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = whisper.load_model(model_size, device=device)
                logger.info(f"Whisper model loaded on {device}")
                
            elif self.model_type == 'wav2vec2':
                # Facebook's Wav2Vec2 model
                logger.info("Loading Wav2Vec2 model")
                self.model = pipeline(
                    "automatic-speech-recognition",
                    model="facebook/wav2vec2-base-960h",
                    device=-1  # CPU
                )
                logger.info("Wav2Vec2 model loaded")
                
            else:
                logger.warning(f"Unknown model type: {self.model_type}, defaulting to whisper-tiny")
                self.model = whisper.load_model("tiny")
                
        except Exception as e:
            logger.error(f"Error loading transcription model: {str(e)}")
            # Fallback to tiny model
            try:
                self.model = whisper.load_model("tiny")
                logger.info("Loaded fallback Whisper tiny model")
            except:
                logger.error("Failed to load any transcription model")
                self.model = None
    
    def transcribe(self, audio_path):
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file (WAV format preferred)
            
        Returns:
            Dictionary with transcription results:
            {
                'text': str,
                'segments': list (with timestamps),
                'language': str
            }
        """
        try:
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found: {audio_path}")
                return {'text': '', 'segments': [], 'language': 'en'}
            
            if self.model is None:
                logger.error("No transcription model loaded")
                return {'text': '', 'segments': [], 'language': 'en'}
            
            if self.model_type.startswith('whisper'):
                return self._transcribe_whisper(audio_path)
            elif self.model_type == 'wav2vec2':
                return self._transcribe_wav2vec2(audio_path)
            else:
                return {'text': '', 'segments': [], 'language': 'en'}
                
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return {'text': '', 'segments': [], 'language': 'en'}
    
    def _transcribe_whisper(self, audio_path):
        """Transcribe using Whisper model"""
        try:
            logger.info(f"Transcribing with Whisper: {audio_path}")
            
            # Transcribe with timestamps
            result = self.model.transcribe(
                audio_path,
                language='en',  # Force English for Super Bowl commentary
                task='transcribe',
                word_timestamps=False,
                verbose=False
            )
            
            # Format segments
            segments = []
            if 'segments' in result:
                for seg in result['segments']:
                    segments.append({
                        'start': seg['start'],
                        'end': seg['end'],
                        'text': seg['text'].strip()
                    })
            
            transcription = {
                'text': result['text'].strip(),
                'segments': segments,
                'language': result.get('language', 'en')
            }
            
            logger.info(f"Transcription complete: {len(transcription['text'])} chars")
            return transcription
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            return {'text': '', 'segments': [], 'language': 'en'}
    
    def _transcribe_wav2vec2(self, audio_path):
        """Transcribe using Wav2Vec2 model"""
        try:
            logger.info(f"Transcribing with Wav2Vec2: {audio_path}")
            
            result = self.model(audio_path)
            
            transcription = {
                'text': result['text'],
                'segments': [],  # Wav2Vec2 doesn't provide segments by default
                'language': 'en'
            }
            
            logger.info(f"Transcription complete: {len(transcription['text'])} chars")
            return transcription
            
        except Exception as e:
            logger.error(f"Wav2Vec2 transcription error: {str(e)}")
            return {'text': '', 'segments': [], 'language': 'en'}
    
    def get_model_info(self):
        """Get information about the loaded model"""
        return {
            'model_type': self.model_type,
            'loaded': self.model is not None,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }


class LightweightTranscriptionService:
    """
    Ultra-lightweight transcription using Vosk (offline)
    Good for resource-constrained environments like PythonAnywhere
    """
    
    def __init__(self, model_path=None):
        """
        Initialize Vosk transcription
        
        Args:
            model_path: Path to Vosk model directory
        """
        try:
            from vosk import Model, KaldiRecognizer
            import json
            import wave
            
            self.Model = Model
            self.KaldiRecognizer = KaldiRecognizer
            self.json = json
            self.wave = wave
            
            # Default to small English model
            if model_path is None:
                model_path = "vosk-model-small-en-us-0.15"
            
            if os.path.exists(model_path):
                self.model = Model(model_path)
                logger.info(f"Vosk model loaded from {model_path}")
            else:
                logger.warning(f"Vosk model not found at {model_path}")
                self.model = None
                
        except ImportError:
            logger.warning("Vosk not installed - install with: pip install vosk")
            self.model = None
    
    def transcribe(self, audio_path):
        """Transcribe using Vosk"""
        try:
            if self.model is None:
                return {'text': '', 'segments': [], 'language': 'en'}
            
            wf = self.wave.open(audio_path, "rb")
            rec = self.KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    results.append(self.json.loads(rec.Result()))
            
            # Final result
            final_result = self.json.loads(rec.FinalResult())
            results.append(final_result)
            
            # Combine all text
            full_text = ' '.join([r.get('text', '') for r in results])
            
            return {
                'text': full_text,
                'segments': results,
                'language': 'en'
            }
            
        except Exception as e:
            logger.error(f"Vosk transcription error: {str(e)}")
            return {'text': '', 'segments': [], 'language': 'en'}