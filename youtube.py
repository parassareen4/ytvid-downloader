from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import shutil
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "audio": "bestaudio/best"
}

@app.post("/prepare/")
async def prepare_download(request: DownloadRequest):
    """Prepares a video for download and returns a download URL"""
    if request.quality not in QUALITY_MAP:
        raise HTTPException(status_code=400, detail="Invalid quality option.")
    
    # Create a unique ID for this download
    download_id = str(uuid.uuid4())
    download_dir = os.path.join(TEMP_PATH, download_id)
    os.makedirs(download_dir, exist_ok=True)
    
    # Enhanced yt-dlp options to bypass restrictions
    ydl_opts = {
        'format': QUALITY_MAP[request.quality],
        'outtmpl': f"{download_dir}/%(title)s.%(ext)s",
        'merge_output_format': 'mp4' if request.quality != "audio" else 'mp3',
        'postprocessors': [],
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'quiet': False,
        'no_warnings': False,
        'verbose': True,
        'geo_bypass': True,
        'sleep_interval': 5,  # Avoid rate limiting
        'max_sleep_interval': 10,
        'extract_flat': False,
        'socket_timeout': 30,
        'retry_sleep_functions': {
            'http': lambda n: 5 * (2 ** n),  # Exponential backoff
        },
        'extractor_retries': 5,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'retry_sleep_interval': 5,
        'overwrites': True,
    }
    
    # Add user-agent to look more like a browser
    ydl_opts['http_headers'] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    if request.quality == "audio":
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        })
    
    try:
        logger.info(f"Starting download for URL: {request.url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First just extract info without downloading to check if video is available
            try:
                info_dict = ydl.extract_info(request.url, download=False)
                if not info_dict:
                    raise HTTPException(status_code=404, detail="Could not access video information. The video might be unavailable or restricted.")
                
                logger.info(f"Video info extracted successfully: {info_dict.get('title', 'Unknown')}")
                
                # Then download
                info = ydl.extract_info(request.url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Check for audio format and adjust extension
                if request.quality == "audio":
                    base_filename = os.path.basename(filename).rsplit(".", 1)[0] + ".mp3"
                    filename = os.path.join(download_dir, base_filename)
                else:
                    base_filename = os.path.basename(filename)
                
                # Verify file exists
                if not os.path.exists(filename):
                    logger.error(f"Downloaded file not found at: {filename}")
                    raise HTTPException(status_code=500, detail="File was processed but could not be found on server")
                
                logger.info(f"Download completed successfully: {filename}")
                
                # Create a download URL
                download_url = f"{PUBLIC_URL}/{download_id}/{base_filename}"
                
                # Schedule cleanup after some time (e.g., 1 hour)
                # background_tasks.add_task(clean_up_download, download_dir, 3600)
                
                return JSONResponse({
                    "status": "success",
                    "download_url": download_url,
                    "filename": base_filename,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "thumbnail": info.get('thumbnail', '')
                })
                
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"yt-dlp download error: {str(e)}")
                # More user-friendly error message
                error_message = str(e)
                if "HTTP Error 403: Forbidden" in error_message:
                    error_message = "Access to this video is restricted by YouTube. Try another video."
                elif "Video unavailable" in error_message:
                    error_message = "This video is unavailable. It may be private, deleted, or region-restricted."
                elif "Sign in" in error_message:
                    error_message = "This video requires sign-in to access. Try another video."
                else:
                    error_message = f"Download failed: {error_message}"
                    
                raise HTTPException(status_code=400, detail=error_message)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
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
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir, ignore_errors=True)
        logger.info(f"Cleaned up {download_dir}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}