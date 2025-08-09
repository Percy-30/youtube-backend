from fastapi import APIRouter

router = APIRouter()

@router.get("/trending")
async def trending(region: str = "US"):
    # Placeholder: podrías usar yt-dlp o scraping para trending
    return {"success": True, "region": region, "trending_videos": []}
