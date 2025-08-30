import os
import sys
import subprocess
import whisper
from pydub import AudioSegment
from pydub.silence import split_on_silence
import json
import re
from datetime import timedelta
from langdetect import detect, DetectorFactory
from .mongodb_storage import mongodb_storage
import tempfile
import logging

logger = logging.getLogger(__name__)

# Set seed for consistent language detection
DetectorFactory.seed = 0

class VideoToSRTConverterWhisper:
    def __init__(self, model_size="base"):
        """
        Initialize with Whisper model
        model_size options: "tiny", "base", "small", "medium", "large"
        """
        logger.info(f"Loading Whisper model: {model_size}")
        try:
            self.model = whisper.load_model(model_size)
            logger.info(f"Whisper model {model_size} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
        
    def mp4_to_mp3(self, input_file_id, output_filename=None):
        """
        Convert MP4 video to MP3 audio using ffmpeg from GridFS
        """
        if output_filename is None:
            output_filename = f"temp_audio_{os.urandom(8).hex()}.mp3"
        
        try:
            # Check if ffmpeg is installed
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg is not installed")
            return None
        
        temp_input = None
        temp_output = None
        
        try:
            # Get video file from GridFS
            video_content = mongodb_storage.get_file_content(input_file_id)
            if not video_content:
                logger.error(f"Could not retrieve video file {input_file_id} from GridFS")
                return None
            
            # Create temporary input file
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_input.write(video_content)
            temp_input.close()
            
            # Create temporary output file
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_output.close()
            
            # Convert MP4 to MP3
            cmd = [
                'ffmpeg', '-i', temp_input.name,
                '-vn',  # No video
                '-acodec', 'mp3',
                '-ab', '192k',  # Bitrate
                '-ar', '16000',  # Sample rate (Whisper works best with 16kHz)
                '-y',  # Overwrite output file
                temp_output.name
            ]
            
            logger.info(f"Converting video to MP3...")
            subprocess.run(cmd, check=True, capture_output=True)
            
            if os.path.exists(temp_output.name):
                # Read converted file and store in GridFS
                with open(temp_output.name, 'rb') as f:
                    from django.core.files.base import ContentFile
                    content = ContentFile(f.read())
                    content.name = output_filename
                    content.content_type = 'audio/mpeg'
                    
                    # Save to GridFS
                    mp3_file_id = mongodb_storage._save(output_filename, content)
                    
                    logger.info(f"Successfully converted to MP3 and stored in GridFS: {mp3_file_id}")
                    return mp3_file_id
            else:
                logger.error("MP3 output file was not created")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during MP4 to MP3 conversion: {e}")
            return None
        finally:
            # Clean up temporary files
            if temp_input and os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            if temp_output and os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
    
    def transcribe_audio(self, audio_file_id):
        """
        Transcribe audio file from GridFS using Whisper
        """
        logger.info("Transcribing audio with Whisper...")
        
        temp_audio = None
        try:
            # Get audio file from GridFS
            audio_content = mongodb_storage.get_file_content(audio_file_id)
            if not audio_content:
                logger.error(f"Could not retrieve audio file {audio_file_id} from GridFS")
                return None
            
            # Create temporary audio file
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_audio.write(audio_content)
            temp_audio.close()
            
            # Transcribe with timestamps
            result = self.model.transcribe(
                temp_audio.name,
                verbose=True,
                word_timestamps=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
        finally:
            if temp_audio and os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)
    
    def detect_language(self, text):
        """
        Detect language from transcribed text
        """
        try:
            if not text or len(text.strip()) < 10:
                return "unknown"
            
            # Clean text for better detection
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            if len(clean_text) < 5:
                return "unknown"
            
            detected_lang = detect(clean_text)
            
            # Map language codes to readable names
            language_map = {
                'en': 'English',
                'hi': 'Hindi',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese',
                'ar': 'Arabic',
                'bn': 'Bengali',
                'ur': 'Urdu',
                'te': 'Telugu',
                'ta': 'Tamil',
                'ml': 'Malayalam',
                'kn': 'Kannada',
                'gu': 'Gujarati',
                'pa': 'Punjabi',
                'mr': 'Marathi',
                'or': 'Odia',
                'as': 'Assamese',
                'ne': 'Nepali',
                'si': 'Sinhala',
                'my': 'Burmese',
                'th': 'Thai',
                'vi': 'Vietnamese',
                'id': 'Indonesian',
                'ms': 'Malay',
                'tl': 'Tagalog',
                'fa': 'Persian',
                'tr': 'Turkish',
                'he': 'Hebrew',
                'pl': 'Polish',
                'cs': 'Czech',
                'sk': 'Slovak',
                'hu': 'Hungarian',
                'ro': 'Romanian',
                'bg': 'Bulgarian',
                'hr': 'Croatian',
                'sr': 'Serbian',
                'sl': 'Slovenian',
                'et': 'Estonian',
                'lv': 'Latvian',
                'lt': 'Lithuanian',
                'fi': 'Finnish',
                'sv': 'Swedish',
                'da': 'Danish',
                'no': 'Norwegian',
                'is': 'Icelandic',
                'nl': 'Dutch',
                'af': 'Afrikaans',
                'sw': 'Swahili',
                'zu': 'Zulu',
                'xh': 'Xhosa',
                'yo': 'Yoruba',
                'ig': 'Igbo',
                'ha': 'Hausa',
                'am': 'Amharic',
                'so': 'Somali',
                'ku': 'Kurdish',
                'ps': 'Pashto',
                'uz': 'Uzbek',
                'kk': 'Kazakh',
                'ky': 'Kyrgyz',
                'tg': 'Tajik',
                'mn': 'Mongolian',
                'ka': 'Georgian',
                'hy': 'Armenian',
                'az': 'Azerbaijani',
                'be': 'Belarusian',
                'uk': 'Ukrainian',
                'mk': 'Macedonian',
                'sq': 'Albanian',
                'mt': 'Maltese',
                'cy': 'Welsh',
                'ga': 'Irish',
                'gd': 'Scottish Gaelic',
                'br': 'Breton',
                'eu': 'Basque',
                'ca': 'Catalan',
                'gl': 'Galician',
                'oc': 'Occitan',
                'co': 'Corsican',
                'fur': 'Friulian',
                'sc': 'Sardinian',
                'vec': 'Venetian',
                'lmo': 'Lombard',
                'pms': 'Piedmontese',
                'rm': 'Romansh',
                'lad': 'Ladino',
                'jv': 'Javanese',
                'su': 'Sundanese',
                'ceb': 'Cebuano',
                'war': 'Waray',
                'ilo': 'Ilocano',
                'pam': 'Kapampangan',
                'bcl': 'Central Bikol',
                'hil': 'Hiligaynon',
                'cbk': 'Chavacano',
                'kha': 'Khasi',
                'mni': 'Manipuri',
                'sat': 'Santali',
                'doi': 'Dogri',
                'ks': 'Kashmiri',
                'sd': 'Sindhi',
                'bal': 'Balochi',
                'ps': 'Pashto',
                'dari': 'Dari',
                'uz': 'Uzbek',
                'tk': 'Turkmen',
                'ug': 'Uyghur',
                'bo': 'Tibetan',
                'dz': 'Dzongkha',
                'my': 'Burmese',
                'lo': 'Lao',
                'km': 'Khmer',
                'th': 'Thai',
                'vi': 'Vietnamese',
                'id': 'Indonesian',
                'ms': 'Malay',
                'tl': 'Tagalog',
                'ceb': 'Cebuano',
                'war': 'Waray',
                'ilo': 'Ilocano',
                'pam': 'Kapampangan',
                'bcl': 'Central Bikol',
                'hil': 'Hiligaynon',
                'cbk': 'Chavacano',
                'jv': 'Javanese',
                'su': 'Sundanese',
                'min': 'Minangkabau',
                'ace': 'Acehnese',
                'ban': 'Balinese',
                'mad': 'Madurese',
                'sun': 'Sundanese',
                'jav': 'Javanese',
                'bug': 'Buginese',
                'mak': 'Makassarese',
                'gor': 'Gorontalo',
                'min': 'Minangkabau',
                'ace': 'Acehnese',
                'ban': 'Balinese',
                'mad': 'Madurese',
                'sun': 'Sundanese',
                'jav': 'Javanese',
                'bug': 'Buginese',
                'mak': 'Makassarese',
                'gor': 'Gorontalo'
            }
            
            return language_map.get(detected_lang, detected_lang.upper())
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return "unknown"
    
    def format_time(self, seconds):
        """
        Convert seconds to SRT time format (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        seconds = seconds % 3600
        minutes = int(seconds // 60)
        seconds = seconds % 60
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def generate_srt_from_whisper(self, transcription_result, output_filename=None):
        """
        Generate SRT file from Whisper transcription result and store in GridFS
        """
        logger.info("Generating SRT file from Whisper transcription...")
        
        if output_filename is None:
            output_filename = f"subtitles_{os.urandom(8).hex()}.srt"
        
        try:
            # Create temporary SRT file
            temp_srt = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.srt', encoding='utf-8')
            
            subtitle_index = 1
            
            # Process segments from Whisper
            for segment in transcription_result['segments']:
                start_time = segment['start']
                end_time = segment['end']
                text = segment['text'].strip()
                
                if text:  # Only add subtitle if there's text
                    # Format timestamps
                    start_formatted = self.format_time(start_time)
                    end_formatted = self.format_time(end_time)
                    
                    # Write SRT format
                    temp_srt.write(f"{subtitle_index}\n")
                    temp_srt.write(f"{start_formatted} --> {end_formatted}\n")
                    temp_srt.write(f"{text}\n\n")
                    
                    subtitle_index += 1
            
            temp_srt.close()
            
            # Read the SRT file and store in GridFS
            with open(temp_srt.name, 'rb') as f:
                from django.core.files.base import ContentFile
                content = ContentFile(f.read())
                content.name = output_filename
                content.content_type = 'text/plain'
                
                # Save to GridFS
                srt_file_id = mongodb_storage._save(output_filename, content)
                
                logger.info(f"SRT file generated and stored in GridFS: {srt_file_id}")
                return srt_file_id
                
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}")
            return None
        finally:
            if temp_srt and os.path.exists(temp_srt.name):
                os.unlink(temp_srt.name)
    
    def process_video_to_srt(self, input_file_id, model_size="base"):
        """
        Main function to process video: MP4 -> MP3 -> SRT using Whisper
        Returns: dict with file_ids, language, and status
        """
        try:
            # Step 1: Convert MP4 to MP3
            mp3_file_id = self.mp4_to_mp3(input_file_id)
            if not mp3_file_id:
                return {
                    'success': False,
                    'error': 'Failed to convert video to MP3'
                }
            
            # Step 2: Transcribe audio with Whisper
            transcription_result = self.transcribe_audio(mp3_file_id)
            if not transcription_result:
                return {
                    'success': False,
                    'error': 'Failed to transcribe audio'
                }
            
            # Step 3: Detect language
            full_text = ' '.join([segment['text'] for segment in transcription_result['segments']])
            detected_language = self.detect_language(full_text)
            
            # Step 4: Generate SRT file
            srt_file_id = self.generate_srt_from_whisper(transcription_result)
            if not srt_file_id:
                return {
                    'success': False,
                    'error': 'Failed to generate SRT file'
                }
            
            return {
                'success': True,
                'mp3_file_id': mp3_file_id,
                'srt_file_id': srt_file_id,
                'language': detected_language,
                'transcription_text': full_text,
                'segments_count': len(transcription_result['segments'])
            }
            
        except Exception as e:
            logger.error(f"Error processing video to SRT: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
srt_converter = VideoToSRTConverterWhisper()
