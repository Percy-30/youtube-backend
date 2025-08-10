import re
from urllib.parse import urlparse
from fastapi import HTTPException
from typing import Optional

VALID_DOMAINS = {
    'tiktok': ['tiktokcdn.com', 'tiktokv.com', 'muscdn.com'],
    'facebook': ['facebook.com', 'fbcdn.net'],
    'youtube': ['youtube.com', 'googlevideo.com', 'youtu.be']
}

def validate_url(url: str) -> urlparse:
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError("URL inválida")
        return parsed
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL inválida: {str(e)}")

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

def get_platform_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if "tiktok.com" in domain:
        return "tiktok"
    elif "facebook.com" in domain or "fb.watch" in domain:
        return "facebook"
    elif "youtube.com" in domain or "youtu.be" in domain:
        return "youtube"
    else:
        raise HTTPException(status_code=400, detail="Plataforma no soportada")
