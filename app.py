"""
Flask server for real-time video processing pipeline
FIXED VERSION with proper static file serving
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import time
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app - NO static_folder parameter
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
CHUNKS_FOLDER = 'chunks'
PROCESSED_FOLDER = 'processed'
CHUNK_DURATION = 5

# Ensure directories exist
for folder in [UPLOAD_FOLDER, CHUNKS_FOLDER, PROCESSED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Import processors (make sure these imports work)
try:
    from Video_Processing.video_processor import VideoProcessor
    from Video_Processing.audio_processor import AudioProcessor
    from Video_Processing.transcription_service import TranscriptionService
    
    # Initialize services
    video_processor = VideoProcessor(CHUNKS_FOLDER, CHUNK_DURATION)
    audio_processor = AudioProcessor()
    transcription_service = TranscriptionService()
    logger.info("✅ All processors initialized successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import processors: {str(e)}")
    video_processor = None
    audio_processor = None
    transcription_service = None

# Cache for processed chunks
chunk_cache = defaultdict(dict)


# ============= STATIC FILE ROUTES =============
@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('./static', 'index.html')


@app.route('/styles.css')
def styles():
    """Serve CSS file"""
    return send_from_directory('./static', 'styles.css')


@app.route('/app.js')
def app_js():
    """Serve JavaScript file"""
    return send_from_directory('./static', 'app.js')


# ============= API ROUTES =============
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    processors_loaded = all([video_processor, audio_processor, transcription_service])
    return jsonify({
        'status': 'healthy' if processors_loaded else 'degraded',
        'processors_loaded': processors_loaded,
        'cached_chunks': sum(len(v) for v in chunk_cache.values())
    })


@app.route('/api/video/info', methods=['POST'])
def get_video_info():
    """Get video information without downloading"""
    try:
        data = request.json
        video_url = data.get('video_url')
        
        logger.info(f"📹 Getting info for: {video_url}")
        
        if not video_url:
            return jsonify({'success': False, 'error': 'video_url is required'}), 400
        
        if not video_processor:
            return jsonify({'success': False, 'error': 'Video processor not initialized'}), 500
        
        # Get video metadata
        metadata = video_processor.get_video_info(video_url)
        
        if not metadata:
            return jsonify({'success': False, 'error': 'Failed to get video information'}), 500
        
        logger.info(f"✅ Video info retrieved: {metadata.get('title', 'Unknown')}")
        
        return jsonify({
            'success': True,
            'duration': metadata.get('duration', 0),
            'title': metadata.get('title', 'Unknown'),
            'thumbnail': metadata.get('thumbnail', ''),
            'video_url': video_url,
            'chunk_duration': CHUNK_DURATION
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting video info: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/process/chunk', methods=['POST'])
def process_chunk():
    """Process a specific chunk of video in real-time"""
    try:
        data = request.json
        video_url = data.get('video_url')
        start_time = data.get('start_time', 0)
        duration = data.get('duration', CHUNK_DURATION)
        
        logger.info(f"🎬 Processing chunk at {start_time}s")
        
        if not video_url:
            return jsonify({'success': False, 'error': 'video_url is required'}), 400
        
        if not all([video_processor, audio_processor, transcription_service]):
            return jsonify({'success': False, 'error': 'Processors not initialized'}), 500
        
        # Create cache key
        cache_key = f"{video_url}_{start_time}_{duration}"
        
        # Check cache first
        if cache_key in chunk_cache.get(video_url, {}):
            logger.info(f"💾 Returning cached chunk: {start_time}s")
            cached_result = chunk_cache[video_url][cache_key].copy()
            cached_result['from_cache'] = True
            return jsonify(cached_result)
        
        # Download chunk
        chunk_path = video_processor.download_chunk(video_url, start_time, duration)
        
        if not chunk_path:
            return jsonify({'success': False, 'error': 'Failed to download chunk'}), 500
        
        # Extract audio
        audio_path = audio_processor.extract_audio(chunk_path, int(start_time))
        
        if not audio_path:
            return jsonify({'success': False, 'error': 'Failed to extract audio'}), 500
        
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
            'processed_at': time.time(),
            'from_cache': False
        }
        
        # Cache the result
        if video_url not in chunk_cache:
            chunk_cache[video_url] = {}
        chunk_cache[video_url][cache_key] = result
        
        logger.info(f"✅ Chunk at {start_time}s processed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error processing chunk: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clear_cache', methods=['POST'])
def clear_cache():
    """Clear the chunk cache"""
    try:
        data = request.json or {}
        video_url = data.get('video_url')
        
        if video_url:
            if video_url in chunk_cache:
                del chunk_cache[video_url]
                return jsonify({'success': True, 'message': f'Cache cleared for {video_url}'})
            return jsonify({'success': True, 'message': 'No cache found for URL'})
        else:
            chunk_cache.clear()
            return jsonify({'success': True, 'message': 'All cache cleared'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Flask Server")
    print("=" * 60)
    print(f"📍 Server: http://localhost:5000")
    print(f"📍 Health Check: http://localhost:5000/health")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)