"""
Test script to verify installation and basic functionality
"""

import sys
import subprocess
import importlib


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False


def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} installed")
        return True
    except ImportError:
        print(f"✗ {package_name} NOT installed")
        return False


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("Checking FFmpeg...")
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ {version_line}")
            return True
        else:
            print("✗ FFmpeg not working properly")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg NOT installed")
        print("  Install: sudo apt-get install ffmpeg (Ubuntu)")
        print("  Install: brew install ffmpeg (macOS)")
        return False
    except Exception as e:
        print(f"✗ Error checking FFmpeg: {str(e)}")
        return False


def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")
    import os
    
    dirs = ['uploads', 'chunks', 'audio', 'processed']
    all_exist = True
    
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"✓ {dir_name}/ exists")
        else:
            print(f"○ {dir_name}/ will be created")
            os.makedirs(dir_name, exist_ok=True)
    
    return True


def test_whisper_model():
    """Test loading Whisper model"""
    print("\nTesting Whisper model...")
    try:
        import whisper
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Device: {device}")
        
        print("  Loading whisper-tiny model...")
        model = whisper.load_model("tiny", device=device)
        print("✓ Whisper model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Error loading Whisper: {str(e)}")
        return False


def test_audio_processing():
    """Test audio processing libraries"""
    print("\nTesting audio processing...")
    try:
        import librosa
        import numpy as np
        
        # Create a simple test signal
        sr = 16000
        duration = 1
        t = np.linspace(0, duration, sr * duration)
        y = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Test RMS calculation
        rms = librosa.feature.rms(y=y)
        
        print("✓ Audio processing libraries working")
        return True
    except Exception as e:
        print(f"✗ Error in audio processing: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("SYSTEM CHECK - Video Processing Pipeline")
    print("="*60)
    
    results = []
    
    # Python version
    results.append(("Python version", check_python_version()))
    
    print("\nChecking Python packages...")
    # Core packages
    results.append(("Flask", check_package("flask", "flask")))
    results.append(("Flask-CORS", check_package("flask-cors", "flask_cors")))
    
    # Video/Audio processing
    results.append(("yt-dlp", check_package("yt-dlp", "yt_dlp")))
    results.append(("librosa", check_package("librosa", "librosa")))
    results.append(("scipy", check_package("scipy", "scipy")))
    
    # AI/ML
    results.append(("OpenAI Whisper", check_package("openai-whisper", "whisper")))
    results.append(("torch", check_package("torch", "torch")))
    results.append(("transformers", check_package("transformers", "transformers")))
    
    # System tools
    results.append(("FFmpeg", check_ffmpeg()))
    
    # Directories
    results.append(("Directories", check_directories()))
    
    # Functional tests
    results.append(("Whisper model", test_whisper_model()))
    results.append(("Audio processing", test_audio_processing()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! System ready.")
        print("\nNext steps:")
        print("  1. python app.py          # Start the Flask server")
        print("  2. python client_example.py  # Test with example client")
    else:
        print("\n✗ Some checks failed. Please install missing dependencies.")
        print("\nTo install all dependencies:")
        print("  pip install -r requirements.txt")
        print("\nTo install FFmpeg:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
    
    return passed == total


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test video processing pipeline setup')
    parser.add_argument('--quick', action='store_true', help='Skip model loading tests')
    args = parser.parse_args()
    
    if args.quick:
        print("Running quick check (skipping model tests)...\n")
        # Run subset of tests
        check_python_version()
        check_ffmpeg()
        check_directories()
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)