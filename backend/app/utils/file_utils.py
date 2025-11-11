import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import ffmpeg


def get_video_files(videos_dir: str) -> List[Path]:
    """
    Scan directory for video files
    
    Args:
        videos_dir: Path to videos directory
    
    Returns:
        List of video file paths
    """
    videos_path = Path(videos_dir)
    
    if not videos_path.exists():
        return []
    
    # Supported video extensions
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}
    
    video_files = []
    for file_path in videos_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            video_files.append(file_path)
    
    # Sort by modification time (newest first)
    video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return video_files


def get_video_duration(video_path: str) -> Optional[float]:
    """
    Get video duration in seconds using ffprobe
    
    Args:
        video_path: Path to video file
    
    Returns:
        Duration in seconds or None if unable to determine
    """
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
            None
        )
        if video_stream:
            duration = float(video_stream.get('duration', 0))
            if duration > 0:
                return duration
        
        # Fallback to format duration
        if 'format' in probe and 'duration' in probe['format']:
            return float(probe['format']['duration'])
        
        return None
    
    except Exception as e:
        print(f"Error getting video duration: {str(e)}")
        return None


def validate_video_constraints(
    video_path: str,
    max_size_mb: int = 100,
    max_duration_sec: int = 300
) -> tuple[bool, Optional[str]]:
    """
    Validate video against size and duration constraints
    
    Args:
        video_path: Path to video file
        max_size_mb: Maximum file size in MB
        max_duration_sec: Maximum duration in seconds
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    file_path = Path(video_path)
    
    if not file_path.exists():
        return False, "Video file not found"
    
    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"Video size ({file_size_mb:.1f}MB) exceeds limit of {max_size_mb}MB"
    
    # Check duration
    duration = get_video_duration(video_path)
    if duration and duration > max_duration_sec:
        return False, f"Video duration ({duration:.1f}s) exceeds limit of {max_duration_sec}s"
    
    return True, None


def extract_model_from_caption_filename(caption_filename: str) -> Optional[str]:
    """
    Extract model name from caption filename
    Format: video.mp4_modelname.json
    
    Args:
        caption_filename: Caption file name
    
    Returns:
        Model name or None
    """
    # Pattern: {video_name}_{model}.json
    match = re.search(r'_([^_]+)\.json$', caption_filename)
    if match:
        return match.group(1)
    return None


def find_caption_for_video(
    video_filename: str,
    captions_dir: str,
    model_name: Optional[str] = None
) -> Optional[Path]:
    """
    Find caption file for a video
    
    Args:
        video_filename: Video filename
        captions_dir: Captions directory path
        model_name: Specific model name to look for (optional)
    
    Returns:
        Path to caption file or None
    """
    captions_path = Path(captions_dir)
    
    if not captions_path.exists():
        return None
    
    # If model specified, look for exact match
    if model_name:
        caption_path = captions_path / f"{video_filename}_{model_name}.json"
        if caption_path.exists():
            return caption_path
        return None
    
    # Otherwise, find any caption for this video
    pattern = f"{video_filename}_*.json"
    matches = list(captions_path.glob(pattern))
    
    if matches:
        # Return the most recently modified caption
        matches.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return matches[0]
    
    return None


def get_audio_filename(video_filename: str) -> str:
    """
    Convert video filename to WAV audio filename
    
    Args:
        video_filename: Video filename (e.g., "example.mp4")
    
    Returns:
        Audio filename with .wav extension (e.g., "example.wav")
    """
    video_path = Path(video_filename)
    return video_path.with_suffix('.wav').name


def check_audio_exists(video_filename: str, videos_dir: str) -> bool:
    """
    Check if audio file exists for a video
    
    Args:
        video_filename: Video filename
        videos_dir: Videos directory path
    
    Returns:
        True if audio file exists, False otherwise
    """
    videos_path = Path(videos_dir)
    audio_filename = get_audio_filename(video_filename)
    audio_path = videos_path / audio_filename
    
    return audio_path.exists() and audio_path.is_file()


def extract_audio_to_wav(video_path: str, output_path: str) -> str:
    """
    Extract audio from video file and convert to WAV format
    
    Args:
        video_path: Path to input video file
        output_path: Path to output WAV file
    
    Returns:
        Path to output WAV file
    
    Raises:
        Exception: If video has no audio track or extraction fails
    """
    import ffmpeg
    
    video_file = Path(video_path)
    
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Check if video has audio track
    try:
        probe = ffmpeg.probe(video_path)
        audio_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
        
        if not audio_streams:
            raise ValueError("Video has no audio track")
    except Exception as e:
        if "no audio track" in str(e).lower() or "Video has no audio track" in str(e):
            raise ValueError("Video has no audio track")
        # If probe fails for other reasons, continue and let ffmpeg handle it
    
    try:
        # Extract audio and convert to WAV
        # -vn: disable video
        # -acodec pcm_s16le: PCM 16-bit little-endian (standard WAV)
        # -ar 44100: sample rate 44.1kHz (CD quality)
        # -ac 2: stereo (2 channels)
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                vn=None,  # No video
                acodec='pcm_s16le',  # WAV codec
                ar=44100,  # Sample rate
                ac=2  # Stereo
            )
            .overwrite_output()  # Overwrite if exists
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
        
        # Verify output file was created
        output_file = Path(output_path)
        if not output_file.exists():
            raise Exception("Audio extraction completed but output file not found")
        
        return output_path
    
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        # Check for common error messages
        if "no audio stream" in error_msg.lower() or "does not contain any stream" in error_msg.lower():
            raise ValueError("Video has no audio track")
        raise Exception(f"FFmpeg error: {error_msg}")
    except Exception as e:
        if "no audio track" in str(e).lower() or "Video has no audio track" in str(e):
            raise ValueError("Video has no audio track")
        raise Exception(f"Failed to extract audio: {str(e)}")





