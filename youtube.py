from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import glob

app = FastAPI()

# CORS: Allow frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL for security
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
def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Downloads a video/audio from YouTube and returns it as a file."""
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
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)

            # Check for audio format and adjust extension
            if request.quality == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

        # Return the file as a response
        return FileResponse(filename, filename=os.path.basename(filename), media_type="application/octet-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
