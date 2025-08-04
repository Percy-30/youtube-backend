import yt_dlp
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path

from models.video_info import VideoInfo, VideoFormat, VideoThumbnail, PlaylistInfo
from utils.proxy import ProxyRotator
from utils.cookies import CookieManager
from config import Config

logger = logging.getLogger(__name__)

class YouTubeExtractor:
    """Extractor principal de contenido de YouTube usando yt-dlp"""
    
    def __init__(self):
        self.proxy_rotator = None
        self.cookie_manager = CookieManager()
        self.setup_proxies()
        self.setup_cookies()
    
    def setup_proxies(self):
        """Configura el sistema de proxies"""
        if Config.USE_PROXIES and Config.PROXY_LIST:
            self.proxy_rotator = ProxyRotator(Config.PROXY_LIST)
            logger.info(f"Rotador de proxies configurado con {len(Config.PROXY_LIST)} proxies")
    
    def setup_cookies(self):
        """Configura las cookies"""
        if Config.USE_BROWSER_COOKIES:
            # Extraer cookies del navegador
            success = self.cookie_manager.export_browser_cookies(
                Config.BROWSER_NAME, 
                Config.COOKIES_FULL_PATH
            )
            if not success:
                logger.warning("No se pudieron extraer cookies del navegador")
        
        # Verificar si existe el archivo de cookies
        if not Config.COOKIES_FULL_PATH.exists():
            logger.info("Creando archivo de cookies de ejemplo")
            self.cookie_manager.create_sample_cookies_file(Config.COOKIES_FULL_PATH)
    
    def get_yt_dlp_options(self, custom_options: Optional[Dict] = None) -> Dict:
        """Obtiene las opciones para yt-dlp"""
        options = Config.YT_DLP_OPTIONS.copy()
        
        # Agregar User-Agent
        options['http_headers'] = {
            'User-Agent': Config.USER_AGENT
        }
        
        # Agregar cookies si existen
        if Config.COOKIES_FULL_PATH.exists():
            if self.cookie_manager.validate_cookies_file(Config.COOKIES_FULL_PATH):
                options['cookiefile'] = str(Config.COOKIES_FULL_PATH)
                logger.info("Cookies configuradas")
        
        # Agregar proxy si está disponible
        if self.proxy_rotator:
            proxy = self.proxy_rotator.get_yt_dlp_proxy_option()
            if proxy:
                options['proxy'] = proxy
                logger.info(f"Usando proxy: {proxy}")
        
        # Merge con opciones personalizadas
        if custom_options:
            options.update(custom_options)
        
        return options
    
    def extract_video_info(self, url: str, extract_audio: bool = False, 
                          quality: str = "best") -> Optional[VideoInfo]:
        """Extrae información de un video de YouTube"""
        start_time = time.time()
        
        try:
            # Configurar opciones específicas
            custom_options = {}
            
            if extract_audio:
                custom_options.update({
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3'
                })
            else:
                if quality == "high":
                    custom_options['format'] = 'best[height<=1080]/best'
                elif quality == "medium":
                    custom_options['format'] = 'best[height<=720]/best'
                elif quality == "low":
                    custom_options['format'] = 'worst/best'
            
            options = self.get_yt_dlp_options(custom_options)
            
            with yt_dlp.YoutubeDL(options) as ydl:
                # Extraer información sin descargar
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    logger.error("No se pudo extraer información del video")
                    return None
                
                # Convertir a nuestro modelo
                video_info = self._convert_to_video_info(info)
                
                processing_time = time.time() - start_time
                logger.info(f"Video extraído en {processing_time:.2f}s: {video_info.title}")
                
                return video_info
                
        except Exception as e:
            logger.error(f"Error extrayendo video {url}: {e}")
            
            # Intentar con proxy diferente si falla
            if self.proxy_rotator and "proxy" in str(e).lower():
                logger.info("Intentando con proxy diferente...")
                return self._retry_with_different_proxy(url, extract_audio, quality)
            
            return None
    
    def _retry_with_different_proxy(self, url: str, extract_audio: bool, 
                                   quality: str) -> Optional[VideoInfo]:
        """Reintenta la extracción con un proxy diferente"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if self.proxy_rotator:
                    current_proxy = self.proxy_rotator.get_next_proxy()
                    logger.info(f"Reintento {attempt + 1} con proxy: {current_proxy}")
                
                return self.extract_video_info(url, extract_audio, quality)
                
            except Exception as e:
                logger.warning(f"Reintento {attempt + 1} falló: {e}")
                continue
        
        return None
    
    def extract_playlist_info(self, url: str, max_videos: int = 50) -> Optional[PlaylistInfo]:
        """Extrae información de una playlist de YouTube"""
        try:
            options = self.get_yt_dlp_options({
                'extract_flat': True,  # Solo metadata, no descargar
                'playlistend': max_videos
            })
            
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info or 'entries' not in info:
                    logger.error("No se pudo extraer información de la playlist")
                    return None
                
                # Extraer información detallada de cada video
                videos = []
                for entry in info['entries'][:max_videos]:
                    if entry:
                        video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}"
                        video_info = self.extract_video_info(video_url)
                        if video_info:
                            videos.append(video_info)
                
                playlist_info = PlaylistInfo(
                    id=info.get('id', ''),
                    title=info.get('title', 'Unknown Playlist'),
                    description=info.get('description'),
                    uploader=info.get('uploader'),
                    uploader_id=info.get('uploader_id'),
                    webpage_url=info.get('webpage_url', url),
                    entries=videos,
                    playlist_count=len(videos),
                    extracted_at=datetime.now()
                )
                
                logger.info(f"Playlist extraída: {playlist_info.title} ({len(videos)} videos)")
                return playlist_info
                
        except Exception as e:
            logger.error(f"Error extrayendo playlist {url}: {e}")
            return None
    
    def _convert_to_video_info(self, yt_info: Dict[str, Any]) -> VideoInfo:
        """Convierte la información de yt-dlp a nuestro modelo"""
        
        # Convertir formatos
        formats = []
        if 'formats' in yt_info:
            for fmt in yt_info['formats']:
                format_obj = VideoFormat(
                    format_id=fmt.get('format_id', ''),
                    ext=fmt.get('ext', ''),
                    quality=fmt.get('quality'),
                    filesize=fmt.get('filesize'),
                    url=fmt.get('url', ''),
                    acodec=fmt.get('acodec'),
                    vcodec=fmt.get('vcodec'),
                    resolution=fmt.get('resolution'),
                    fps=fmt.get('fps'),
                    tbr=fmt.get('tbr')
                )
                formats.append(format_obj)
        
        # Convertir thumbnails
        thumbnails = []
        if 'thumbnails' in yt_info:
            for thumb in yt_info['thumbnails']:
                thumbnail_obj = VideoThumbnail(
                    url=thumb.get('url', ''),
                    height=thumb.get('height'),
                    width=thumb.get('width'),
                    resolution=thumb.get('resolution')
                )
                thumbnails.append(thumbnail_obj)
        
        # Obtener mejores URLs de video y audio
        best_video_url = None
        best_audio_url = None
        
        if 'url' in yt_info:
            best_video_url = yt_info['url']
        
        # Buscar mejor formato de audio
        if formats:
            audio_formats = [f for f in formats if f.vcodec == 'none' or f.vcodec is None]
            if audio_formats:
                best_audio_url = audio_formats[0].url
        
        # Formatear duración
        duration_string = None
        if yt_info.get('duration'):
            duration = int(yt_info['duration'])
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            if hours > 0:
                duration_string = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_string = f"{minutes:02d}:{seconds:02d}"
        
        video_info = VideoInfo(
            id=yt_info.get('id', ''),
            title=yt_info.get('title', 'Unknown Title'),
            description=yt_info.get('description'),
            uploader=yt_info.get('uploader'),
            uploader_id=yt_info.get('uploader_id'),
            upload_date=yt_info.get('upload_date'),
            duration=yt_info.get('duration'),
            duration_string=duration_string,
            view_count=yt_info.get('view_count'),
            like_count=yt_info.get('like_count'),
            dislike_count=yt_info.get('dislike_count'),
            average_rating=yt_info.get('average_rating'),
            age_limit=yt_info.get('age_limit'),
            webpage_url=yt_info.get('webpage_url', ''),
            original_url=yt_info.get('original_url', ''),
            thumbnails=thumbnails,
            formats=formats,
            best_video_url=best_video_url,
            best_audio_url=best_audio_url,
            tags=yt_info.get('tags', []),
            categories=yt_info.get('categories', []),
            channel=yt_info.get('channel'),
            channel_id=yt_info.get('channel_id'),
            channel_url=yt_info.get('channel_url'),
            extracted_at=datetime.now()
        )
        
        return video_info
    
    def search_videos(self, query: str, max_results: int = 10) -> List[VideoInfo]:
        """Busca videos en YouTube por query"""
        try:
            search_url = f"ytsearch{max_results}:{query}"
            
            options = self.get_yt_dlp_options({
                'extract_flat': True,
                'quiet': True
            })
            
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(search_url, download=False)
                
                videos = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            video_info = self.extract_video_info(video_url)
                            if video_info:
                                videos.append(video_info)
                
                logger.info(f"Búsqueda completada: {len(videos)} videos encontrados para '{query}'")
                return videos
                
        except Exception as e:
            logger.error(f"Error buscando videos: {e}")
            return []
    
    def get_video_stream_url(self, video_id: str, quality: str = "best") -> Optional[str]:
        """Obtiene URL directa de stream de video"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            video_info = self.extract_video_info(url, quality=quality)
            
            if video_info and video_info.best_video_url:
                return video_info.best_video_url
                
        except Exception as e:
            logger.error(f"Error obteniendo stream URL: {e}")
            
        return None
    
    def get_channel_videos(self, channel_url: str, max_videos: int = 20) -> List[VideoInfo]:
        """Obtiene videos de un canal"""
        try:
            # Agregar /videos al final si no está presente
            if not channel_url.endswith('/videos'):
                channel_url = channel_url.rstrip('/') + '/videos'
            
            options = self.get_yt_dlp_options({
                'extract_flat': True,
                'playlistend': max_videos
            })
            
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                videos = []
                if 'entries' in info:
                    for entry in info['entries'][:max_videos]:
                        if entry:
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            video_info = self.extract_video_info(video_url)
                            if video_info:
                                videos.append(video_info)
                
                logger.info(f"Canal procesado: {len(videos)} videos extraídos")
                return videos
                
        except Exception as e:
            logger.error(f"Error extrayendo videos del canal: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del extractor"""
        stats = {
            'proxies_configured': Config.USE_PROXIES,
            'cookies_configured': Config.COOKIES_FULL_PATH.exists(),
            'browser_cookies': Config.USE_BROWSER_COOKIES
        }
        
        if self.proxy_rotator:
            stats['proxy_stats'] = self.proxy_rotator.get_stats()
        
        return stats