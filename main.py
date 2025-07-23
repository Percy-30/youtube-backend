from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from yt_dlp import YoutubeDL
import uvicorn

app = FastAPI()

# CORS para que tu app Android pueda acceder sin restricciones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia por el dominio exacto de tu app si prefieres más seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/youtube")
async def youtube_info(url: str = Query(...), request: Request = None):
    cookies = request.headers.get("cookie") or request.headers.get("Cookie")

    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True,
        "skip_download": True,
        "cookiefile": None,
        "format": "best",
    }

    # Usamos cookies si las recibimos
    if cookies:
        ydl_opts["http_headers"] = {
            "Cookie": cookies,
            "User-Agent": "Mozilla/5.0"
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", ""),
                "downloadUrl": info.get("url", ""),
                "thumbnail": info.get("thumbnail", ""),
                "duration": str(info.get("duration", 0)) + "s"
            }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"No se pudo procesar el video: {str(e)}"}
        )

# Para correr local (no necesario en Render)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)