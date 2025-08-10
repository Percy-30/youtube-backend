import os
import random
import tempfile
import logging

from fastapi import HTTPException

import yt_dlp

from utils.headers import USER_AGENTS
from utils.url_utils import validate_url

logger = logging.getLogger(__name__)

USER_AGENT = random.choice(USER_AGENTS)

async def handle_youtube(url: str, cookies: str | None = None, force_ytdlp: bool = False) -> dict:
    """
    Extrae información de un video de YouTube usando yt-dlp.
    Parámetros:
    - url: URL del video YouTube
    - cookies: string con cookies en formato netscape para mejorar acceso
    - force_ytdlp: si True intenta modos alternativos en yt-dlp para evadir bloqueos
    """

    # Validar URL
    validate_url(url)

    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['android', 'web'],
            }
        },
        'http_headers': {
            'User-Agent': USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
        'socket_timeout': 30,
    }

    cookies_path = None

    try:
        # Guardar cookies temporales si se proporcionan
        if cookies:
            fd, cookies_path = tempfile.mkstemp(suffix='.txt')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(cookies)
            ydl_opts['cookiefile'] = cookies_path
        # Usar archivo local si existe y no se pasan cookies
        elif os.path.exists("cookies/youtube_cookies.txt"):
            logger.info("✅ Cookie local encontrada y usada")
            ydl_opts['cookiefile'] = "cookies/youtube_cookies.txt"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("No se pudo extraer información del video")

            video_url = None
            if 'url' in info:
                video_url = info['url']
            elif 'formats' in info:
                # Elegir mejor formato http/https disponible
                formats = sorted(info['formats'], key=lambda f: (f.get('height', 0), f.get('tbr', 0)), reverse=True)
                for f in formats:
                    if f.get('url') and f.get('protocol') in ('http', 'https'):
                        video_url = f['url']
                        break

            if not video_url:
                if force_ytdlp:
                    # Intentar forzar con cliente alternativo
                    return await _force_ytdlp_youtube(url, ydl_opts)
                raise Exception("No se encontró URL de video válida")

            return {
                "status": "success",
                "platform": "youtube",
                "title": info.get('title', 'Video de YouTube'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "video_url": video_url,
                "width": info.get('width'),
                "height": info.get('height'),
                "uploader": info.get('uploader', ''),
                "view_count": info.get('view_count', 0),
                "method": "ytdlp_with_cookies" if ('cookiefile' in ydl_opts) else "ytdlp"
            }

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Sign in to confirm you're not a bot" in msg:
            raise HTTPException(status_code=403, detail="YouTube requiere cookies válidas. Usa 'Get cookies.txt'.")
        raise HTTPException(status_code=500, detail=f"Error al descargar de YouTube: {msg}")

    except Exception as e:
        logger.error(f"Error inesperado con YouTube: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    finally:
        if cookies_path and os.path.exists(cookies_path):
            os.unlink(cookies_path)

async def _force_ytdlp_youtube(url: str, base_opts: dict) -> dict:
    """
    Fuerza la extracción usando diferentes player_client para evadir bloqueos.
    """
    clients = [
        {'player_client': ['android'], 'format': 'best[height<=480]'},
        {'player_client': ['tv_embedded'], 'format': 'best[height<=720]'},
        {'player_client': ['web'], 'format': 'best[height<=360]'},
    ]

    for client in clients:
        try:
            opts = base_opts.copy()
            opts['extractor_args']['youtube']['player_client'] = client['player_client']
            opts['format'] = client['format']
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'url' in info:
                    return {
                        "status": "success",
                        "platform": "youtube",
                        "title": info.get('title'),
                        "video_url": info['url'],
                        "method": f"forced_{client['player_client'][0]}"
                    }
        except Exception:
            continue

    raise HTTPException(status_code=403, detail="YouTube bloqueó la extracción. Proporcione cookies.")
