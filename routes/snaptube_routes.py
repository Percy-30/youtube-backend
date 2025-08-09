# routes/snaptube_routes.py
from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
import time
import logging

from models.snaptube_models import (
    VideoFormatsResponse, DownloadUrlResponse, DownloadRequest,
    TrendingResponse, SearchResponse, QuickInfoResponse,
    SnaptubeConverter
)
from services.youtube_handler import YouTubeExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Snaptube API"])

# Instancia del extractor
extractor = YouTubeExtractor()

@router.get("/video/info", response_model=QuickInfoResponse)
async def get_video_info(url: str = Query(..., description="URL del video de YouTube")):
    """Obtiene información rápida del video (preview estilo Snaptube)"""
    start_time = time.time()
    
    try:
        video_info = extractor.extract_video_info(url)
        processing_time = time.time() - start_time
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        snaptube_info = SnaptubeConverter.video_to_snaptube_info(video_info)
        
        return QuickInfoResponse(
            success=True,
            video=snaptube_info,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo info del video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video/formats", response_model=VideoFormatsResponse)
async def get_video_formats(url: str = Query(..., description="URL del video")):
    """Obtiene formatos disponibles estilo Snaptube"""
    start_time = time.time()
    
    try:
        video_info = extractor.extract_video_info(url)
        processing_time = time.time() - start_time
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        snaptube_info = SnaptubeConverter.video_to_snaptube_info(video_info)
        
        # Organizar formatos por calidad
        formats = {"video": {"high_quality": [], "medium_quality": [], "low_quality": [], "mobile": []}}
        
        for fmt in video_info.formats:
            if fmt.vcodec and fmt.vcodec != 'none':
                if fmt.resolution:
                    height = int(fmt.resolution.split('x')[1]) if 'x' in fmt.resolution else 0
                    if height >= 720:
                        formats["video"]["high_quality"].append(fmt.dict())
                    elif height >= 480:
                        formats["video"]["medium_quality"].append(fmt.dict())
                    elif height >= 360:
                        formats["video"]["low_quality"].append(fmt.dict())
                    else:
                        formats["video"]["mobile"].append(fmt.dict())
        
        # Generar opciones de descarga estilo Snaptube
        download_options = SnaptubeConverter.generate_download_options(video_info)
        
        return VideoFormatsResponse(
            success=True,
            video_info=snaptube_info,
            formats=formats,
            download_options=download_options,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo formatos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download", response_model=DownloadUrlResponse)
async def get_download_url(request: DownloadRequest):
    """Obtiene URL directa de descarga estilo Snaptube"""
    try:
        video_info = extractor.extract_video_info(
            url=request.url,
            extract_audio=(request.format_type == "audio"),
            quality=request.quality
        )
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        # Seleccionar URL según el tipo
        download_url = None
        if request.format_type == "audio":
            download_url = video_info.best_audio_url
        else:
            download_url = video_info.best_video_url
        
        if not download_url:
            raise HTTPException(status_code=404, detail="URL de descarga no disponible")
        
        # Estimar tamaño del archivo
        filesize_mb = None
        if video_info.duration:
            size_estimate = SnaptubeConverter.estimate_filesize(
                video_info.duration, request.quality, request.format_type
            )
            try:
                if "MB" in size_estimate:
                    filesize_mb = float(size_estimate.replace("~", "").replace("MB", ""))
            except:
                pass
        
        format_ext = "mp3" if request.format_type == "audio" else "mp4"
        
        return DownloadUrlResponse(
            success=True,
            download_url=download_url,
            title=video_info.title,
            filesize_mb=filesize_mb,
            format=format_ext,
            quality=request.quality,
            type=request.format_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando URL de descarga: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search_videos(
    q: str = Query(..., description="Término de búsqueda"),
    max_results: int = Query(default=10, ge=1, le=50)
):
    """Búsqueda de videos estilo Snaptube"""
    try:
        videos = extractor.search_videos(q, max_results)
        
        # Convertir a formato Snaptube
        search_results = [
            SnaptubeConverter.video_to_search_result(video) 
            for video in videos
        ]
        
        return SearchResponse(
            success=True,
            query=q,
            total_results=len(search_results),
            results=search_results,
            suggestions=[]  # Puedes implementar sugerencias después
        )
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending", response_model=TrendingResponse)
async def get_trending(region: str = Query(default="US", description="Región para trending")):
    """Obtiene videos trending estilo Snaptube"""
    try:
        # Simular trending usando búsquedas populares
        trending_queries = [
            "trending music", "viral videos", "popular today",
            "trending now", "top videos"
        ]
        
        all_videos = []
        for query in trending_queries[:2]:  # Limitar consultas
            videos = extractor.search_videos(query, 5)
            all_videos.extend(videos)
        
        # Convertir a formato trending
        trending_videos = [
            SnaptubeConverter.video_to_trending(video)
            for video in all_videos[:20]
        ]
        
        return TrendingResponse(
            success=True,
            region=region,
            total_results=len(trending_videos),
            trending_videos=trending_videos
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo trending: {e}")
        raise HTTPException(status_code=500, detail=str(e))