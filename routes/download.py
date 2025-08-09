from fastapi import APIRouter, HTTPException
from services.yt_service import get_video_info

router = APIRouter()

@router.get("/download")
async def get_download_url(url: str, format_id: str = None):
    video = get_video_info(url)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    # seleccionar formato por format_id si es provisto
    if format_id:
        for f in video.formats:
            if f.format_id == format_id:
                return {"success": True, "download_url": f.url}
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    # fallback: best_video_url
    if video.best_video_url:
        return {"success": True, "download_url": video.best_video_url}
    raise HTTPException(status_code=404, detail="No se encontró URL de descarga")
