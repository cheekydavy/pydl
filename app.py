from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import yt_dlp
import os
from fastapi.responses import FileResponse
from typing import Optional
import logging
from contextlib import asynccontextmanager

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create downloads directory if it doesn't exist
if not os.path.exists("downloads"):
    os.makedirs("downloads")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up YouTube Downloader API...")
    yield
    # Cleanup downloaded files on shutdown
    logger.info("Shutting down, cleaning up downloads...")
    try:
        for file in os.listdir("downloads"):
            file_path = os.path.join("downloads", file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"Removed file: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")

app = FastAPI(title="YouTube Downloader API", lifespan=lifespan)

class DownloadRequest(BaseModel):
    url: str

# Shared yt-dlp options
BASE_YDL_OPTS = {
    'cookiefile': 'cookies.txt',
    'quiet': True,
    'no_warnings': True,
    'outtmpl': 'downloads/%(title)s.%(ext)s',
}

# POST endpoint for song (original, for programmatic use)
@app.post("/song")
async def download_song_post(request: DownloadRequest):
    ydl_opts = {
        **BASE_YDL_OPTS,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        logger.info(f"POST: Downloading song from URL: {request.url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            if os.path.exists(filename):
                logger.info(f"POST: Song downloaded successfully: {filename}")
                return FileResponse(filename, media_type='audio/mpeg', filename=os.path.basename(filename))
            logger.error(f"POST: File not found after download: {filename}")
            raise HTTPException(status_code=500, detail="File not found after download")
    except Exception as e:
        logger.error(f"POST: Error downloading song: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint for song (for direct link access)
@app.get("/song")
async def download_song_get(url: str = Query(..., description="YouTube URL to download as MP3")):
    ydl_opts = {
        **BASE_YDL_OPTS,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        logger.info(f"GET: Downloading song from URL: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
                if file_size > 50:  # Basic size limit for GET requests
                    logger.warning(f"GET: File too large for download: {file_size} MB")
                    raise HTTPException(status_code=413, detail="File too large for direct download (>50MB)")
                logger.info(f"GET: Song downloaded successfully: {filename}")
                return FileResponse(filename, media_type='audio/mpeg', filename=os.path.basename(filename))
            logger.error(f"GET: File not found after download: {filename}")
            raise HTTPException(status_code=500, detail="File not found after download")
    except Exception as e:
        logger.error(f"GET: Error downloading song: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# POST endpoint for video (original, for programmatic use)
@app.post("/video")
async def download_video_post(request: DownloadRequest):
    ydl_opts = {
        **BASE_YDL_OPTS,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
    }
    
    try:
        logger.info(f"POST: Downloading video from URL: {request.url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                logger.info(f"POST: Video downloaded successfully: {filename}")
                return FileResponse(filename, media_type='video/mp4', filename=os.path.basename(filename))
            logger.error(f"POST: File not found after download: {filename}")
            raise HTTPException(status_code=500, detail="File not found after download")
    except Exception as e:
        logger.error(f"POST: Error downloading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint for video (for direct link access)
@app.get("/video")
async def download_video_get(url: str = Query(..., description="YouTube URL to download as MP4")):
    ydl_opts = {
        **BASE_YDL_OPTS,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
    }
    
    try:
        logger.info(f"GET: Downloading video from URL: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
                if file_size > 50:  # Basic size limit for GET requests
                    logger.warning(f"GET: File too large for download: {file_size} MB")
                    raise HTTPException(status_code=413, detail="File too large for direct download (>50MB)")
                logger.info(f"GET: Video downloaded successfully: {filename}")
                return FileResponse(filename, media_type='video/mp4', filename=os.path.basename(filename))
            logger.error(f"GET: File not found after download: {filename}")
            raise HTTPException(status_code=500, detail="File not found after download")
    except Exception as e:
        logger.error(f"GET: Error downloading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
