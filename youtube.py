from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend on Netlify to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define request model
class DownloadRequest(BaseModel):
    url: str
    quality: str
    save_path: str  # User-defined save path

# Define quality formats for yt-dlp
QUALITY_MAP = {
    "highest": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height=1080]+bestaudio/best",
    "720p": "bestvideo[height=720]+bestaudio/best",
    "audio": "bestaudio"
}

@app.post("/download/")
def download_video(request: DownloadRequest):
    """Downloads a video/audio from YouTube to a user-specified directory."""
    
    if request.quality not in QUALITY_MAP:
        raise HTTPException(status_code=400, detail="Invalid quality option.")

    # Use the user-specified save path or default to 'downloads' folder
    save_path = request.save_path.strip() or "downloads"

    # Ensure the directory exists
    os.makedirs(save_path, exist_ok=True)

    ydl_opts = {
        'format': QUALITY_MAP[request.quality],
        'outtmpl': f"{save_path}/%(title)s.%(ext)s",
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
        return {"message": f"Download started successfully! Saved to {save_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
