from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    quality: str

# Define quality formats for yt-dlp
QUALITY_MAP = {
    "highest": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height=1080]+bestaudio/best",
    "720p": "bestvideo[height=720]+bestaudio/best",
    "audio": "bestaudio"
}

@app.post("/download/")
def download_video(request: DownloadRequest):
    """Downloads a video/audio from YouTube and returns it to the frontend."""
    if request.quality not in QUALITY_MAP:
        raise HTTPException(status_code=400, detail="Invalid quality option.")

    # Generate a unique filename
    filename = f"{uuid.uuid4()}.mp4" if request.quality != "audio" else f"{uuid.uuid4()}.mp3"
    file_path = os.path.join("downloads", filename)

    ydl_opts = {
        'format': QUALITY_MAP[request.quality],
        'outtmpl': file_path,
        'merge_output_format': 'mp4' if request.quality != "audio" else 'mp3',
        'postprocessors': []
    }

    if request.quality == "audio":
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # Return the file for frontend download
        return FileResponse(file_path, filename=os.path.basename(file_path), media_type="video/mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
