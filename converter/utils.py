import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from django.conf import settings
from .mongodb_storage import mongodb_storage
import logging

logger = logging.getLogger(__name__)

class VideoConverter:
    """Utility class for converting video files to audio using MongoDB storage"""
    
    def __init__(self):
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        self.supported_audio_formats = ['.mp3', '.wav', '.aac', '.ogg']
    
    def is_video_file(self, filename):
        """Check if file is a supported video format"""
        return Path(filename).suffix.lower() in self.supported_video_formats
    
    def is_audio_file(self, filename):
        """Check if file is a supported audio format"""
        return Path(filename).suffix.lower() in self.supported_audio_formats
    
    def convert_video_to_mp3(self, input_file_id, output_filename=None):
        """
        Convert video file to MP3 using ffmpeg
        
        Args:
            input_file_id: GridFS file ID of input video
            output_filename: Name for output MP3 file (optional)
            
        Returns:
            str: GridFS file ID of converted MP3 file or None if failed
        """
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg is not installed or not in PATH")
            return None
        
        # Create temporary files for processing
        temp_input = None
        temp_output = None
        
        try:
            # Get input file from GridFS
            input_content = mongodb_storage.get_file_content(input_file_id)
            if not input_content:
                logger.error(f"Could not retrieve input file {input_file_id} from GridFS")
                return None
            
            # Create temporary input file
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_input.write(input_content)
            temp_input.close()
            
            # Create temporary output file
            if output_filename is None:
                output_filename = f"converted_{uuid.uuid4().hex}.mp3"
            
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_output.close()
            
            # FFmpeg command for video to MP3 conversion
            cmd = [
                'ffmpeg',
                '-i', temp_input.name,
                '-vn',  # No video
                '-acodec', 'libmp3lame',  # MP3 codec
                '-ab', '192k',  # Bitrate
                '-ar', '44100',  # Sample rate
                '-y',  # Overwrite output file
                temp_output.name
            ]
            
            logger.info(f"Converting video to MP3...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if os.path.exists(temp_output.name):
                # Read converted file and store in GridFS
                with open(temp_output.name, 'rb') as f:
                    from django.core.files.base import ContentFile
                    content = ContentFile(f.read())
                    content.name = output_filename
                    content.content_type = 'audio/mpeg'
                    
                    # Save to GridFS
                    output_file_id = mongodb_storage._save(output_filename, content)
                    
                    logger.info(f"Successfully converted to MP3 and stored in GridFS: {output_file_id}")
                    return output_file_id
            else:
                logger.error("Output file was not created")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {e}")
            return None
        finally:
            # Clean up temporary files
            if temp_input and os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            if temp_output and os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
    
    def get_video_info(self, file_id):
        """
        Get video file information using ffprobe
        
        Args:
            file_id: GridFS file ID
            
        Returns:
            dict: Video information or None if failed
        """
        temp_file = None
        try:
            # Get file content from GridFS
            content = mongodb_storage.get_file_content(file_id)
            if not content:
                return None
            
            # Create temporary file for ffprobe
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_file.write(content)
            temp_file.close()
            
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                temp_file.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            return json.loads(result.stdout)
            
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get video info: {e}")
            return None
        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def create_temp_file(self, suffix='.mp3'):
        """Create a temporary file with the given suffix"""
        return tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name
    
    def cleanup_temp_file(self, file_path):
        """Remove temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {e}")

# Global instance
video_converter = VideoConverter()
