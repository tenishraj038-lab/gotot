import logging
import os
import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db
from app.models.user import User, DownloadHistory
from app.models.monetization import SubscriptionTier
from app.services.downloader import extract_video_info, download_video, convert_to_mp3, extract_playlist
from app.services.cache import get_cached_video_info, set_cached_video_info
from app.utils.helpers import is_valid_url, detect_platform
from app.config import get_settings

router = APIRouter(prefix="/download", tags=["download"])
settings = get_settings()
logger = logging.getLogger("gotot.download")


class InfoRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not is_valid_url(v):
            raise ValueError("Invalid URL format")
        if not detect_platform(v):
            raise ValueError("Unsupported platform")
        return v.strip()


class DownloadRequest(BaseModel):
    url: str
    format_id: str
    as_mp3: bool = False
    mp3_bitrate: str = "192"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not is_valid_url(v):
            raise ValueError("Invalid URL format")
        if not detect_platform(v):
            raise ValueError("Unsupported platform")
        return v.strip()


class BatchDownloadRequest(BaseModel):
    urls: list[str]
    format_id: str
    as_mp3: bool = False

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v):
        if len(v) > 20:
            raise ValueError("Maximum 20 URLs per batch")
        for url in v:
            if not is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            if not detect_platform(url):
                raise ValueError(f"Unsupported platform: {url}")
        return v


class PlaylistRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not is_valid_url(v):
            raise ValueError("Invalid URL format")
        return v.strip()


async def get_user_from_request(request: Request, db: AsyncSession) -> Optional[User]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    from app.services.auth_service import decode_token
    payload = decode_token(token)
    if not payload:
        return None
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    return result.scalar_one_or_none()


@router.post("/info")
async def get_video_info(request: Request, data: InfoRequest, db: AsyncSession = Depends(get_db)):
    cached = await get_cached_video_info(data.url)
    if cached:
        return cached

    info = await extract_video_info(data.url)
    if not info:
        raise HTTPException(status_code=400, detail="Could not extract video info. Please check the URL and try again.")

    result = {
        "title": info.title,
        "platform": info.platform,
        "duration": info.duration,
        "thumbnail": info.thumbnail,
        "formats": info.formats,
        "is_playlist": info.is_playlist,
        "playlist_count": info.playlist_count,
        "requires_payment": False,
    }
    await set_cached_video_info(data.url, result)
    return result


