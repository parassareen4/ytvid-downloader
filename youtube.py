from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

# CORS: Allow frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class DownloadRequest(BaseModel):
    url: str
    quality: str

# Directory where files will be saved
SAVE_PATH = "downloads"
os.makedirs(SAVE_PATH, exist_ok=True)

# Video quality formats for yt-dlp
QUALITY_MAP = {
    "highest": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height=1080]+bestaudio/best",
    "720p": "bestvideo[height=720]+bestaudio/best",
    "audio": "bestaudio"
}

# Path to cookies.txt (Make sure you place it in the backend folder)
COOKIES_PATH = "cookies.txt"

@app.post("/download/")
def download_video(request: DownloadRequest):
    """Downloads a video/audio from YouTube."""
    if request.quality not in QUALITY_MAP:
        raise HTTPException(status_code=400, detail="Invalid quality option.")

    ydl_opts = {
        'format': QUALITY_MAP[request.quality],
        'outtmpl': f"{SAVE_PATH}/%(title)s.%(ext)s",
        'merge_output_format': 'mp4' if request.quality != "audio" else 'mp3',
        'postprocessors': [],
        'cookiefile': COOKIES_PATH  # Use YouTube cookies for authentication
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
        return {"message": "Download started successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
