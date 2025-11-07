from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional
import os
from pathlib import Path

from ..schemas.video_schema import VideoInfo, CaptionResponse
from ..services.caption_service import CaptionService
from ..services.model_client import get_available_models
from ..utils.file_utils import (
    get_video_files,
    get_video_duration,
    validate_video_constraints,
    extract_model_from_caption_filename
)

router = APIRouter(prefix="/api/videos", tags=["videos"])

# Configuration from environment
VIDEOS_DIR = os.getenv("VIDEOS_DIR", "/app/videos")
CAPTIONS_DIR = os.getenv("CAPTIONS_DIR", "/app/captions")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-omni")
REMOTE_VIDEO_URL = os.getenv("REMOTE_VIDEO_URL", "http://localhost:8080")
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
MAX_VIDEO_DURATION_SEC = int(os.getenv("MAX_VIDEO_DURATION_SEC", "300"))

# Initialize caption service
caption_service = CaptionService(
    videos_dir=VIDEOS_DIR,
    captions_dir=CAPTIONS_DIR,
    model_name=MODEL_NAME
)


@router.get("/available-models")
async def list_available_models():
    """
    List all available AI models for caption generation
    """
    return {
        "models": get_available_models(),
        "default": os.getenv("DEFAULT_MODEL", "qwen2vl")
    }


@router.get("", response_model=List[VideoInfo])
async def list_videos():
    """
    List all videos in the videos directory with their caption status
    """
    video_files = get_video_files(VIDEOS_DIR)
    videos_info = []
    
    for video_path in video_files:
        filename = video_path.name
        
        # Get file info
        file_size = video_path.stat().st_size
        duration = get_video_duration(str(video_path))
        created_at = video_path.stat().st_mtime
        
        # Check for captions from all models
        all_captions = caption_service.load_all_captions(filename)
        has_caption = len(all_captions) > 0
        
        # Get comma-separated list of models that have captions
        model_used = ','.join([c['model_key'] for c in all_captions]) if all_captions else None
        
        # Use first caption's text for preview
        caption_text = all_captions[0]['caption'] if all_captions else None
        
        video_info = VideoInfo(
            filename=filename,
            size=file_size,
            duration=duration,
            has_caption=has_caption,
            caption_text=caption_text,
            model_used=model_used,
            created_at=created_at
        )
        
        videos_info.append(video_info)
    
    return videos_info


@router.get("/{filename}")
async def get_video_info(filename: str):
    """Get information about a specific video"""
    video_path = Path(VIDEOS_DIR) / filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get file info
    file_size = video_path.stat().st_size
    duration = get_video_duration(str(video_path))
    created_at = video_path.stat().st_mtime
    
    # Check caption
    caption_data = caption_service.load_caption(filename)
    has_caption = caption_data is not None
    
    return VideoInfo(
        filename=filename,
        size=file_size,
        duration=duration,
        has_caption=has_caption,
        caption_text=caption_data.get("caption") if caption_data else None,
        model_used=caption_data.get("model_name") if caption_data else None,
        created_at=created_at
    )


@router.get("/{filename}/stream")
async def stream_video(filename: str):
    """Stream video file from local filesystem"""
    video_path = Path(VIDEOS_DIR) / filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found in local storage")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=filename
    )


@router.post("/{filename}/caption", response_model=CaptionResponse)
async def generate_caption(
    filename: str,
    prompt: Optional[str] = None,
    model: str = Query("qwen2vl", description="Model to use (qwen2vl or omnivinci)"),
    regenerate: bool = Query(False, description="Regenerate even if caption exists")
):
    """
    Generate or regenerate caption for a video
    
    Args:
        filename: Video filename
        prompt: Optional custom prompt for caption generation
        model: Model to use for generation (qwen2vl or omnivinci)
        regenerate: If True, regenerate caption even if it exists
    """
    video_path = Path(VIDEOS_DIR) / filename
    
    # Validate video exists
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate video constraints
    is_valid, error_msg = validate_video_constraints(
        str(video_path),
        max_size_mb=MAX_VIDEO_SIZE_MB,
        max_duration_sec=MAX_VIDEO_DURATION_SEC
    )
    
    if not is_valid:
        raise HTTPException(status_code=413, detail=error_msg)
    
    # Generate caption with selected model
    try:
        caption_data = await caption_service.generate_caption(
            video_filename=filename,
            prompt=prompt,
            model_key=model,
            regenerate=regenerate
        )
        
        return CaptionResponse(**caption_data)
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        error_detail = str(e)
        
        # Determine appropriate status code
        if "timed out" in error_detail.lower():
            status_code = 504
        elif "service" in error_detail.lower():
            status_code = 503
        else:
            status_code = 500
        
        raise HTTPException(status_code=status_code, detail=error_detail)


@router.get("/{filename}/all-captions")
async def get_all_captions(filename: str):
    """Get all captions from all models for a video"""
    all_captions = caption_service.load_all_captions(filename)
    
    return {
        "filename": filename,
        "captions": all_captions,
        "count": len(all_captions)
    }


@router.get("/{filename}/caption", response_model=CaptionResponse)
async def get_caption(filename: str):
    """Get existing caption for a video (returns first available)"""
    caption_data = caption_service.load_caption(filename)
    
    if not caption_data:
        raise HTTPException(
            status_code=404,
            detail="Caption not found. Generate one first."
        )
    
    return CaptionResponse(**caption_data)


@router.delete("/{filename}/caption")
async def delete_caption(filename: str):
    """Delete caption for a video"""
    success = caption_service.delete_caption(filename)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Caption not found"
        )
    
    return {"message": "Caption deleted successfully", "filename": filename}


