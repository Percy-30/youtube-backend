# services/enhanced_youtube_service.py
from typing import Optional, List, Dict, Any
import logging
import time
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import re

from services.youtube_handler import YouTubeExtractor
from models.video_info import VideoInfo, PlaylistInfo
from models.snaptube_models import (
    SnaptubeVideoInfo, SearchResult, TrendingVideo,
    SnaptubeConverter, EnhancedSnaptubeConverter
)
from config import Config

logger = logging.getLogger(__name__)

class EnhancedYouTubeService:
    """Servicio mejorado de YouTube con funcionalidades específicas de Snaptube"""
    
    def __init__(self):
        self.extractor = YouTubeExtractor()
        self.cache = {}  # Cache simple en memoria
        self.cache_ttl = 300  # 5 minutos
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Genera clave de cache"""
        params = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{prefix}:{params}"
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si el cache es válido"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key].get('timestamp', 0)
        return time.time() - cached_time < self.cache_ttl
    
    def _set_cache(self, key: str, data: Any):
        """Establece datos en cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Obtiene datos del cache"""
        if self._is_cache_valid(key):
            return self.cache[key]['data']
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_video_info_with_retry(self, url: str, extract_audio: bool = False, 
                                       quality: str = "best") -> Optional[VideoInfo]:
        """Obtiene información del video con reintentos"""
        cache_key = self._get_cache_key("video_info", url=url, audio=extract_audio, quality=quality)
        
        # Verificar cache
        cached_data = self._get_cache(cache_key)
        if cached_data:
            logger.info(f"Cache hit para video: {url}")
            return cached_data
        
        try:
            video_info = self.extractor.extract_video_info(url, extract_audio, quality)
            
            if video_info:
                # Validaciones adicionales
                if not self._validate_video_info(video_info):
                    logger.warning(f"Video info inválida para: {url}")
                    return None
                
                # Cachear resultado
                self._set_cache(cache_key, video_info)
                logger.info(f"Video extraído y cacheado: {video_info.title}")
                
            return video_info
            
        except Exception as e:
            logger.error(f"Error extrayendo video {url}: {e}")
            raise
    
    def _validate_video_info(self, video_info: VideoInfo) -> bool:
        """Valida que la información del video sea correcta"""
        if not video_info.id or not video_info.title:
            return False
        
        # Verificar duración máxima
        if video_info.duration and video_info.duration > Config.MAX_VIDEO_DURATION:
            logger.warning(f"Video demasiado largo: {video_info.duration}s")
            return False
        
        return True
    
    async def search_videos_enhanced(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Búsqueda mejorada con filtros y validación"""
        if not re.match(r'^[a-zA-Z0-9\s\-_áéíóúñü]+$', query):
            logger.warning(f"Query con caracteres sospechosos: {query}")
            return []
        
        cache_key = self._get_cache_key("search", query=query, max_results=max_results)
        cached_results = self._get_cache(cache_key)
        
        if cached_results:
            logger.info(f"Cache hit para búsqueda: {query}")
            return cached_results
        
        try:
            videos = self.extractor.search_videos(query, max_results)
            
            # Convertir a formato Snaptube y filtrar
            search_results = []
            for video in videos:
                if self._validate_video_info(video):
                    result = EnhancedSnaptubeConverter.video_to_search_result(video)
                    search_results.append(result)
            
            # Cachear resultados
            self._set_cache(cache_key, search_results)
            logger.info(f"Búsqueda completada: {len(search_results)} resultados para '{query}'")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def get_trending_videos(self, region: str = "US") -> List[TrendingVideo]:
        """Obtiene videos trending simulados"""
        cache_key = self._get_cache_key("trending", region=region)
        cached_trending = self._get_cache(cache_key)
        
        if cached_trending:
            logger.info(f"Cache hit para trending: {region}")
            return cached_trending
        
        try:
            # Queries populares por región
            trending_queries = {
                "US": ["trending music", "viral videos", "popular now", "trending today"],
                "ES": ["música trending", "videos virales", "popular hoy"],
                "MX": ["tendencias mexico", "viral mexico", "música popular"],
                "AR": ["trending argentina", "videos populares", "música argentina"],
                "default": ["trending", "popular", "viral", "music"]
            }
            
            queries = trending_queries.get(region, trending_queries["default"])
            all_videos = []
            
            # Obtener videos de múltiples queries
            for query in queries[:3]:  # Limitar a 3 queries
                try:
                    videos = self.extractor.search_videos(query, 8)
                    all_videos.extend(videos)
                except Exception as e:
                    logger.warning(f"Error en query trending '{query}': {e}")
                    continue
            
            # Eliminar duplicados y convertir
            seen_ids = set()
            trending_videos = []
            
            for video in all_videos:
                if video.id not in seen_ids and self._validate_video_info(video):
                    seen_ids.add(video.id)
                    trending_video = EnhancedSnaptubeConverter.video_to_trending(video)
                    trending_videos.append(trending_video)
                    
                    if len(trending_videos) >= 20:  # Limitar a 20
                        break
            
            # Cachear resultados
            self._set_cache(cache_key, trending_videos)
            logger.info(f"Trending obtenido: {len(trending_videos)} videos para {region}")
            
            return trending_videos
            
        except Exception as e:
            logger.error(f"Error obteniendo trending para {region}: {e}")
            return []
    
    async def get_download_url_smart(self, url: str, format_type: str = "video", 
                                   quality: str = "best") -> Optional[Dict[str, Any]]:
        """Obtiene URL de descarga con selección inteligente"""
        try:
            video_info = await self.get_video_info_with_retry(
                url, 
                extract_audio=(format_type == "audio"),
                quality=quality
            )
            
            if not video_info:
                return None
            
            # Selección inteligente de formato
            download_url = None
            selected_format = None
            
            if format_type == "audio":
                # Buscar mejor formato de audio
                audio_formats = [f for f in video_info.formats if f.acodec and f.acodec != 'none']
                if audio_formats:
                    # Ordenar por calidad de audio (preferir AAC > Opus > MP3)
                    codec_priority = {'aac': 3, 'opus': 2, 'mp3': 1}
                    audio_formats.sort(
                        key=lambda x: (codec_priority.get(x.acodec, 0), x.tbr or 0),
                        reverse=True
                    )
                    selected_format = audio_formats[0]
                    download_url = selected_format.url
                else:
                    download_url = video_info.best_audio_url
            else:
                # Buscar mejor formato de video según calidad solicitada
                video_formats = [f for f in video_info.formats if f.vcodec and f.vcodec != 'none']
                
                if quality == "best":
                    # Mejor calidad disponible
                    video_formats.sort(key=lambda x: x.quality or 0, reverse=True)
                    if video_formats:
                        selected_format = video_formats[0]
                        download_url = selected_format.url
                    else:
                        download_url = video_info.best_video_url
                        
                elif quality in ["1080p", "720p", "480p", "360p"]:
                    # Calidad específica
                    target_height = int(quality.replace("p", ""))
                    best_match = None
                    
                    for fmt in video_formats:
                        if fmt.resolution:
                            height_match = re.search(r'(\d+)p?, fmt.resolution')
                            if height_match:
                                fmt_height = int(height_match.group(1))
                                if fmt_height <= target_height:
                                    if not best_match or fmt_height > int(re.search(r'(\d+)', best_match.resolution).group(1)):
                                        best_match = fmt
                    
                    if best_match:
                        selected_format = best_match
                        download_url = best_match.url
                    else:
                        download_url = video_info.best_video_url
                else:
                    download_url = video_info.best_video_url
            
            if not download_url:
                logger.error(f"No se pudo obtener URL de descarga para: {url}")
                return None
            
            # Preparar respuesta
            result = {
                'download_url': download_url,
                'title': video_info.title,
                'format': selected_format.ext if selected_format else ('mp3' if format_type == 'audio' else 'mp4'),
                'quality': quality,
                'type': format_type,
                'filesize': selected_format.filesize if selected_format else None,
                'duration': video_info.duration,
                'video_id': video_info.id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo URL de descarga: {e}")
            return None
    
    async def get_channel_info(self, channel_url: str, max_videos: int = 20) -> Optional[Dict[str, Any]]:
        """Obtiene información de canal con videos"""
        cache_key = self._get_cache_key("channel", url=channel_url, max_videos=max_videos)
        cached_data = self._get_cache(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            videos = self.extractor.get_channel_videos(channel_url, max_videos)
            
            if not videos:
                return None
            
            # Información del canal basada en el primer video
            first_video = videos[0]
            channel_info = {
                'channel_id': first_video.channel_id,
                'channel_name': first_video.channel or first_video.uploader,
                'channel_url': first_video.channel_url or channel_url,
                'video_count': len(videos),
                'videos': [EnhancedSnaptubeConverter.video_to_search_result(v) for v in videos]
            }
            
            self._set_cache(cache_key, channel_info)
            return channel_info
            
        except Exception as e:
            logger.error(f"Error obteniendo canal: {e}")
            return None
    
    def get_supported_qualities(self, video_info: VideoInfo) -> Dict[str, List[str]]:
        """Obtiene calidades soportadas del video"""
        qualities = {
            'video': [],
            'audio': []
        }
        
        # Calidades de video
        video_formats = [f for f in video_info.formats if f.vcodec and f.vcodec != 'none']
        video_heights = set()
        
        for fmt in video_formats:
            if fmt.resolution:
                height_match = re.search(r'(\d+)p?, fmt.resolution')
                if height_match:
                    height = int(height_match.group(1))
                    video_heights.add(height)
        
        # Ordenar calidades de video
        for height in sorted(video_heights, reverse=True):
            qualities['video'].append(f"{height}p")
        
        # Calidades de audio estándar
        qualities['audio'] = ["High (192K)", "Standard (128K)", "Low (96K)"]
        
        return qualities
    
    def estimate_download_time(self, filesize: Optional[int], connection_speed: str = "medium") -> str:
        """Estima tiempo de descarga"""
        if not filesize:
            return "Unknown"
        
        # Velocidades típicas en Mbps
        speeds = {
            "slow": 2,      # 2 Mbps
            "medium": 10,   # 10 Mbps  
            "fast": 50,     # 50 Mbps
            "fiber": 100    # 100 Mbps
        }
        
        speed_mbps = speeds.get(connection_speed, 10)
        speed_bytes_per_sec = (speed_mbps * 1024 * 1024) / 8  # Convertir a bytes/sec
        
        estimated_seconds = filesize / speed_bytes_per_sec
        
        if estimated_seconds < 60:
            return f"~{int(estimated_seconds)}s"
        elif estimated_seconds < 3600:
            minutes = int(estimated_seconds / 60)
            return f"~{minutes}m"
        else:
            hours = int(estimated_seconds / 3600)
            minutes = int((estimated_seconds % 3600) / 60)
            return f"~{hours}h {minutes}m"
    
    def get_video_suggestions(self, video_info: VideoInfo) -> List[str]:
        """Genera sugerencias basadas en el video"""
        suggestions = []
        
        if video_info.tags:
            # Usar tags como sugerencias
            relevant_tags = [tag for tag in video_info.tags[:5] if len(tag) > 3]
            suggestions.extend(relevant_tags)
        
        if video_info.uploader:
            suggestions.append(f"More from {video_info.uploader}")
        
        if video_info.categories:
            suggestions.extend(video_info.categories[:2])
        
        return suggestions[:8]  # Limitar a 8 sugerencias
    
    async def bulk_extract_videos(self, urls: List[str], max_concurrent: int = 3) -> List[VideoInfo]:
        """Extrae múltiples videos concurrentemente"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single(url: str) -> Optional[VideoInfo]:
            async with semaphore:
                return await self.get_video_info_with_retry(url)
        
        tasks = [extract_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados válidos
        valid_results = []
        for result in results:
            if isinstance(result, VideoInfo):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Error en extracción bulk: {result}")
        
        return valid_results
    
    def cleanup_cache(self):
        """Limpia cache expirado"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.cache.items():
            if current_time - data['timestamp'] > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"Cache limpiado: {len(expired_keys)} entradas eliminadas")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del servicio"""
        return {
            'cache_size': len(self.cache),
            'extractor_stats': self.extractor.get_stats(),
            'cache_hit_ratio': self._calculate_cache_hit_ratio()
        }
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calcula ratio de cache hits (simulado)"""
        # Implementación básica - en producción usarías métricas reales
        total_requests = len(self.cache)
        if total_requests == 0:
            return 0.0
        
        # Estimación basada en cache válido
        valid_cache = sum(1 for key in self.cache.keys() if self._is_cache_valid(key))
        return round(valid_cache / total_requests, 2)

# Instancia global del servicio
enhanced_service = EnhancedYouTubeService()