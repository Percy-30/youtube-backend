from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class VideoFormat(BaseModel):
    format_id: str
    ext: str
    quality: Optional[str] = None
    filesize: Optional[int] = None
    url: Optional[str] = None
    acodec: Optional[str] = None
    vcodec: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    tbr: Optional[float] = None

class VideoThumbnail(BaseModel):
    url: str
    height: Optional[int] = None
    width: Optional[int] = None
    resolution: Optional[str] = None

class VideoInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    uploader: Optional[str] = None
    uploader_id: Optional[str] = None
    upload_date: Optional[str] = None
    duration: Optional[int] = None
    duration_string: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    average_rating: Optional[float] = None
    age_limit: Optional[int] = None
    webpage_url: Optional[str] = None
    original_url: Optional[str] = None
    thumbnails: List[VideoThumbnail] = []
    formats: List[VideoFormat] = []
    best_video_url: Optional[str] = None
    best_audio_url: Optional[str] = None
    tags: List[str] = []
    categories: List[str] = []
    channel: Optional[str] = None
    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    extracted_at: datetime

class PlaylistInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    uploader: Optional[str] = None
    uploader_id: Optional[str] = None
    webpage_url: Optional[str] = None
    entries: List[VideoInfo] = []
    playlist_count: int = 0
    extracted_at: datetime

class ExtractRequest(BaseModel):
    url: str
    extract_audio: bool = False
    quality: Optional[str] = "best"

class ExtractResponse(BaseModel):
    success: bool
    message: str
    data: Optional[VideoInfo] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class PlaylistExtractResponse(BaseModel):
    success: bool
    message: str
    data: Optional[PlaylistInfo] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
