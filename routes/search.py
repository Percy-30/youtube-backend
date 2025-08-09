from fastapi import APIRouter, HTTPException, Query
from services.yt_service import search

router = APIRouter()

@router.get("/search")
async def search_videos(q: str = Query(...), max_results: int = Query(10, ge=1, le=50)):
    try:
        results = search(q, max_results)
        return {"success": True, "query": q, "results": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
