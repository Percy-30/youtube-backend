from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import yt_dlp
import logging

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Habilitar CORS para cualquier frontend/app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Restringe esto en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/video")
async def extract_video_info(url: str, cookie: Optional[str] = Header(None)):
    logger.info(f"URL recibida: {url}")
    logger.info(f"Cookies recibidas: {cookie is not None}")

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'nocheckcertificate': True,
        'cookiefile': None,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) Chrome/115.0.0.0 Mobile Safari/537.36'
        }
    }

    if cookie:
        ydl_opts['http_headers']['Cookie'] = cookie

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            best = next(
                (f for f in info.get("formats", []) if f.get("ext") == "mp4" and f.get("vcodec") != "none" and f.get("acodec") != "none"),
                None
            )

            return {
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "video_url": best.get("url") if best else "",
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "platform": "YouTube"
            }
    except Exception as e:
        logger.error(f"Error al procesar el video: {e}")
        return JSONResponse(status_code=500, content={"error": "No se pudo analizar el video"})