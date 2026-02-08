"""
Flask server for real-time video processing pipeline
Handles real-time video chunking, audio extraction, transcription, and amplitude analysis
Processes chunks on-demand as the video plays on frontend
"""

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import os
import json
import time
from Video_Processing.video_processor import VideoProcessor
from Video_Processing.audio_processor import AudioProcessor
from Video_Processing.transcription_service import TranscriptionService
import threading
from queue import Queue
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
CHUNKS_FOLDER = 'chunks'
PROCESSED_FOLDER = 'processed'
CHUNK_DURATION = 5  # seconds

# Ensure directories exist
for folder in [UPLOAD_FOLDER, CHUNKS_FOLDER, PROCESSED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Initialize services
video_processor = VideoProcessor(CHUNKS_FOLDER, CHUNK_DURATION)
audio_processor = AudioProcessor()
transcription_service = TranscriptionService()

# Cache for processed chunks to avoid reprocessing
chunk_cache = defaultdict(dict)


@app.route('/')
def index():
    """Serve the main frontend"""
    return send_from_directory('static', 'index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'cached_chunks': sum(len(v) for v in chunk_cache.values())
    })


@app.route('/api/video/info', methods=['POST'])
def get_video_info():
    """
    Get video information without downloading
    Expected JSON: {"video_url": "https://youtube.com/..."}
    """
    try:
        data = request.json
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({'error': 'video_url is required'}), 400
        
        # Get video metadata using yt-dlp
        metadata = video_processor.get_video_info(video_url)
        
        if not metadata:
            return jsonify({'error': 'Failed to get video information'}), 500
        
        return jsonify({
            'success': True,
            'duration': metadata.get('duration', 0),
            'title': metadata.get('title', 'Unknown'),
            'thumbnail': metadata.get('thumbnail', ''),
            'video_url': video_url,
            'chunk_duration': CHUNK_DURATION
        })
        
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/process/chunk', methods=['POST'])
def process_chunk():
    """
    Process a specific chunk of video in real-time
    Expected JSON: {
        "video_url": "https://youtube.com/...",
        "start_time": 0,
        "duration": 5
    }
    """
    print("🔥 process_chunk called")
    try:
        data = request.json
        video_url = data.get('video_url')
        start_time = data.get('start_time', 0)
        duration = data.get('duration', CHUNK_DURATION)
        
        if not video_url:
            return jsonify({'error': 'video_url is required'}), 400
        
        # Create cache key
        cache_key = f"{video_url}_{start_time}_{duration}"
        
        # Check cache first
        if cache_key in chunk_cache.get(video_url, {}):
            logger.info(f"Returning cached chunk: {start_time}s")
            return jsonify(chunk_cache[video_url][cache_key])
        
        # Process chunk
        logger.info(f"Processing chunk at {start_time}s")
        
        # Download only the specific chunk
        chunk_path = video_processor.download_chunk(video_url, start_time, duration)
        
        if not chunk_path:
            return jsonify({'error': 'Failed to download chunk'}), 500
        
        # Extract audio
        audio_path = audio_processor.extract_audio(chunk_path, int(start_time))
        
        # Get amplitudes
        amplitudes = audio_processor.get_amplitudes(audio_path)
        
        # Transcribe
        transcript = transcription_service.transcribe(audio_path)
        
        # Prepare result
        result = {
            'success': True,
            'start_time': start_time,
            'duration': duration,
            'video_path': chunk_path,
            'audio_path': audio_path,
            'transcript': transcript,
            'amplitudes': amplitudes,
            'processed_at': time.time()
        }
        
        # Cache the result
        if video_url not in chunk_cache:
            chunk_cache[video_url] = {}
        chunk_cache[video_url][cache_key] = result
        
        logger.info(f"Chunk at {start_time}s processed successfully")
        return jsonify(result)
    
        print("✅ process_chunk completed")
        
    except Exception as e:
        logger.error(f"Error processing chunk: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/process/batch', methods=['POST'])
def process_batch():
    """
    Process multiple chunks in parallel (for pre-buffering)
    Expected JSON: {
        "video_url": "https://youtube.com/...",
        "chunks": [
            {"start_time": 0, "duration": 5},
            {"start_time": 5, "duration": 5},
            ...
        ]
    }
    """
    try:
        data = request.json
        video_url = data.get('video_url')
        chunks = data.get('chunks', [])
        
        if not video_url or not chunks:
            return jsonify({'error': 'video_url and chunks are required'}), 400
        
        results = []
        
        # Process each chunk
        for chunk in chunks:
            start_time = chunk.get('start_time', 0)
            duration = chunk.get('duration', CHUNK_DURATION)
            
            # Use the single chunk processor
            chunk_result = process_single_chunk(video_url, start_time, duration)
            results.append(chunk_result)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return jsonify({'error': str(e)}), 500


def process_single_chunk(video_url, start_time, duration):
    """Helper function to process a single chunk"""
    try:
        cache_key = f"{video_url}_{start_time}_{duration}"
        
        # Check cache
        if cache_key in chunk_cache.get(video_url, {}):
            return chunk_cache[video_url][cache_key]
        
        # Download chunk
        chunk_path = video_processor.download_chunk(video_url, start_time, duration)
        
        if not chunk_path:
            return {'error': 'Failed to download chunk', 'start_time': start_time}
        
        # Extract audio
        audio_path = audio_processor.extract_audio(chunk_path, int(start_time))
        
        # Get amplitudes
        amplitudes = audio_processor.get_amplitudes(audio_path)
        
        # Transcribe
        transcript = transcription_service.transcribe(audio_path)
        
        # Prepare result
        result = {
            'success': True,
            'start_time': start_time,
            'duration': duration,
            'transcript': transcript,
            'amplitudes': amplitudes,
            'processed_at': time.time()
        }
        
        # Cache
        if video_url not in chunk_cache:
            chunk_cache[video_url] = {}
        chunk_cache[video_url][cache_key] = result
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing single chunk: {str(e)}")
        return {'error': str(e), 'start_time': start_time}


@app.route('/api/clear_cache', methods=['POST'])
def clear_cache():
    """Clear the chunk cache"""
    try:
        data = request.json
        video_url = data.get('video_url')
        
        if video_url:
            if video_url in chunk_cache:
                del chunk_cache[video_url]
                return jsonify({'success': True, 'message': f'Cache cleared for {video_url}'})
        else:
            chunk_cache.clear()
            return jsonify({'success': True, 'message': 'All cache cleared'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Global state for active processing sessions
active_sessions = {}


class ProcessingSession:
    """Manages a single video processing session"""
    
    def __init__(self, session_id, video_url):
        self.session_id = session_id
        self.video_url = video_url
        self.chunk_queue = Queue()
        self.results_queue = Queue()
        self.is_active = False
        self.current_chunk_index = 0
        
    def process_chunk(self, chunk_data):
        """Process a single video chunk"""
        try:
            chunk_index = chunk_data['chunk_index']
            video_path = chunk_data['video_path']
            
            logger.info(f"Processing chunk {chunk_index} for session {self.session_id}")
            
            # Extract audio from video chunk
            audio_path = audio_processor.extract_audio(video_path, chunk_index)
            
            # Get audio amplitudes
            amplitudes = audio_processor.get_amplitudes(audio_path)
            
            # Transcribe audio
            transcript = transcription_service.transcribe(audio_path)
            
            # Prepare result
            result = {
                'session_id': self.session_id,
                'chunk_index': chunk_index,
                'timestamp': chunk_index * CHUNK_DURATION,
                'duration': CHUNK_DURATION,
                'video_path': video_path,
                'audio_path': audio_path,
                'transcript': transcript,
                'amplitudes': amplitudes,
                'processed_at': time.time()
            }
            
            self.results_queue.put(result)
            logger.info(f"Chunk {chunk_index} processed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            return None


if __name__ == '__main__':
    # For development
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    # app.run()