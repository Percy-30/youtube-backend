import re
import json
import requests
from bs4 import BeautifulSoup
import yt_dlp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def handle_facebook(url: str, headers: dict) -> Optional[dict]:
    for fn in [try_ytdlp_facebook, try_manual_facebook]:
        res = await fn(url, headers)
        if res:
            return res
    return None

async def try_ytdlp_facebook(url: str, headers: dict) -> Optional[dict]:
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'format': 'best',
            'http_headers': headers,
            'extractor_args': {'facebook': {'skip_dash_manifest': True}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            video_url = info.get('url')
            if not video_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('protocol') in ('http', 'https'):
                        video_url = f['url']
                        break
            if not video_url:
                return None
            return {
                "status": "success",
                "platform": "facebook",
                "title": info.get('title', 'Video de Facebook'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "video_url": video_url,
                "width": info.get('width'),
                "height": info.get('height')
            }
    except Exception as e:
        logger.warning(f"yt-dlp Facebook falló: {e}")
        return None

async def try_manual_facebook(url: str, headers: dict) -> Optional[dict]:
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        video_url = None
        meta_video = soup.find("meta", property="og:video") or soup.find("meta", property="og:video:url")
        if meta_video and meta_video.get("content"):
            video_url = meta_video["content"]
        if not video_url:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        video_url = data.get("contentUrl")
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("contentUrl"):
                                video_url = item["contentUrl"]
                                break
                    if video_url:
                        break
                except Exception:
                    continue
        if not video_url:
            for script in soup.find_all("script"):
                if not script.string:
                    continue
                patterns = [
                    r'"browser_native_hd_url":"([^"]+)"',
                    r'"browser_native_sd_url":"([^"]+)"',
                    r'src:\\"([^"]+\.mp4[^\\]*)\\"',
                    r'video_src":"([^"]+)"'
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string)
                    if matches:
                        video_url = matches[0].replace('\\/', '/')
                        break
                if video_url:
                    break
        if not video_url:
            video_tag = soup.find("video")
            if video_tag:
                sources = video_tag.find_all("source")
                for source in sources:
                    if source.get("src"):
                        video_url = source["src"]
                        break
        if not video_url:
            return None
        title_tag = soup.find("meta", property="og:title") or soup.find("title")
        thumbnail_tag = soup.find("meta", property="og:image")
        return {
            "status": "success",
            "platform": "facebook",
            "title": title_tag["content"] if title_tag and hasattr(title_tag, "content") else (title_tag.text if title_tag else "Video de Facebook"),
            "thumbnail": thumbnail_tag["content"] if thumbnail_tag else "",
            "video_url": video_url,
            "duration": 0,
            "width": None,
            "height": None
        }
    except Exception as e:
        logger.warning(f"Manual Facebook falló: {e}")
        return None
