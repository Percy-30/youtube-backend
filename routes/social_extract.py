from fastapi import APIRouter, Query, Header, HTTPException
from typing import Optional

from utils.headers import DESKTOP_HEADERS, MOBILE_HEADERS, FACEBOOK_HEADERS, FACEBOOK_MOBILE_HEADERS

from utils.url_utils import validate_url, get_platform_from_url

from services.tiktok_service import handle_tiktok
from services.facebook_service import handle_facebook
from services.youtube_service import handle_youtube

router = APIRouter()

@router.get("/video")
async def get_video_info(
    url: str = Query(...),
    prefer_mobile: bool = Query(False),
    cookies: Optional[str] = Header(None),
    force_ytdlp: bool = Query(False)
):
    validate_url(url)
    platform = get_platform_from_url(url)

    if platform == "tiktok":
        info = await handle_tiktok(url)
    elif platform == "facebook":
        headers = FACEBOOK_MOBILE_HEADERS if prefer_mobile else FACEBOOK_HEADERS
        info = await handle_facebook(url, headers)
    elif platform == "youtube":
        info = await handle_youtube(url, cookies, force_ytdlp)
    else:
        raise HTTPException(400, "Plataforma no soportada")

    if not info:
        raise HTTPException(404, "No se pudo extraer la información del video")

    return info