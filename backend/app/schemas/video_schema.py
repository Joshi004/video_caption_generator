from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VideoInfo(BaseModel):
    """Video information schema"""
    filename: str
    size: int  # Size in bytes
    duration: Optional[float] = None  # Duration in seconds
    has_caption: bool = False
    caption_text: Optional[str] = None
    model_used: Optional[str] = None
    created_at: Optional[datetime] = None


class CaptionResponse(BaseModel):
    """Caption response schema"""
    filename: str
    caption: str
    prompt: str  # Prompt used to generate the caption
    generated_at: datetime
    processing_time_seconds: float
    model_name: str
    model_version: str = "nvidia/omnivinci"


class CaptionGenerateRequest(BaseModel):
    """Caption generation request"""
    prompt: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    backend_healthy: bool
    model_service_healthy: bool
    model_service_url: str





