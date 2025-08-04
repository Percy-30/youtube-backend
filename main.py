<<<<<<< HEAD
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import logging
from typing import Optional, List
from datetime import datetime

from models.video_info import (
    ExtractRequest, ExtractResponse, PlaylistExtractResponse,
    VideoInfo, PlaylistInfo
)
from services.youtube_handler import YouTubeExtractor
from config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear instancia de FastAPI
app = FastAPI(
    title="YouTube Extractor API",
    description="API para extraer información y contenido de YouTube usando yt-dlp",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
=======
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from yt_dlp import YoutubeDL
import uvicorn

app = FastAPI()

# CORS para que tu app Android pueda acceder sin restricciones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia por el dominio exacto de tu app si prefieres más seguridad
>>>>>>> ad6af88411ae2baf0111a7aff4d1766a939b8d7c
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# Instancia global del extractor
extractor = YouTubeExtractor()

# Rate limiting simple (en memoria)
request_times = {}

def check_rate_limit(client_ip: str) -> bool:
    """Verifica rate limiting simple"""
    current_time = time.time()
    if client_ip not in request_times:
        request_times[client_ip] = []
    
    # Limpiar requests antiguos (más de 1 minuto)
    request_times[client_ip] = [
        req_time for req_time in request_times[client_ip]
        if current_time - req_time < 60
    ]
    
    # Verificar límite
    if len(request_times[client_ip]) >= Config.MAX_REQUESTS_PER_MINUTE:
        return False
    
    request_times[client_ip].append(current_time)
    return True

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Middleware para agregar tiempo de procesamiento"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": "YouTube Extractor API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "extract_video": "/extract/video",
            "extract_playlist": "/extract/playlist",
            "search": "/search",
            "channel_videos": "/channel/{channel_id}/videos",
            "stream_url": "/stream/{video_id}",
            "health": "/health",
            "stats": "/stats"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud"""
    try:
        stats = extractor.get_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "extractor_stats": stats
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/extract/video", response_model=ExtractResponse)
async def extract_video(request: ExtractRequest):
    """Extrae información de un video de YouTube"""
    start_time = time.time()
    
    try:
        logger.info(f"Extrayendo video: {request.url}")
        
        video_info = extractor.extract_video_info(
            url=request.url,
            extract_audio=request.extract_audio,
            quality=request.quality or "best"
        )
        
        processing_time = time.time() - start_time
        
        if video_info:
            return ExtractResponse(
                success=True,
                message="Video extraído exitosamente",
                data=video_info,
                processing_time=processing_time
            )
        else:
            return ExtractResponse(
                success=False,
                message="No se pudo extraer el video",
                error="Video no encontrado o inaccesible",
                processing_time=processing_time
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error extrayendo video: {e}")
        
        return ExtractResponse(
            success=False,
            message="Error interno del servidor",
            error=str(e),
            processing_time=processing_time
        )

@app.post("/extract/playlist", response_model=PlaylistExtractResponse)
async def extract_playlist(
    url: str,
    max_videos: int = Query(default=20, ge=1, le=100, description="Máximo número de videos a extraer")
):
    """Extrae información de una playlist de YouTube"""
    start_time = time.time()
    
    try:
        logger.info(f"Extrayendo playlist: {url}")
        
        playlist_info = extractor.extract_playlist_info(url, max_videos)
        processing_time = time.time() - start_time
        
        if playlist_info:
            return PlaylistExtractResponse(
                success=True,
                message=f"Playlist extraída exitosamente ({len(playlist_info.entries)} videos)",
                data=playlist_info,
                processing_time=processing_time
            )
        else:
            return PlaylistExtractResponse(
                success=False,
                message="No se pudo extraer la playlist",
                error="Playlist no encontrada o inaccesible",
                processing_time=processing_time
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error extrayendo playlist: {e}")
        
        return PlaylistExtractResponse(
            success=False,
            message="Error interno del servidor",
            error=str(e),
            processing_time=processing_time
        )

@app.get("/search")
async def search_videos(
    q: str = Query(..., description="Término de búsqueda"),
    max_results: int = Query(default=10, ge=1, le=50, description="Máximo número de resultados")
):
    """Busca videos en YouTube"""
    try:
        logger.info(f"Buscando videos: {q}")
        
        videos = extractor.search_videos(q, max_results)
        
        return {
            "success": True,
            "message": f"Búsqueda completada: {len(videos)} videos encontrados",
            "query": q,
            "results": len(videos),
            "data": videos
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/channel/{channel_id}/videos")
async def get_channel_videos(
    channel_id: str = Path(..., description="ID del canal o URL del canal"),
    max_videos: int = Query(default=20, ge=1, le=50, description="Máximo número de videos")
):
    """Obtiene videos de un canal específico"""
    try:
        # Construir URL del canal si solo se proporciona el ID
        if not channel_id.startswith('http'):
            channel_url = f"https://www.youtube.com/channel/{channel_id}"
        else:
            channel_url = channel_id
        
        logger.info(f"Obteniendo videos del canal: {channel_url}")
        
        videos = extractor.get_channel_videos(channel_url, max_videos)
        
        return {
            "success": True,
            "message": f"Videos del canal obtenidos: {len(videos)} videos",
            "channel_url": channel_url,
            "results": len(videos),
            "data": videos
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo videos del canal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream/{video_id}")
async def get_stream_url(
    video_id: str = Path(..., description="ID del video de YouTube"),
    quality: str = Query(default="best", description="Calidad del video (best, high, medium, low)")
):
    """Obtiene URL directa de stream de un video"""
    try:
        logger.info(f"Obteniendo stream URL para: {video_id}")
        
        stream_url = extractor.get_video_stream_url(video_id, quality)
        
        if stream_url:
            return {
                "success": True,
                "message": "Stream URL obtenida exitosamente",
                "video_id": video_id,
                "quality": quality,
                "stream_url": stream_url
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="No se pudo obtener la URL de stream para este video"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo stream URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtiene estadísticas del sistema"""
    try:
        stats = extractor.get_stats()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "system_stats": {
                "total_requests": sum(len(times) for times in request_times.values()),
                "active_clients": len(request_times),
                "config": {
                    "use_proxies": Config.USE_PROXIES,
                    "use_browser_cookies": Config.USE_BROWSER_COOKIES,
                    "max_requests_per_minute": Config.MAX_REQUESTS_PER_MINUTE
                }
            },
            "extractor_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint no encontrado",
            "error": "La ruta solicitada no existe",
            "available_endpoints": [
                "/docs",
                "/extract/video",
                "/extract/playlist",
                "/search",
                "/health"
            ]
        }
    )

@app.exception_handler(500)
async def custom_500_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Error interno del servidor",
            "error": "Ha ocurrido un error inesperado",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    logger.info("Iniciando YouTube Extractor API...")
    logger.info(f"Configuración cargada - Proxies: {Config.USE_PROXIES}, Cookies: {Config.USE_BROWSER_COOKIES}")
    
    uvicorn.run(
        "main:app",
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        reload=Config.DEBUG,
        log_level="info"
    )
=======
@app.get("/youtube")
async def youtube_info(url: str = Query(...), request: Request = None):
    cookies = request.headers.get("cookie") or request.headers.get("Cookie")

    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True,
        "skip_download": True,
        "cookiefile": None,
        "format": "best",
    }

    # Usamos cookies si las recibimos
    if cookies:
        ydl_opts["http_headers"] = {
            "Cookie": cookies,
            "User-Agent": "Mozilla/5.0"
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", ""),
                "downloadUrl": info.get("url", ""),
                "thumbnail": info.get("thumbnail", ""),
                "duration": str(info.get("duration", 0)) + "s"
            }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"No se pudo procesar el video: {str(e)}"}
        )

# Para correr local (no necesario en Render)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
>>>>>>> ad6af88411ae2baf0111a7aff4d1766a939b8d7c
