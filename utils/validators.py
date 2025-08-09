# app/utils/validators.py

import re
from urllib.parse import urlparse
from fastapi import HTTPException
from typing import Optional

def validate_url(url: str) -> urlparse:
    """Valida y parsea la URL de entrada."""
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError("URL inválida")
        return parsed
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL inválida: {str(e)}")

def extract_tiktok_id(url: str) -> Optional[str]:
    """Extrae el ID del video de TikTok"""
    from .constants import TIKTOK_ID_PATTERNS
    
    for pattern in TIKTOK_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_valid_video_url(video_url: str, platform: str) -> bool:
    """Valida si una URL de video es válida para la plataforma específica"""
    from .constants import VALID_DOMAINS
    
    if not video_url:
        return False
    
    if platform not in VALID_DOMAINS:
        return True  # Si no conocemos la plataforma, asumimos que es válida
    
    return any(domain in video_url for domain in VALID_DOMAINS[platform])

def get_platform_from_url(url: str) -> str:
    """Determina la plataforma basada en la URL"""
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

def clean_facebook_url(video_url: str) -> str:
    """Limpia y valida URLs de video de Facebook"""
    if video_url:
        return video_url.replace('\\/', '/')
    return video_url