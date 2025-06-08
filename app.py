from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import os
from fastapi.responses import FileResponse
from typing import Optional

app = FastAPI(title="YouTube Downloader API")

class DownloadRequest(BaseModel):
    url: str

# Shared yt-dlp options
BASE_YDL_OPTS = {
    'cookiefile': 'cookies.txt',
    'quiet': True,
    'no_warnings': True,
    'outtmpl': 'downloads/%(title)s.%(ext)s',
}

@app.post("/song")
async def download_song(request: DownloadRequest):
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            if os.path.exists(filename):
                return FileResponse(filename, media_type='audio/mpeg', filename=os.path.basename(filename))
            raise HTTPException(status_code=500, detail="File not found after download")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video")
async def download_video(request: DownloadRequest):
    ydl_opts = {
        **BASE_YDL_OPTS,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                return FileResponse(filename, media_type='video/mp4', filename=os.path.basename(filename))
            raise HTTPException(status_code=500, detail="File not found after download")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup downloaded files (optional, can be expanded)
@app.on_event("shutdown")
async def cleanup():
    for file in os.listdir('downloads'):
        os.remove(os.path.join('downloads', file))
