# services/snaptube_converter.py
from typing import List, Dict, Any, Optional
from models.video_info import VideoInfo, VideoFormat
from models.snaptube_models import (
    SnaptubeVideoInfo, DownloadOption, SearchResult, 
    TrendingVideo, FormatGroup
)
import re

class EnhancedSnaptubeConverter:
    """Convertidor mejorado para formato Snaptube"""
    
    @staticmethod
    def format_filesize(bytes_size: Optional[int]) -> str:
        """Formatea tamaño de archivo de forma legible"""
        if not bytes_size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"~{bytes_size:.1f}{unit}"
            bytes_size /= 1024
        return f"~{bytes_size:.1f}TB"
    
    @staticmethod
    def get_quality_label(resolution: str, fps: Optional[float] = None) -> str:
        """Obtiene etiqueta de calidad mejorada"""
        if not resolution:
            return "Unknown"
        
        # Extraer altura de resolución
        height_match = re.search(r'(\d+)p?$', resolution)
        if height_match:
            height = int(height_match.group(1))
            label = f"{height}p"
            
            # Agregar FPS si está disponible y es relevante
            if fps and fps > 30:
                label += f" {int(fps)}fps"
            
            return label
        
        return resolution
    
    @staticmethod
    def categorize_formats(formats: List[VideoFormat]) -> FormatGroup:
        """Categoriza formatos por calidad"""
        group = FormatGroup()
        
        for fmt in formats:
            format_dict = fmt.dict()
            
            if not fmt.vcodec or fmt.vcodec == 'none':
                continue  # Saltar formatos solo de audio
            
            height = 0
            if fmt.resolution:
                height_match = re.search(r'(\d+)p?$', fmt.resolution)
                if height_match:
                    height = int(height_match.group(1))
            
            # Categorizar por altura
            if height >= 1080:
                group.high_quality.append(format_dict)
            elif height >= 720:
                group.medium_quality.append(format_dict)
            elif height >= 480:
                group.low_quality.append(format_dict)
            elif height > 0:
                group.mobile.append(format_dict)
        
        return group
    
    @staticmethod
    def generate_smart_download_options(video_info: VideoInfo) -> List[DownloadOption]:
        """Genera opciones de descarga inteligentes basadas en formatos disponibles"""
        options = []
        seen_qualities = set()
        
        # Procesar formatos de video disponibles
        video_formats = [f for f in video_info.formats if f.vcodec and f.vcodec != 'none']
        video_formats.sort(key=lambda x: x.quality or 0, reverse=True)
        
        for fmt in video_formats:
            if not fmt.resolution:
                continue
                
            quality_label = EnhancedSnaptubeConverter.get_quality_label(fmt.resolution, fmt.fps)
            
            if quality_label in seen_qualities:
                continue
            seen_qualities.add(quality_label)
            
            size_estimate = "Unknown"
            if fmt.filesize:
                size_estimate = EnhancedSnaptubeConverter.format_filesize(fmt.filesize)
            elif video_info.duration:
                # Estimación basada en duración
                size_estimate = EnhancedSnaptubeConverter.estimate_filesize(
                    video_info.duration, quality_label, "video"
                )
            
            # Marcar como recomendado si es 720p
            recommended = "720p" in quality_label
            
            options.append(DownloadOption(
                type="video",
                quality=quality_label,
                format="mp4",
                size_estimate=size_estimate,
                recommended=recommended,
                format_id=fmt.format_id,
                actual_filesize=fmt.filesize
            ))
        
        # Agregar opciones de audio
        audio_qualities = [
            ("High Quality", "192K"),
            ("Standard", "128K"), 
            ("Low Quality", "96K")
        ]
        
        for i, (quality_name, bitrate) in enumerate(audio_qualities):
            size_estimate = "Unknown"
            if video_info.duration:
                size_estimate = EnhancedSnaptubeConverter.estimate_filesize(
                    video_info.duration, quality_name.lower(), "audio"
                )
            
            options.append(DownloadOption(
                type="audio",
                quality=f"{quality_name} ({bitrate})",
                format="mp3",
                size_estimate=size_estimate,
                recommended=(i == 1)  # Standard como recomendado
            ))
        
        return options
    
    @staticmethod
    def estimate_filesize(duration: int, quality: str, format_type: str) -> str:
        """Estimación mejorada de tamaño de archivo"""
        if not duration:
            return "Unknown"
        
        # Tasas mejoradas en MB por minuto
        rates = {
            "video": {
                "2160p": 15.0,  # 4K
                "1440p": 10.0,  # 2K  
                "1080p": 8.0,
                "720p": 5.0,
                "480p": 3.0,
                "360p": 2.0,
                "240p": 1.0,
                "144p": 0.5
            },
            "audio": {
                "high": 1.5,     # 320kbps
                "standard": 1.0,  # 128kbps
                "low": 0.6       # 96kbps
            }
        }
        
        minutes = duration / 60
        
        # Extraer altura de quality si es video
        if format_type == "video":
            height_match = re.search(r'(\d+)p', quality.lower())
            if height_match:
                height = height_match.group(1) + "p"
                rate = rates["video"].get(height, 3.0)
            else:
                rate = 3.0  # Default
        else:
            quality_key = quality.lower().split()[0]  # "high quality" -> "high"
            rate = rates["audio"].get(quality_key, 1.0)
        
        estimated_mb = minutes * rate
        
        if estimated_mb < 1:
            return f"~{int(estimated_mb * 1024)}KB"
        elif estimated_mb < 1024:
            return f"~{int(estimated_mb)}MB"
        else:
            return f"~{estimated_mb/1024:.1f}GB"
    
    @staticmethod
    def enhance_video_info(video_info: VideoInfo) -> SnaptubeVideoInfo:
        """Convierte VideoInfo a SnaptubeVideoInfo mejorado"""
        # Seleccionar mejor thumbnail
        best_thumbnail = None
        if video_info.thumbnails:
            # Preferir thumbnails medianos (no muy pequeños ni muy grandes)
            sorted_thumbs = sorted(
                video_info.thumbnails,
                key=lambda x: abs((x.width or 480) - 480) if x.width else 999
            )
            best_thumbnail = sorted_thumbs[0].url
        
        # Formatear descripción
        description = None
        if video_info.description:
            description = (video_info.description[:150] + "...") if len(video_info.description) > 150 else video_info.description
        
        # Convertir thumbnails a formato simple
        thumbnails_data = []
        for thumb in video_info.thumbnails[:8]:  # Limitar a 8 thumbnails
            thumbnails_data.append({
                "url": thumb.url,
                "width": thumb.width,
                "height": thumb.height,
                "resolution": f"{thumb.width}x{thumb.height}" if thumb.width and thumb.height else None
            })
        
        return SnaptubeVideoInfo(
            id=video_info.id,
            title=video_info.title,
            description=description,
            duration=video_info.duration,
            duration_string=video_info.duration_string,
            view_count=video_info.view_count,
            uploader=video_info.uploader or "Unknown Uploader",
            upload_date=video_info.upload_date,
            thumbnail=best_thumbnail,
            thumbnails=thumbnails_data,
            webpage_url=video_info.webpage_url or f"https://youtube.com/watch?v={video_info.id}",
            has_formats=len(video_info.formats) > 0
        )
    
    @staticmethod
    def video_to_search_result(video_info: VideoInfo) -> SearchResult:
        """Convierte VideoInfo a SearchResult optimizado"""
        # Seleccionar mejor thumbnail para búsqueda (resolución media)
        thumbnail_url = ""
        if video_info.thumbnails:
            for thumb in video_info.thumbnails:
                if thumb.width and 320 <= thumb.width <= 480:
                    thumbnail_url = thumb.url
                    break
            if not thumbnail_url:
                thumbnail_url = video_info.thumbnails[0].url
        
        return SearchResult(
            id=video_info.id,
            title=video_info.title,
            uploader=video_info.uploader or "Unknown",
            duration_string=video_info.duration_string,
            view_count=video_info.view_count,
            thumbnail=thumbnail_url,
            url=video_info.webpage_url or f"https://youtube.com/watch?v={video_info.id}",
            upload_date=video_info.upload_date
        )
    
    @staticmethod
    def video_to_trending(video_info: VideoInfo) -> TrendingVideo:
        """Convierte VideoInfo a TrendingVideo"""
        thumbnail_url = None
        if video_info.thumbnails:
            # Para trending, usar thumbnail de alta calidad
            high_quality_thumbs = [t for t in video_info.thumbnails if t.width and t.width >= 480]
            if high_quality_thumbs:
                thumbnail_url = high_quality_thumbs[0].url
            else:
                thumbnail_url = video_info.thumbnails[0].url
        
        return TrendingVideo(
            id=video_info.id,
            title=video_info.title,
            uploader=video_info.uploader or "Unknown",
            duration_string=video_info.duration_string,
            view_count=video_info.view_count,
            thumbnail=thumbnail_url,
            url=video_info.webpage_url or f"https://youtube.com/watch?v={video_info.id}"
        )