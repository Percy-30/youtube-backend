import re
import json
import requests
from bs4 import BeautifulSoup
import yt_dlp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def handle_tiktok(url: str) -> Optional[dict]:
    for fn in [_handle_tiktok_ytdlp, _handle_tiktok_manual, _handle_tiktok_api]:
        res = await fn(url)
        if res:
            return res
    return None

async def _handle_tiktok_ytdlp(url: str) -> Optional[dict]:
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'skip_download': True,
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Referer': 'https://www.tiktok.com/',
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            video_url = info.get('url') or (info.get('formats') and next((f['url'] for f in info['formats'] if f.get('url')), None))
            if not video_url:
                return None
            if not any(domain in video_url for domain in ['tiktokcdn.com', 'tiktokv.com', 'muscdn.com']):
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
        logger.warning(f"yt-dlp TikTok falló: {e}")
        return None

async def _handle_tiktok_manual(url: str) -> Optional[dict]:
    try:
        session = requests.Session()
        resp = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')

        video_data = None
        for script in soup.find_all('script'):
            if script.string and 'SIGI_STATE' in script.string:
                match = re.search(r"window\['SIGI_STATE'\]=({.*?});window\[", script.string)
                if match:
                    data = json.loads(match.group(1))
                    for v in data.get('ItemModule', {}).values():
                        if 'video' in v:
                            video_data = v
                            break
                if video_data:
                    break

        if not video_data:
            for script in soup.find_all('script'):
                if script.string and '__UNIVERSAL_DATA_FOR_REHYDRATION__' in script.string:
                    match = re.search(r'__UNIVERSAL_DATA_FOR_REHYDRATION__=({.*?});', script.string)
                    if match:
                        data = json.loads(match.group(1))
                        video_data = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', None)
                        if video_data:
                            break
        if not video_data:
            return None

        video_info = video_data.get('video', {})
        video_url = video_info.get('downloadAddr') or video_info.get('playAddr')
        return {
            "status": "success",
            "platform": "tiktok",
            "title": video_data.get('desc', 'Video de TikTok'),
            "thumbnail": video_info.get('cover', ''),
            "duration": video_info.get('duration', 0),
            "video_url": video_url,
            "width": video_info.get('width'),
            "height": video_info.get('height'),
            "uploader": video_data.get('author', {}).get('uniqueId', ''),
            "view_count": video_data.get('stats', {}).get('playCount', 0),
            "method": "manual_extraction"
        }
    except Exception as e:
        logger.warning(f"Manual TikTok falló: {e}")
        return None

async def _handle_tiktok_api(url: str) -> Optional[dict]:
    try:
        video_id = extract_tiktok_id(url)
        if not video_id:
            return None
        api_url = f"https://www.tikwm.com/api/?url={url}"
        response = requests.get(api_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
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
        return None
    except Exception as e:
        logger.warning(f"TikTok API método falló: {e}")
        return None

def extract_tiktok_id(url: str) -> Optional[str]:
    patterns = [
        r'/video/(\d+)',
        r'tiktok\.com.*?/(\d{19})',
        r'vm\.tiktok\.com/([A-Za-z0-9]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None
