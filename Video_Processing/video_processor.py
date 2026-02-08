"""
Video processing module
Handles video downloading, chunking, and metadata extraction
"""

import os
import subprocess
import logging
from pathlib import Path
import yt_dlp

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video download and chunking operations"""
    
    def __init__(self, chunks_folder, chunk_duration=5):
        self.chunks_folder = chunks_folder
        self.chunk_duration = chunk_duration
        os.makedirs(chunks_folder, exist_ok=True)
    
    
    def get_video_info(self, video_url):
        """
        Get video metadata without downloading
        """
        try:
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                logger.info(f"Getting info for YouTube video: {video_url}")
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                
                return {
                    'duration': info.get('duration', 0),
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': video_url,
                    'formats': info.get('formats', [])
                }
            else:
                # For direct URLs, try to get duration with ffprobe
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                duration = float(result.stdout.strip()) if result.returncode == 0 else 0
                
                return {
                    'duration': duration,
                    'title': 'Direct Video',
                    'thumbnail': '',
                    'url': video_url
                }
                
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None
    
    def download_chunk(self, video_url, start_time, duration=None):
        """
        Download a specific chunk of video directly from YouTube/URL
        without downloading the full video first
        
        Args:
            video_url: URL of the video
            start_time: Start time in seconds
            duration: Duration in seconds (default: self.chunk_duration)
            
        Returns:
            Path to downloaded chunk or None on error
        """
        try:
            if duration is None:
                duration = self.chunk_duration
            
            chunk_filename = f'chunk_{int(start_time)}_{int(duration)}.mp4'
            chunk_path = os.path.join(self.chunks_folder, chunk_filename)
            
            # If chunk already exists, return it
            if os.path.exists(chunk_path):
                logger.info(f"Chunk already exists: {chunk_path}")
                return chunk_path
            
            logger.info(f"Downloading chunk from {start_time}s to {start_time + duration}s")
            
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                # For YouTube, download with yt-dlp and then extract chunk
                temp_output = os.path.join(self.chunks_folder, f'temp_{int(start_time)}.mp4')
                
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': temp_output,
                    'quiet': False,
                    'no_warnings': False,
                    'external_downloader': 'ffmpeg',
                    'external_downloader_args': [
                        '-ss', str(start_time),
                        '-t', str(duration)
                    ]
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
                # Rename temp file to chunk file
                if os.path.exists(temp_output):
                    os.rename(temp_output, chunk_path)
                
            else:
                # For direct URLs, use ffmpeg to download specific chunk
                cmd = [
                    'ffmpeg',
                    '-ss', str(start_time),
                    '-i', video_url,
                    '-t', str(duration),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-preset', 'ultrafast',
                    '-y',
                    chunk_path
                ]
                
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            
            if os.path.exists(chunk_path):
                logger.info(f"Chunk downloaded successfully: {chunk_path}")
                return chunk_path
            else:
                logger.error(f"Chunk file not created: {chunk_path}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout downloading chunk at {start_time}s")
            return None
        except Exception as e:
            logger.error(f"Error downloading chunk: {str(e)}")
            return None
    
    def download_video(self, video_url, session_id):
        """
        Download video from URL (supports YouTube and direct URLs)
        """
        try:
            output_path = os.path.join('uploads', f'{session_id}_original.mp4')
            
            # Check if it's a YouTube URL
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                logger.info(f"Downloading from YouTube: {video_url}")
                
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': output_path,
                    'quiet': False,
                    'no_warnings': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
            else:
                # Direct URL download using ffmpeg
                logger.info(f"Downloading from direct URL: {video_url}")
                cmd = [
                    'ffmpeg',
                    '-i', video_url,
                    '-c', 'copy',
                    '-y',
                    output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            
            if os.path.exists(output_path):
                logger.info(f"Video downloaded successfully: {output_path}")
                return output_path
            else:
                logger.error("Download failed - file not found")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return None
    
    def get_video_duration(self, video_path):
        """
        Get video duration in seconds using ffprobe
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
            
        except Exception as e:
            logger.error(f"Error getting video duration: {str(e)}")
            return 0
    
    def create_chunk(self, video_path, chunk_index, session_id):
        """
        Create a video chunk using ffmpeg
        
        Args:
            video_path: Path to source video
            chunk_index: Index of the chunk
            session_id: Session identifier
            
        Returns:
            Path to created chunk or None on error
        """
        try:
            start_time = chunk_index * self.chunk_duration
            chunk_path = os.path.join(
                self.chunks_folder,
                f'{session_id}_chunk_{chunk_index}.mp4'
            )
            
            # Use ffmpeg to extract chunk
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', video_path,
                '-t', str(self.chunk_duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'ultrafast',  # Fast encoding for real-time
                '-y',  # Overwrite output
                chunk_path
            ]
            
            logger.info(f"Creating chunk {chunk_index} at {start_time}s")
            subprocess.run(cmd, check=True, capture_output=True)
            
            if os.path.exists(chunk_path):
                logger.info(f"Chunk created: {chunk_path}")
                return chunk_path
            else:
                logger.error(f"Chunk file not created: {chunk_path}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error creating chunk: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error creating chunk: {str(e)}")
            return None
    
    def get_video_metadata(self, video_path):
        """
        Extract video metadata using ffprobe
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            metadata = json.loads(result.stdout)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting metadata: {str(e)}")
            return None