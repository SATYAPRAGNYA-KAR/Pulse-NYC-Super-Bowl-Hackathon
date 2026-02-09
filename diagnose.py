"""
Diagnostic script to check if your setup is correct
Run this before starting the Flask app
"""

import sys
import os

print("=" * 60)
print("🔍 DIAGNOSTIC CHECK")
print("=" * 60)

# 1. Check Python version
print(f"\n1. Python Version: {sys.version}")
if sys.version_info < (3, 7):
    print("   ⚠️  WARNING: Python 3.7+ recommended")

# 2. Check required packages
print("\n2. Checking Required Packages:")
required_packages = [
    'flask',
    'flask_cors',
    'yt_dlp',
    'whisper',
    'torch',
    'librosa',
    'scipy',
    'numpy'
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} - NOT FOUND")
        missing_packages.append(package)

if missing_packages:
    print(f"\n   ⚠️  Missing packages: {', '.join(missing_packages)}")
    print("   Install with: pip install " + " ".join(missing_packages))

# 3. Check directories
print("\n3. Checking Directories:")
required_dirs = ['uploads', 'chunks', 'audio', 'processed', 'Video_Processing']
for directory in required_dirs:
    if os.path.exists(directory):
        print(f"   ✅ {directory}/")
    else:
        print(f"   ❌ {directory}/ - NOT FOUND")
        try:
            os.makedirs(directory)
            print(f"      ✅ Created {directory}/")
        except:
            print(f"      ❌ Failed to create {directory}/")

# 4. Check files
print("\n4. Checking Required Files:")
required_files = [
    'static/index.html',
    'static/styles.css',
    'static/app.js',
    'Video_Processing/video_processor.py',
    'Video_Processing/audio_processor.py',
    'Video_Processing/transcription_service.py'
]

for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - NOT FOUND")

# 5. Check ffmpeg
print("\n5. Checking External Tools:")
import subprocess

try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
    if result.returncode == 0:
        print("   ✅ ffmpeg")
    else:
        print("   ❌ ffmpeg - Error running")
except FileNotFoundError:
    print("   ❌ ffmpeg - NOT FOUND")
    print("      Install: sudo apt-get install ffmpeg")
except subprocess.TimeoutExpired:
    print("   ⚠️  ffmpeg - Timeout")

try:
    result = subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5)
    if result.returncode == 0:
        print("   ✅ ffprobe")
    else:
        print("   ❌ ffprobe - Error running")
except FileNotFoundError:
    print("   ❌ ffprobe - NOT FOUND")
except subprocess.TimeoutExpired:
    print("   ⚠️  ffprobe - Timeout")

# 6. Test imports
print("\n6. Testing Module Imports:")
try:
    from Video_Processing.video_processor import VideoProcessor
    print("   ✅ VideoProcessor")
except Exception as e:
    print(f"   ❌ VideoProcessor - {str(e)}")

try:
    from Video_Processing.audio_processor import AudioProcessor
    print("   ✅ AudioProcessor")
except Exception as e:
    print(f"   ❌ AudioProcessor - {str(e)}")

try:
    from Video_Processing.transcription_service import TranscriptionService
    print("   ✅ TranscriptionService")
except Exception as e:
    print(f"   ❌ TranscriptionService - {str(e)}")

# 7. Test yt-dlp
print("\n7. Testing yt-dlp:")
try:
    import yt_dlp
    print("   ✅ yt_dlp imported")
    
    # Try to get info for a test video (not downloading)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ydl_opts = {'quiet': True, 'no_warnings': True}
    
    print(f"   Testing with: {test_url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(test_url, download=False)
        if info:
            print(f"   ✅ Successfully retrieved video info")
            print(f"      Title: {info.get('title', 'Unknown')[:50]}...")
        else:
            print("   ⚠️  Retrieved info but it's empty")
            
except Exception as e:
    print(f"   ❌ yt-dlp test failed: {str(e)}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nIf all checks pass, you can run: python app_fixed.py")
print("=" * 60)