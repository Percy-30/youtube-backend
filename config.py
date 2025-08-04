import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Configuración de la aplicación
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configuración de proxies
    USE_PROXIES = os.getenv("USE_PROXIES", "False").lower() == "true"
    PROXY_LIST = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []
    
    # Configuración de cookies
    COOKIES_PATH = os.getenv("COOKIES_PATH", "cookies.txt")
    USE_BROWSER_COOKIES = os.getenv("USE_BROWSER_COOKIES", "False").lower() == "true"
    BROWSER_NAME = os.getenv("BROWSER_NAME", "chrome")
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 30))
    
    # User Agent
    USER_AGENT = os.getenv("USER_AGENT", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Rutas del proyecto
    PROJECT_ROOT = Path(__file__).parent
    COOKIES_FULL_PATH = PROJECT_ROOT / COOKIES_PATH
    
    # Configuración yt-dlp
    YT_DLP_OPTIONS = {
        'format': 'best[height<=720]/best',
        'extractaudio': False,
        'audioformat': 'mp3',
        'outtmpl': '%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'ignoreerrors': False,
        'no_warnings': False,
        'extractflat': False,
        'writethumbnail': False,
        'writeinfojson': False,
    }