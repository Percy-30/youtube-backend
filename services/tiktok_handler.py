import re
import json
import requests
from bs4 import BeautifulSoup
import yt_dlp
import logging
from typing import Optional
from utils.constants import USER_AGENTS, REQUEST_TIMEOUT
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def handle_tiktok(url: str) -> dict:
    try:
        # Método 1: yt-dlp optimizado
        try:
            result = await _handle_tiktok_ytdlp(url)
            if result and result.get("video_url"):
                return result
        except Exception as e:
            logger.warning(f"yt-dlp no logró un enlace válido, intentando APIs de terceros {str(e)}")

        # Método 2: Extracción manual del HTML
        try:
            result = await _handle_tiktok_manual(url)
            if result and result.get("video_url"):
                return result
        except Exception as e:
            logger.warning(f"Extracción manual falló para TikTok: {str(e)}")

        # Método 3: API de terceros
        try:
            result = await _handle_tiktok_api(url)
            if result and result.get("video_url"):
                return result
        except Exception as e:
            logger.warning(f"API no oficial falló para TikTok: {str(e)}")

        raise HTTPException(
            status_code=404, 
            detail="No se pudo extraer el video de TikTok después de varios intentos."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado con TikTok: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno al procesar TikTok: {str(e)}")

async def _handle_tiktok_ytdlp(url: str) -> Optional[dict]:
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'forceurl': True,
            'simulate': True,
            'skip_download': True,
            'merge_output_format': 'mp4',
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Referer': 'https://www.tiktok.com/',
            },
            'extractor_retries': 3,
            'socket_timeout': 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None

            video_url = info.get('url')
            if not video_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('url') and f.get('protocol') in ('http', 'https'):
                        video_url = f['url']
                        break
            
            if not video_url or not any(domain in video_url for domain in ['tiktokcdn.com', 'tiktokv.com', 'muscdn.com']):
                return None

            return {
                "status": "success",
                "platform": "tiktok",
                "title": info.get('title', 'Video de TikTok'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "video_url": video_url,
                "width": info.get('width'),
                "height": info.get('height'),
                "uploader": info.get('uploader', ''),
                "view_count": info.get('view_count', 0),
                "method": "ytdlp_optimized"
            }

    except Exception as e:
        logger.warning(f"yt-dlp optimizado falló: {str(e)}")
        return None

async def _handle_tiktok_manual(url: str) -> Optional[dict]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
        }

        session = requests.Session()
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        video_data = None
        for script in soup.find_all('script'):
            if script.string and 'SIGI_STATE' in script.string:
                try:
                    match = re.search(r'window\[\'SIGI_STATE\'\]=({.*?});window\[', script.string)
                    if match:
                        data = json.loads(match.group(1))
                        for key, value in data.get('ItemModule', {}).items():
                            if isinstance(value, dict) and 'video' in value:
                                video_data = value
                                break
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue

        if not video_data:
            for script in soup.find_all('script'):
                if script.string and '__UNIVERSAL_DATA_FOR_REHYDRATION__' in script.string:
                    try:
                        match = re.search(r'__UNIVERSAL_DATA_FOR_REHYDRATION__=({.*?});', script.string)
                        if match:
                            data = json.loads(match.group(1))
                            detail_data = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {})
                            if 'itemInfo' in detail_data:
                                video_data = detail_data['itemInfo']['itemStruct']
                                break
                    except (json.JSONDecodeError, AttributeError):
                        continue

        if not video_data:
            return None

        video_info = video_data.get('video', {})
        video_url = video_info.get('downloadAddr') or video_info.get('playAddr')
        
        desc = video_data.get('desc', 'Video de TikTok')
        author = video_data.get('author', {})
        stats = video_data.get('stats', {})
        
        return {
            "status": "success",
            "platform": "tiktok",
            "title": desc,
            "thumbnail": video_info.get('cover', ''),
            "duration": video_info.get('duration', 0),
            "video_url": video_url,
            "width": video_info.get('width'),
            "height": video_info.get('height'),
            "uploader": author.get('uniqueId', ''),
            "view_count": stats.get('playCount', 0),
            "method": "manual_extraction"
        }

    except Exception as e:
        logger.warning(f"Extracción manual de TikTok falló: {str(e)}")
        return None

async def _handle_tiktok_api(url: str) -> Optional[dict]:
    try:
        video_id = extract_tiktok_id(url)
        if not video_id:
            return None

        apis = [
            f"https://www.tikwm.com/api/?url={url}"
        ]

        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    if "tikwm.com" in api_url and data.get('code') == 0:
                        video_data = data.get('data', {})
                        return {
                            "status": "success",
                            "platform": "tiktok",
                            "title": video_data.get('title', 'Video de TikTok'),
                            "thumbnail": video_data.get('cover', ''),
                            "duration": video_data.get('duration', 0),
                            "video_url": video_data.get('play', ''),
                            "uploader": video_data.get('author', {}).get('unique_id', ''),
                            "view_count": video_data.get('play_count', 0),
                            "method": "tikwm_api"
                        }

            except Exception as e:
                logger.warning(f"API {api_url} falló: {str(e)}")
                continue

        return None

    except Exception as e:
        logger.warning(f"Método de API falló: {str(e)}")
        return None

def extract_tiktok_id(url: str) -> Optional[str]:
    patterns = [
        r'/video/(\d+)',
        r'tiktok\.com.*?/(\d{19})',
        r'vm\.tiktok\.com/([A-Za-z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
