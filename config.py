# config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# Cargar variables de entorno
load_dotenv()

class Config:
    # ==================== CONFIGURACIÓN DE LA APLICACIÓN ====================
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ENV = os.getenv("ENV", "development")
    
    # ==================== CONFIGURACIÓN DE PROXIES ====================
    USE_PROXIES = os.getenv("USE_PROXIES", "False").lower() == "true"
    PROXY_LIST = [p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()]
    PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", 10))
    PROXY_ROTATION_INTERVAL = int(os.getenv("PROXY_ROTATION_INTERVAL", 300))  # 5 minutos
    
    # ==================== CONFIGURACIÓN DE COOKIES ====================
    COOKIES_PATH = os.getenv("COOKIES_PATH", "cookies.txt")
    USE_BROWSER_COOKIES = os.getenv("USE_BROWSER_COOKIES", "False").lower() == "true"
    BROWSER_NAME = os.getenv("BROWSER_NAME", "chrome")
    
    # ==================== RATE LIMITING ====================
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 30))
    MAX_REQUESTS_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_HOUR", 500))
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "True").lower() == "true"
    
    # ==================== USER AGENTS ====================
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ]
    USER_AGENT = os.getenv("USER_AGENT", USER_AGENTS[0])
    
    # ==================== RUTAS DEL PROYECTO ====================
    PROJECT_ROOT = Path(__file__).parent
    COOKIES_FULL_PATH = PROJECT_ROOT / COOKIES_PATH
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # Crear directorios si no existen
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # ==================== CONFIGURACIÓN YT-DLP ====================
    YT_DLP_OPTIONS = {
        'format': os.getenv("YT_DLP_FORMAT", "best[height<=1080]/best"),
        'extractaudio': False,
        'audioformat': 'mp3',
        'audioquality': '192K',
        'outtmpl': '%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'ignoreerrors': False,
        'no_warnings': True,
        'extractflat': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'subtitleslangs': ['en', 'es'],
        'concurrent_fragment_downloads': 4,
        'retries': 3,
        'fragment_retries': 3,
        'socket_timeout': 30,
        'http_chunk_size': 1048576,  # 1MB chunks
    }
    
    # ==================== CONFIGURACIÓN DE SNAPTUBE ====================
    # Configuraciones específicas para emular Snaptube
    SNAPTUBE_CONFIG = {
        'default_video_quality': os.getenv("DEFAULT_VIDEO_QUALITY", "720p"),
        'default_audio_quality': os.getenv("DEFAULT_AUDIO_QUALITY", "128K"),
        'max_search_results': int(os.getenv("MAX_SEARCH_RESULTS", 20)),
        'max_playlist_videos': int(os.getenv("MAX_PLAYLIST_VIDEOS", 50)),
        'max_channel_videos': int(os.getenv("MAX_CHANNEL_VIDEOS", 30)),
        'enable_thumbnails': os.getenv("ENABLE_THUMBNAILS", "True").lower() == "true",
        'thumbnail_sizes': ['maxresdefault', 'hqdefault', 'mqdefault', 'default'],
        'supported_formats': {
            'video': ['mp4', 'webm', '3gp'],
            'audio': ['mp3', 'm4a', 'webm']
        },
        'quality_priorities': {
            'video': ['1080p', '720p', '480p', '360p', '240p'],
            'audio': ['192K', '128K', '96K', '64K']
        }
    }
    
    # ==================== CONFIGURACIÓN DE CACHE ====================
    USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "False").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1 hora
    
    # ==================== CONFIGURACIÓN DE LOGGING ====================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "api.log"
    
    # ==================== CONFIGURACIÓN DE SEGURIDAD ====================
    API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "False").lower() == "true"
    API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]
    
    # ==================== TIMEOUTS Y LÍMITES ====================
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", 7200))  # 2 horas
    MAX_PLAYLIST_SIZE = int(os.getenv("MAX_PLAYLIST_SIZE", 100))
    
    # ==================== CONFIGURACIÓN DE EXTRACCIÓN ====================
    EXTRACT_COMMENTS = os.getenv("EXTRACT_COMMENTS", "False").lower() == "true"
    EXTRACT_SUBTITLES = os.getenv("EXTRACT_SUBTITLES", "False").lower() == "true"
    PREFERRED_CODECS = {
        'video': ['h264', 'vp9', 'av01'],
        'audio': ['aac', 'opus', 'mp3']
    }
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """Obtiene un User-Agent aleatorio"""
        import random
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida la configuración"""
        errors = []
        
        # Validar proxies si están habilitados
        if cls.USE_PROXIES and not cls.PROXY_LIST:
            errors.append("USE_PROXIES está habilitado pero PROXY_LIST está vacío")
        
        # Validar cookies
        if cls.USE_BROWSER_COOKIES and not cls.BROWSER_NAME:
            errors.append("USE_BROWSER_COOKIES está habilitado pero BROWSER_NAME no está configurado")
        
        # Validar API keys si están requeridas
        if cls.API_KEY_REQUIRED and not cls.API_KEYS:
            errors.append("API_KEY_REQUIRED está habilitado pero API_KEYS está vacío")
        
        if errors:
            for error in errors:
                print(f"⚠️  Error de configuración: {error}")
            return False
        
        return True
    
    @classmethod
    def print_config_summary(cls):
        """Imprime resumen de configuración"""
        print("🔧 Configuración de YouTube Extractor API:")
        print(f"   🌐 Host: {cls.APP_HOST}:{cls.APP_PORT}")
        print(f"   🐛 Debug: {cls.DEBUG}")
        print(f"   🌍 Proxies: {cls.USE_PROXIES} ({len(cls.PROXY_LIST)} configurados)")
        print(f"   🍪 Cookies: {cls.USE_BROWSER_COOKIES} (Browser: {cls.BROWSER_NAME})")
        print(f"   ⏱️  Rate Limit: {cls.MAX_REQUESTS_PER_MINUTE}/min")
        print(f"   💾 Cache Redis: {cls.USE_REDIS_CACHE}")
        print(f"   🔐 API Key Required: {cls.API_KEY_REQUIRED}")
        print(f"   📁 Data Dir: {cls.DATA_DIR}")
        print(f"   📋 Logs Dir: {cls.LOGS_DIR}")

# Validar configuración al importar
if not Config.validate_config():
    print("❌ Hay errores en la configuración. Revisa las variables de entorno.")