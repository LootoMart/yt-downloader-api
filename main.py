from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class VideoRequest(BaseModel):
    url: str

@app.post("/fetch")
def fetch_video(req: VideoRequest):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "best",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(req.url, download=False)
        formats = []
        for f in info.get("formats", []):
            if f.get("filesize") and f.get("ext") in ["mp4", "webm", "m4a"]:
                formats.append({
                    "format_id": f["format_id"],
                    "ext": f["ext"],
                    "resolution": f.get("format_note") or f.get("height"),
                    "filesize_mb": round(f["filesize"] / 1024 / 1024, 2)
                })

        return {
            "title": info.get("title"),
            "channel": info.get("uploader"),
            "duration": str(info.get("duration")) + " sec",
            "thumbnail": info.get("thumbnail"),
            "formats": formats
        }

@app.get("/download")
def download_video(url: str, format_id: str):
    output_path = f"{uuid.uuid4()}.%(ext)s"
    ydl_opts = {
        "quiet": True,
        "format": format_id,
        "outtmpl": output_path,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return FileResponse(filename, filename=os.path.basename(filename), media_type='application/octet-stream')
