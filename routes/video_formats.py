from fastapi import APIRouter, HTTPException
from services.yt_service import get_video_info

router = APIRouter()

@router.get("/formats")
async def get_formats(url: str):
    video = get_video_info(url)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    # devuelve la lista de formatos cruda (puedes mapear a tu modelo DownloadOption)
    return {"success": True, "formats": [f.dict() for f in video.formats] if video.formats else []}
