# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import time
import logging
from datetime import datetime

# Importar rutas
from routes.snaptube_routes import router as snaptube_router
from routes.video_info import router as video_info_router
from routes.video_formats import router as formats_router
from routes.download import router as download_router
from routes.search import router as search_router
from routes.trending import router as trending_router
from routes.social_extract import router as social_extract_router

from config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear instancia de FastAPI
app = FastAPI(
    title="Snaptube-Like YouTube API",
    description="API para extraer información y descargar contenido de YouTube, compatible con Snaptube",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir todas las solicitudes (estilo Snaptube)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting simple (en memoria)
request_times = {}

@app.middleware("http")
async def rate_limit_and_timing_middleware(request: Request, call_next):
    """Middleware para rate limiting y timing"""
    start_time = time.time()
    
    # Rate limiting
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip not in request_times:
        request_times[client_ip] = []
    
    # Limpiar requests antiguos
    request_times[client_ip] = [
        req_time for req_time in request_times[client_ip]
        if current_time - req_time < 60
    ]
    
    # Verificar límite
    if len(request_times[client_ip]) >= Config.MAX_REQUESTS_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "message": "Rate limit exceeded",
                "error": f"Maximum {Config.MAX_REQUESTS_PER_MINUTE} requests per minute",
                "retry_after": 60
            }
        )
    
    request_times[client_ip].append(current_time)
    
    # Procesar request
    response = await call_next(request)
    
    # Agregar headers de timing
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    response.headers["X-API-Version"] = "2.0.0"
    
    return response

# Incluir rutas principales (estilo Snaptube)
app.include_router(snaptube_router)

# Incluir rutas compatibles con versión anterior
app.include_router(video_info_router, prefix="/v1")
app.include_router(formats_router, prefix="/v1")
app.include_router(download_router, prefix="/v1")
app.include_router(search_router, prefix="/v1")
app.include_router(trending_router, prefix="/v1")
app.include_router(social_extract_router, prefix="/api/v1")
#app.include_router(social_extract_router, prefix="/api/v1")  # social platforms

@app.get("/")
async def root():
    """Endpoint raíz estilo Snaptube"""
    return {
        "app": "Snaptube-Like YouTube API",
        "version": "2.0.0",
        "status": "active",
        "description": "API compatible con Snaptube para extraer y descargar contenido de YouTube",
        "endpoints": {
            "video_info": "/api/v1/video/info?url=VIDEO_URL",
            "video_formats": "/api/v1/video/formats?url=VIDEO_URL", 
            "download": "/api/v1/download",
            "search": "/api/v1/search?q=QUERY",
            "trending": "/api/v1/trending?region=US"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "features": [
            "Video information extraction",
            "Multiple quality options",
            "Audio-only downloads",
            "Search functionality",
            "Trending videos",
            "Proxy support",
            "Cookie management",
            "Rate limiting"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from services.youtube_handler import YouTubeExtractor
        test_extractor = YouTubeExtractor()
        stats = test_extractor.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "extractor_ready": True,
            "stats": stats
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

@app.get("/stats")
async def get_system_stats():
    """Estadísticas del sistema"""
    try:
        from services.youtube_handler import YouTubeExtractor
        test_extractor = YouTubeExtractor()
        extractor_stats = test_extractor.get_stats()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0",
            "system_stats": {
                "total_requests": sum(len(times) for times in request_times.values()),
                "active_clients": len(request_times),
                "rate_limit": Config.MAX_REQUESTS_PER_MINUTE,
                "config": {
                    "use_proxies": Config.USE_PROXIES,
                    "use_browser_cookies": Config.USE_BROWSER_COOKIES,
                    "debug_mode": Config.DEBUG
                }
            },
            "extractor_stats": extractor_stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Manejadores de errores globales
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "error": "The requested resource does not exist",
            "available_endpoints": [
                "/api/v1/video/info",
                "/api/v1/video/formats", 
                "/api/v1/download",
                "/api/v1/search",
                "/api/v1/trending",
                "/health",
                "/stats",
                "/docs"
            ],
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Rate limit exceeded",
            "error": f"Maximum {Config.MAX_REQUESTS_PER_MINUTE} requests per minute allowed",
            "retry_after": 60,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    logger.info("🚀 Iniciando Snaptube-Like YouTube API...")
    logger.info(f"📊 Configuración - Proxies: {Config.USE_PROXIES}, Cookies: {Config.USE_BROWSER_COOKIES}")
    
    # Puerto para deployment (Railway, Render, etc.)
    port = int(os.getenv("PORT", Config.APP_PORT))
    
    uvicorn.run(
        "main:app",
        host=Config.APP_HOST,
        port=port,
        reload=Config.DEBUG,
        log_level="info" if not Config.DEBUG else "debug",
        access_log=True
    )