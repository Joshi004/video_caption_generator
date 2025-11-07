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





