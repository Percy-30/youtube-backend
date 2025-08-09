# app/models/video_models.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any

class VideoInfo(BaseModel):
    """Modelo base para información de video"""
    status: str = Field(..., description="Estado de la respuesta")
    platform: str = Field(..., description="Plataforma del video")
    title: str = Field(..., description="Título del video")
    thumbnail: Optional[str] = Field(None, description="URL de la miniatura")
    duration: Optional[int] = Field(None, description="Duración en segundos")
    video_url: str = Field(..., description="URL directa del video")
    width: Optional[int] = Field(None, description="Ancho del video")
    height: Optional[int] = Field(None, description="Alto del video")
    uploader: Optional[str] = Field(None, description="Nombre del uploader")
    view_count: Optional[int] = Field(None, description="Número de visualizaciones")
    method: Optional[str] = Field(None, description="Método usado para extraer")

class TikTokVideoInfo(VideoInfo):
    """Modelo específico para videos de TikTok"""
    platform: str = Field(default="tiktok", description="Plataforma TikTok")
    like_count: Optional[int] = Field(None, description="Número de likes")
    comment_count: Optional[int] = Field(None, description="Número de comentarios")
    share_count: Optional[int] = Field(None, description="Número de compartidos")

class FacebookVideoInfo(VideoInfo):
    """Modelo específico para videos de Facebook"""
    platform: str = Field(default="facebook", description="Plataforma Facebook")
    
class YouTubeVideoInfo(VideoInfo):
    """Modelo específico para videos de YouTube"""
    platform: str = Field(default="youtube", description="Plataforma YouTube")
    upload_date: Optional[str] = Field(None, description="Fecha de subida")
    description: Optional[str] = Field(None, description="Descripción del video")
    channel: Optional[str] = Field(None, description="Canal de YouTube")
    subscriber_count: Optional[int] = Field(None, description="Suscriptores del canal")

class VideoRequest(BaseModel):
    """Modelo para requests de video"""
    url: HttpUrl = Field(..., description="URL del video")
    prefer_mobile: bool = Field(False, description="Usar user-agent móvil")
    force_ytdlp: bool = Field(False, description="Forzar uso de yt-dlp para YouTube")
    cookies: Optional[str] = Field(None, description="Cookies para YouTube")

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error"""
    status: str = Field(default="error", description="Estado de error")
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")
    platform: Optional[str] = Field(None, description="Plataforma donde ocurrió el error")

class ExtractionResult(BaseModel):
    """Modelo para resultado de extracción"""
    success: bool = Field(..., description="Si la extracción fue exitosa")
    data: Optional[VideoInfo] = Field(None, description="Datos del video")
    error: Optional[str] = Field(None, description="Mensaje de error")
    method_used: Optional[str] = Field(None, description="Método usado para la extracción")