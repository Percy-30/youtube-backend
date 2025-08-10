from fastapi import APIRouter, HTTPException
from models.video_info import ExtractRequest, ExtractResponse, PlaylistExtractResponse
from services.yt_service import get_video_info, get_playlist_info

router = APIRouter()

@router.post("/extract/video", response_model=ExtractResponse)
async def extract_video(req: ExtractRequest):
    video = get_video_info(req.url, req.extract_audio, req.quality)
    if video:
        return ExtractResponse(success=True, message="Video extraído", data=video, processing_time=0.0)
    raise HTTPException(status_code=404, detail="No se pudo extraer el video")

@router.post("/extract/playlist", response_model=PlaylistExtractResponse)
async def extract_playlist(url: str, max_videos: int = 20):
    pl = get_playlist_info(url, max_videos)
    if pl:
        return PlaylistExtractResponse(success=True, message="Playlist extraída", data=pl, processing_time=0.0)
    raise HTTPException(status_code=404, detail="No se pudo extraer la playlist")