@router.post("/start")
async def start_download(
    request: Request,
    data: DownloadRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_from_request(request, db)

    info = await extract_video_info(data.url)
    if not info:
        raise HTTPException(status_code=400, detail="Could not extract video info")

    if data.as_mp3:
        bitrate = data.mp3_bitrate if data.mp3_bitrate in ("128", "192", "256", "320") else "192"
        result = await download_video(data.url, data.format_id, settings.download_dir)
        if not result:
            raise HTTPException(status_code=500, detail="Download failed")
        mp3_result = await convert_to_mp3(result.file_path, bitrate=bitrate)
        if not mp3_result:
            raise HTTPException(status_code=500, detail="MP3 conversion failed")
        final_result = mp3_result
        fmt = "mp3"
    else:
        result = await download_video(data.url, data.format_id, settings.download_dir)
        if not result:
            raise HTTPException(status_code=500, detail="Download failed")
        final_result = result
        fmt = result.format

    download_record = DownloadHistory(
        user_id=user.id if user else None,
        url=data.url,
        title=info.title,
        thumbnail_url=info.thumbnail,
        platform=info.platform,
        format=fmt,
        status="completed",
        file_size=final_result.file_size,
        ip_address=request.client.host if request.client else None,
    )
    db.add(download_record)
    if user:
        user.total_downloads = (user.total_downloads or 0) + 1
    await db.commit()

    return {
        "file_name": final_result.file_name,
        "file_size": final_result.file_size,
        "format": fmt,
        "download_url": f"/download/file/{os.path.basename(final_result.file_path)}",
        "title": info.title,
        "thumbnail": info.thumbnail,
    }


@router.post("/batch")
async def batch_download(
    request: Request,
    data: BatchDownloadRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_from_request(request, db)

    batch_limit = 20
    urls_to_process = data.urls[:batch_limit]

    results = []
    for url in urls_to_process:
        try:
            info = await extract_video_info(url)
            if not info:
                results.append({"url": url, "status": "error", "detail": "Could not extract info"})
                continue
            result = await download_video(url, data.format_id, settings.download_dir)
            if result:
                record = DownloadHistory(
                    user_id=user.id if user else None,
                    url=url,
                    title=info.title,
                    thumbnail_url=info.thumbnail,
                    platform=info.platform,
                    format=result.format,
                    status="completed",
                    file_size=result.file_size,
                    ip_address=request.client.host if request.client else None,
                )
                db.add(record)
                results.append({
                    "url": url,
                    "status": "completed",
                    "file_name": result.file_name,
                    "file_size": result.file_size,
                    "download_url": f"/download/file/{os.path.basename(result.file_path)}",
                })
            else:
                results.append({"url": url, "status": "error", "detail": "Download failed"})
        except Exception as e:
            results.append({"url": url, "status": "error", "detail": str(e)})

    await db.commit()
    return {"results": results, "total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}


@router.post("/playlist")
async def get_playlist_info(data: PlaylistRequest):
    entries = await extract_playlist(data.url)
    if not entries:
        raise HTTPException(status_code=400, detail="Could not extract playlist or not a playlist URL")
    return {"entries": entries, "total": len(entries)}


@router.get("/file/{filename}")
async def serve_file(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(settings.download_dir, safe_name)

    if not os.path.exists(file_path):
        for root, dirs, files in os.walk(settings.download_dir):
            if safe_name in files:
                file_path = os.path.join(root, safe_name)
                break
        else:
            raise HTTPException(status_code=404, detail="File not found or expired")

    media_type = "application/octet-stream"
    if safe_name.endswith(".mp4"):
        media_type = "video/mp4"
    elif safe_name.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif safe_name.endswith(".webm"):
        media_type = "video/webm"
    elif safe_name.endswith(".3gp"):
        media_type = "video/3gpp"

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.get("/history")
async def get_history(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_from_request(request, db)
    if not user:
        return []

    result = await db.execute(
        select(DownloadHistory)
        .where(DownloadHistory.user_id == user.id)
        .order_by(DownloadHistory.created_at.desc())
        .offset(skip).limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "url": r.url,
            "title": r.title,
            "thumbnail_url": r.thumbnail_url,
            "platform": r.platform,
            "format": r.format,
            "status": r.status,
            "file_size": r.file_size,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/recent")
async def get_recent_downloads(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DownloadHistory)
        .where(DownloadHistory.status == "completed")
        .order_by(DownloadHistory.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "platform": r.platform,
            "format": r.format,
            "file_size": r.file_size,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.post("/subtitles")
async def get_subtitles(data: InfoRequest):
    from app.services.downloader import extract_subtitles
    subs = await extract_subtitles(data.url)
    if not subs:
        raise HTTPException(status_code=404, detail="No subtitles found")
    return {"subtitles": subs}


@router.post("/thumbnail")
async def get_thumbnail(data: InfoRequest):
    info = await extract_video_info(data.url)
    if not info or not info.thumbnail:
        raise HTTPException(status_code=404, detail="No thumbnail available")
    return {"thumbnail_url": info.thumbnail}


@router.get("/search")
async def search_downloads(
    q: str = Query(min_length=1, max_length=200),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    safe_q = re.sub(r'[\\%_]', '', q)
    result = await db.execute(
        select(DownloadHistory)
        .where(DownloadHistory.url.ilike(f"%{safe_q}%"))
        .order_by(DownloadHistory.created_at.desc())
        .offset(skip).limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "url": r.url,
            "title": r.title,
            "platform": r.platform,
            "format": r.format,
            "status": r.status,
            "file_size": r.file_size,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
