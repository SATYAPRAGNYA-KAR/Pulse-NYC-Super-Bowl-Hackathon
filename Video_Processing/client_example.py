"""
Example client script to interact with the video processing API
"""

import requests
import json
import time
import sys
from sseclient import SSEClient

# API Configuration
API_BASE_URL = "http://localhost:5000"  # Change to your PythonAnywhere URL


def start_processing(video_url):
    """Start processing a video"""
    print(f"Starting processing for: {video_url}")
    
    response = requests.post(
        f"{API_BASE_URL}/start_processing",
        json={"video_url": video_url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Session started: {data['session_id']}")
        return data['session_id']
    else:
        print(f"Error: {response.text}")
        return None


def stream_results(session_id):
    """Stream processed chunks in real-time using SSE"""
    print(f"\nStreaming results for session: {session_id}")
    print("-" * 80)
    
    url = f"{API_BASE_URL}/stream/{session_id}"
    
    try:
        messages = SSEClient(url)
        
        for msg in messages:
            if msg.data:
                try:
                    data = json.loads(msg.data)
                    
                    if 'error' in data:
                        print(f"Error: {data['error']}")
                        break
                    
                    if data.get('status') == 'complete':
                        print("\n✓ Processing complete!")
                        break
                    
                    # Display chunk information
                    chunk_idx = data.get('chunk_index')
                    timestamp = data.get('timestamp')
                    transcript = data.get('transcript', {}).get('text', '')
                    amplitudes = data.get('amplitudes', [])
                    
                    print(f"\nChunk {chunk_idx} (@ {timestamp}s):")
                    print(f"  Transcript: {transcript[:100]}...")
                    print(f"  Amplitude samples: {len(amplitudes)}")
                    
                    # Show max amplitude (excitement indicator)
                    if amplitudes:
                        max_amp = max(amplitudes)
                        print(f"  Max amplitude: {max_amp:.3f} {'🔥' if max_amp > 0.8 else ''}")
                    
                except json.JSONDecodeError:
                    pass  # Keepalive messages
                    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\nError streaming results: {str(e)}")


def get_chunk(session_id, chunk_index):
    """Get a specific processed chunk"""
    response = requests.get(f"{API_BASE_URL}/get_chunk/{session_id}/{chunk_index}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting chunk: {response.text}")
        return None


def stop_processing(session_id):
    """Stop processing a session"""
    response = requests.post(f"{API_BASE_URL}/stop_processing/{session_id}")
    
    if response.status_code == 200:
        print(f"Session {session_id} stopped")
    else:
        print(f"Error stopping session: {response.text}")


def check_health():
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"API Status: {data['status']}")
            print(f"Active sessions: {data['active_sessions']}")
            return True
        return False
    except:
        print("API is not reachable")
        return False


def example_usage():
    """Example usage of the API"""
    
    # Check if API is running
    print("Checking API health...")
    if not check_health():
        print("\nError: API is not running. Start the Flask server first!")
        return
    
    print("\n" + "="*80)
    print("VIDEO PROCESSING PIPELINE - EXAMPLE CLIENT")
    print("="*80)
    
    # Example YouTube URL (you can replace with any YouTube URL)
    video_url = input("\nEnter YouTube URL (or press Enter for example): ").strip()
    
    if not video_url:
        # Example: Super Bowl highlights
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with actual Super Bowl video
        print(f"Using example URL: {video_url}")
    
    # Start processing
    session_id = start_processing(video_url)
    
    if not session_id:
        return
    
    # Stream results
    try:
        stream_results(session_id)
    except KeyboardInterrupt:
        print("\n\nStopping session...")
        stop_processing(session_id)


def batch_example():
    """Example of processing multiple chunks at once"""
    
    print("\nBatch Processing Example")
    print("-" * 80)
    
    video_url = input("Enter YouTube URL: ").strip()
    
    if not video_url:
        print("No URL provided")
        return
    
    session_id = start_processing(video_url)
    
    if not session_id:
        return
    
    print("\nWaiting for chunks to process...")
    time.sleep(10)  # Wait for some chunks to process
    
    # Get first 3 chunks
    for i in range(3):
        chunk = get_chunk(session_id, i)
        if chunk:
            print(f"\nChunk {i}:")
            print(f"  Text: {chunk['transcript']['text'][:100]}...")
        else:
            print(f"Chunk {i} not ready yet")


if __name__ == "__main__":
    print("""
Choose an option:
1. Standard example (stream results in real-time)
2. Batch example (get specific chunks)
3. Health check only
    """)
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        example_usage()
    elif choice == "2":
        batch_example()
    elif choice == "3":
        check_health()
    else:
        print("Invalid choice")