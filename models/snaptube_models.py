from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# ============== MODELOS ESPECÍFICOS PARA SNAPTUBE ==============

class SnaptubeVideoInfo(BaseModel):
    """Información básica del video para preview (como Snaptube)"""
    id: str
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    duration_string: Optional[str] = None
    view_count: Optional[int] = None
    uploader: str
    upload_date: Optional[str] = None
    thumbnail: Optional[str] = None
    thumbnails: List[Dict[str, Any]] = []
    webpage_url: str
    has_formats: bool = True

class DownloadOption(BaseModel):
    """Opción de descarga estilo Snaptube"""
    type: Literal["video", "audio"]
    quality: str  # "1080p", "720p", "High", etc
    format: str   # "mp4", "mp3", etc
    size_estimate: str  # "~50MB"
    recommended: bool = False
    format_id: Optional[str] = None
    actual_filesize: Optional[int] = None

class FormatGroup(BaseModel):
    """Grupo de formatos organizados por calidad"""
    high_quality: List[Dict[str, Any]] = []
    medium_quality: List[Dict[str, Any]] = []
    low_quality: List[Dict[str, Any]] = []
    mobile: List[Dict[str, Any]] = []

class VideoFormatsResponse(BaseModel):
    """Respuesta completa de formatos disponibles"""
    success: bool
    video_info: SnaptubeVideoInfo
    formats: Dict[str, FormatGroup]
    download_options: List[DownloadOption]
    processing_time: Optional[float] = None

class DownloadRequest(BaseModel):
    """Request para descarga directa"""
    url: str
    format_type: Literal["video", "audio"]
    quality: str = "best"
    convert_to: Optional[str] = None

class DownloadUrlResponse(BaseModel):
    """Respuesta con URL directa de descarga"""
    success: bool
    download_url: str
    title: str
    filesize: Optional[int] = None
    filesize_mb: Optional[float] = None
    format: str
    quality: str
    type: str
    expires_in: str = "1 hour (estimated)"

class TrendingVideo(BaseModel):
    """Video en trending simplificado"""
    id: str
    title: str
    uploader: str
    duration_string: Optional[str] = None
    view_count: Optional[int] = None
    thumbnail: Optional[str] = None
    url: str

class TrendingResponse(BaseModel):
    """Respuesta de videos trending"""
    success: bool
    region: str
    total_results: int
    trending_videos: List[TrendingVideo]

class SearchResult(BaseModel):
    """Resultado de búsqueda optimizado para móvil"""
    id: str
    title: str
    uploader: str
    duration_string: Optional[str] = None
    view_count: Optional[int] = None
    thumbnail: str
    url: str
    upload_date: Optional[str] = None

class SearchResponse(BaseModel):
    """Respuesta de búsqueda estilo Snaptube"""
    success: bool
    query: str
    total_results: int
    results: List[SearchResult]
    suggestions: List[str] = []  # Sugerencias relacionadas

class QuickInfoResponse(BaseModel):
    """Información rápida del video (preview)"""
    success: bool
    video: SnaptubeVideoInfo
    processing_time: Optional[float] = None

# ============== UTILIDADES PARA CONVERSIÓN ==============

class SnaptubeConverter:
    """Convertidor de modelos a formato Snaptube"""
    
    @staticmethod
    def video_to_snaptube_info(video_info) -> SnaptubeVideoInfo:
        """Convierte VideoInfo a SnaptubeVideoInfo"""
        return SnaptubeVideoInfo(
            id=video_info.id,
            title=video_info.title,
            description=video_info.description[:200] + "..." if video_info.description else None,
            duration=video_info.duration,
            duration_string=video_info.duration_string,
            view_count=video_info.view_count,
            uploader=video_info.uploader or "Unknown",
            upload_date=video_info.upload_date,
            thumbnail=video_info.thumbnails[0].url if video_info.thumbnails else None,
            thumbnails=[
                {
                    "url": thumb.url,
                    "width": thumb.width,
                    "height": thumb.height,
                    "resolution": f"{thumb.width}x{thumb.height}" if thumb.width else None
                }
                for thumb in video_info.thumbnails[:5]
            ],
            webpage_url=video_info.webpage_url,
            has_formats=len(video_info.formats) > 0
        )
    
    @staticmethod
    def video_to_search_result(video_info) -> SearchResult:
        """Convierte VideoInfo a SearchResult"""
        return SearchResult(
            id=video_info.id,
            title=video_info.title,
            uploader=video_info.uploader or "Unknown",
            duration_string=video_info.duration_string,
            view_count=video_info.view_count,
            thumbnail=video_info.thumbnails[0].url if video_info.thumbnails else "",
            url=video_info.webpage_url,
            upload_date=video_info.upload_date
        )
    
    @staticmethod
    def video_to_trending(video_info) -> TrendingVideo:
        """Convierte VideoInfo a TrendingVideo"""
        return TrendingVideo(
            id=video_info.id,
            title=video_info.title,
            uploader=video_info.uploader or "Unknown",
            duration_string=video_info.duration_string,
            view_count=video_info.view_count,
            thumbnail=video_info.thumbnails[0].url if video_info.thumbnails else None,
            url=video_info.webpage_url
        )
    
    @staticmethod
    def estimate_filesize(duration: int, quality: str, format_type: str) -> str:
        """Estima el tamaño del archivo basado en duración y calidad"""
        if not duration:
            return "Unknown"
        
        # Estimaciones aproximadas (MB por minuto)
        rates = {
            "video": {
                "1080p": 8.0,   # ~8MB por minuto
                "720p": 5.0,    # ~5MB por minuto  
                "480p": 3.0,    # ~3MB por minuto
                "360p": 2.0,    # ~2MB por minuto
                "240p": 1.0     # ~1MB por minuto
            },
            "audio": {
                "high": 1.2,    # ~1.2MB por minuto
                "medium": 1.0,  # ~1MB por minuto
                "low": 0.5      # ~0.5MB por minuto
            }
        }
        
        minutes = duration / 60
        rate = rates.get(format_type, {}).get(quality.lower(), 2.0)
        estimated_mb = minutes * rate
        
        if estimated_mb < 1:
            return f"~{int(estimated_mb * 1024)}KB"
        elif estimated_mb < 1024:
            return f"~{int(estimated_mb)}MB"
        else:
            return f"~{estimated_mb/1024:.1f}GB"
    
    @staticmethod
    def generate_download_options(video_info, include_audio: bool = True) -> List[DownloadOption]:
        """Genera opciones de descarga estilo Snaptube"""
        options = []
        
        # Opciones de video
        video_qualities = ["1080p", "720p", "480p", "360p"]
        for i, quality in enumerate(video_qualities):
            size_estimate = SnaptubeConverter.estimate_filesize(
                video_info.duration or 300, quality, "video"
            )
            
            options.append(DownloadOption(
                type="video",
                quality=quality,
                format="mp4",
                size_estimate=size_estimate,
                recommended=(i == 1)  # 720p recomendado
            ))
        
        # Opciones de audio
        if include_audio:
            audio_qualities = [("High", "192K"), ("Medium", "128K"), ("Low", "96K")]
            for i, (quality_name, bitrate) in enumerate(audio_qualities):
                size_estimate = SnaptubeConverter.estimate_filesize(
                    video_info.duration or 300, quality_name.lower(), "audio"
                )
                
                options.append(DownloadOption(
                    type="audio",
                    quality=f"{quality_name} ({bitrate})",
                    format="mp3",
                    size_estimate=size_estimate,
                    recommended=(i == 1)  # Medium recomendado
                ))
        
        return options