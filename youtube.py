from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import shutil

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

# Directory where files will be temporarily saved
TEMP_PATH = "temp_downloads"
os.makedirs(TEMP_PATH, exist_ok=True)

# Public URL where downloaded files will be accessible
# Replace with your actual domain from Render or wherever you host this
PUBLIC_URL = "https://ytvid-downloader.onrender.com/download"

# Video quality formats for yt-dlp
QUALITY_MAP = {
    "highest": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height=1080]+bestaudio/best",
    "720p": "bestvideo[height=720]+bestaudio/best",
    "audio": "bestaudio"
}

# Path to cookies.txt (if needed)
COOKIES_PATH = "cookies.txt"

@app.post("/prepare/")
async def prepare_download(request: DownloadRequest):
    """Prepares a video for download and returns a download URL"""
    if request.quality not in QUALITY_MAP:
        raise HTTPException(status_code=400, detail="Invalid quality option.")
    
    # Create a unique ID for this download
    download_id = str(uuid.uuid4())
    download_dir = os.path.join(TEMP_PATH, download_id)
    os.makedirs(download_dir, exist_ok=True)
    
    ydl_opts = {
        'format': QUALITY_MAP[request.quality],
        'outtmpl': f"{download_dir}/%(title)s.%(ext)s",
        'merge_output_format': 'mp4' if request.quality != "audio" else 'mp3',
        'postprocessors': [],
    }
    
    # Use cookies file if it exists
    if os.path.exists(COOKIES_PATH):
        ydl_opts['cookiefile'] = COOKIES_PATH
    
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
                base_filename = os.path.basename(filename).rsplit(".", 1)[0] + ".mp3"
                filename = os.path.join(download_dir, base_filename)
            else:
                base_filename = os.path.basename(filename)
            
            # Create a download URL
            download_url = f"{PUBLIC_URL}/{download_id}/{base_filename}"
            
            # Schedule cleanup after some time (e.g., 1 hour)
            # background_tasks.add_task(clean_up_download, download_dir, 3600)
            
            return JSONResponse({
                "status": "success",
                "download_url": download_url,
                "filename": base_filename
            })
    
    except Exception as e:
        # Clean up in case of error
        shutil.rmtree(download_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{download_id}/{filename}")
async def serve_download(download_id: str, filename: str):
    """Serves the downloaded file"""
    file_path = os.path.join(TEMP_PATH, download_id, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    extension = filename.split(".")[-1].lower()
    media_type = "audio/mpeg" if extension == "mp3" else "video/mp4"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

# Function to clean up downloads after a certain time
async def clean_up_download(download_dir: str, delay_seconds: int):
    """Removes the downloaded files after a delay"""
    await asyncio.sleep(delay_seconds)
    shutil.rmtree(download_dir, ignore_errors=True)

# Don't forget to import these for the clean_up_download function
import asyncio
from fastapi.responses import FileResponse