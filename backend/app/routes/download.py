"""
Download API Routes

Endpoints for video info extraction, download management, format selection,
playlist extraction, subtitle extraction, and download history.
"""
import logging
import os
import re
import time
from urllib.parse import quote
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db
from app.models.user import User, DownloadHistory
from app.services.downloader import (
    extract_video_info, download_video, convert_to_mp3,
    extract_playlist, download_and_merge_mp4, download_mp3,
    download_image, extract_subtitles, validate_media_file,
    repair_media_file, check_ffmpeg, get_ffmpeg_status,
    get_ffmpeg_install_instructions, cancel_download,
    register_progress_callback, unregister_progress_callback,
    cleanup_temp_files,
)
from app.services.cache import get_cached_video_info, set_cached_video_info
from app.services.audit_log import audit_logger
from app.utils.helpers import (
    is_valid_url, detect_platform, generate_secure_download_id,
    generate_task_id, sanitize_filename,
)
from app.config import get_settings

RECENT_DOWNLOADS: dict[str, dict] = {}
_MAX_RECENT_DOWNLOADS = 10000
_COOKIES_DIR: str = "/tmp/gotot_cookies"


def _trim_recent_downloads():
    if len(RECENT_DOWNLOADS) > _MAX_RECENT_DOWNLOADS:
        cutoff = time.time() - 3600
        keys_to_del = [k for k, v in RECENT_DOWNLOADS.items() if v.get("time", 0) < cutoff]
        for k in keys_to_del:
            del RECENT_DOWNLOADS[k]
        if len(RECENT_DOWNLOADS) > _MAX_RECENT_DOWNLOADS:
            sorted_items = sorted(RECENT_DOWNLOADS.items(), key=lambda x: x[1].get("time", 0))
            for k, _ in sorted_items[:len(sorted_items) // 5]:
                del RECENT_DOWNLOADS[k]


settings = get_settings()
logger = logging.getLogger("gotot.download")
router = APIRouter(prefix="/download", tags=["download"])

os.makedirs(_COOKIES_DIR, exist_ok=True)


# ─── Pydantic Models ──────────────────────────────────────────────────

class InfoRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError("URL is required")
        if not is_valid_url(v.strip()):
            raise ValueError("Invalid URL format. Must start with http:// or https://")
        if not detect_platform(v.strip()):
            raise ValueError(
                "Unsupported platform. We support: TikTok, Instagram, X/Twitter, "
                "Facebook, Reddit, Vimeo, Dailymotion, Twitch, LinkedIn, Pinterest, "
                "Snapchat, Bilibili, SoundCloud, Rumble, and Odysee."
            )
        return v.strip()


class DownloadRequest(BaseModel):
    url: str
    format_id: str
    as_mp3: bool = False
    mp3_bitrate: str = "192"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError("URL is required")
        if not is_valid_url(v.strip()):
            raise ValueError("Invalid URL format. Must start with http:// or https://")
        return v.strip()

    @field_validator("format_id")
    @classmethod
    def validate_format_id(cls, v):
        if not v or not v.strip():
            raise ValueError("format_id is required")
        if len(v) > 500:
            raise ValueError("format_id is too long")
        return v.strip()

    @field_validator("mp3_bitrate")
    @classmethod
    def validate_bitrate(cls, v):
        if v not in ("64", "96", "128", "192", "256", "320"):
            raise ValueError("Bitrate must be one of: 64, 96, 128, 192, 256, 320")
        return v


class BatchDownloadRequest(BaseModel):
    urls: list[str]
    format_id: str
    as_mp3: bool = False

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v):
        if not v:
            raise ValueError("At least one URL is required")
        if len(v) > 20:
            raise ValueError("Maximum 20 URLs per batch request")
        for i, url in enumerate(v):
            if not url or not url.strip():
                raise ValueError(f"URL at position {i + 1} is empty")
            if not is_valid_url(url.strip()):
                raise ValueError(f"Invalid URL at position {i + 1}: {url}")
            if not detect_platform(url.strip()):
                raise ValueError(f"Unsupported platform at position {i + 1}: {url}")
        return [u.strip() for u in v]


class PlaylistRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError("URL is required")
        if not is_valid_url(v.strip()):
            raise ValueError("Invalid URL format")
        return v.strip()


class QueueRequest(BaseModel):
    url: str
    format_id: str
    as_mp3: bool = False
    mp3_bitrate: str = "192"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError("URL is required")
        if not is_valid_url(v.strip()):
            raise ValueError("Invalid URL format")
        return v.strip()


class CancelRequest(BaseModel):
    task_id: str


# ─── Helpers ──────────────────────────────────────────────────────────

def _build_download_error(status_code: int, message: str, platform: str = None,
                          auth_required: bool = False, install_hint: str = None) -> dict:
    """Build a standardized error response with context."""
    error = {
        "error": message,
        "status_code": status_code,
        "retry_allowed": status_code in (502, 503, 504),
    }
    if platform:
        error["platform"] = platform
    if auth_required:
        error["auth_required"] = True
        error["auth_hint"] = "This content may require authentication. Use /download/cookies/import to add browser cookies."
    if install_hint:
        error["install_hint"] = install_hint
    return error


def _get_media_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".webm": "video/webm",
        ".3gp": "video/3gpp",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".mkv": "video/x-matroska",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".flv": "video/x-flv",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    return mime_map.get(ext, "application/octet-stream")


async def get_user_from_request(request: Request, db: AsyncSession) -> Optional[User]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    from app.services.auth_service import decode_token, parse_user_id
    payload = decode_token(token)
    if not payload:
        return None
    uid = parse_user_id(payload.get("sub"))
    if not uid:
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


def _resolve_cookies_file(request: Request) -> Optional[str]:
    """Resolve cookies file from request (uploaded or browser-imported)."""
    cookie_id = request.cookies.get("gotot_cookie_id") or request.headers.get("X-Cookie-ID")
    if cookie_id:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', cookie_id)[:64]
        candidate = os.path.join(_COOKIES_DIR, f"{safe_id}.txt")
        if os.path.isfile(candidate):
            return candidate
    return None


# ─── Routes ───────────────────────────────────────────────────────────

@router.get("/ffmpeg-status")
async def ffmpeg_status_endpoint():
    """Check if FFmpeg is installed and get platform-specific instructions."""
    return get_ffmpeg_status()


@router.post("/info")
async def get_video_info(request: Request, data: InfoRequest, db: AsyncSession = Depends(get_db)):
    """Extract video metadata including available formats, thumbnails, and subtitles."""
    cached = await get_cached_video_info(data.url)
    if cached:
        return cached

    cookies_file = _resolve_cookies_file(request)
    ydl_opts = {}
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    info = await extract_video_info(data.url, ydl_opts=ydl_opts if ydl_opts else None)
    if not info:
        platform = detect_platform(data.url)
        if not platform:
            raise HTTPException(
                status_code=400,
                detail="Unsupported URL. We support 15+ platforms including TikTok, Instagram, X, Facebook, Reddit, Vimeo, and more.",
            )

        provider = __import__("app.providers", fromlist=["provider_registry"]).provider_registry.get(platform)
        auth_required = provider.requires_auth() if provider else False

        raise HTTPException(
            status_code=422 if auth_required else 400,
            detail=_build_download_error(
                422 if auth_required else 400,
                f"Could not extract media from {platform.title()}. "
                "The content may be private, geo-restricted, deleted, or requires authentication.",
                platform=platform,
                auth_required=auth_required,
            ),
        )

    result = {
        "title": info.title,
        "platform": info.platform,
        "duration": info.duration,
        "thumbnail": info.thumbnail,
        "formats": info.formats,
        "is_playlist": info.is_playlist,
        "playlist_count": info.playlist_count,
        "requires_payment": False,
        "metadata": info.metadata,
        "description": info.description,
        "uploader": info.uploader,
        "upload_date": info.upload_date,
        "view_count": info.view_count,
        "like_count": info.like_count,
        "tags": info.tags,
        "subtitles": info.subtitles,
        "thumbnails": info.thumbnails,
        "chapters": info.chapters,
        "ffmpeg_available": check_ffmpeg(),
    }
    await set_cached_video_info(data.url, result)
    return result


@router.post("/start")
async def start_download(
    request: Request,
    data: DownloadRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a video/audio download with format selection and quality options."""
    logger.info("download_start", extra={
        "url": data.url, "format": data.format_id, "mp3": data.as_mp3, "bitrate": data.mp3_bitrate,
    })

    user = await get_user_from_request(request, db)

    # Rate limiting for authenticated users
    if user:
        now = datetime.utcnow()
        if user.last_download_reset.date() < now.date():
            user.downloads_today = 0
            user.last_download_reset = now
        if user.downloads_today >= user.daily_download_limit:
            raise HTTPException(
                status_code=429,
                detail=_build_download_error(
                    429,
                    f"Daily download limit reached ({user.daily_download_limit}). Upgrade your plan for more downloads.",
                ),
            )

    # Validate platform support
    platform = detect_platform(data.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Unsupported platform. Please check the URL.")

    # Check FFmpeg for MP3 conversion
    if data.as_mp3 and not check_ffmpeg():
        raise HTTPException(
            status_code=400,
            detail=_build_download_error(
                400,
                "MP3 conversion requires FFmpeg but it is not installed.",
                install_hint=get_ffmpeg_install_instructions().get("instructions", ""),
            ),
        )

    # Resolve cookies
    cookies_file = _resolve_cookies_file(request)

    # Validate requested format exists and build a fallback chain
    info = await extract_video_info(data.url)
    if info and info.formats:
        available_ids = {f.format_id for f in info.formats if hasattr(f, 'format_id')}
        available_ids.update({f.get("format_id") for f in info.formats if isinstance(f, dict)})
        req_fmt = data.format_id
        if req_fmt not in available_ids and "+" not in req_fmt:
            # Try matching by height first
            try:
                req_height = int(req_fmt) if req_fmt.isdigit() else None
            except Exception:
                req_height = None
            if req_height:
                # Fallback: find closest available height
                available_heights = sorted(set(
                    int(f.height) for f in info.formats if hasattr(f, 'height') and f.height
                ), reverse=True)
                for h in available_heights:
                    if h <= req_height:
                        for f in info.formats:
                            fh = f.height if hasattr(f, 'height') else f.get("height", 0)
                            if fh == h:
                                req_fmt = f.format_id if hasattr(f, 'format_id') else f.get("format_id", req_fmt)
                                logger.warning("format_fallback", extra={
                                    "requested": data.format_id, "fallback": req_fmt,
                                    "requested_height": req_height, "actual_height": h,
                                })
                                break
                        break
            data.format_id = req_fmt

    # Extract info if not already done (for the download itself)
    if not info:
        info = await extract_video_info(data.url)
    if not info:
        provider = __import__("app.providers", fromlist=["provider_registry"]).provider_registry.get(platform)
        auth_required = provider.requires_auth() if provider else False
        raise HTTPException(
            status_code=422 if auth_required else 400,
            detail=_build_download_error(
                422 if auth_required else 400,
                "Could not extract video info. The content may be private, deleted, or geo-restricted.",
                platform=platform,
                auth_required=auth_required,
            ),
        )

    download_id = generate_secure_download_id()
    task_id = generate_task_id()

    try:
        if data.as_mp3:
            result = await download_mp3(
                data.url, bitrate=data.mp3_bitrate,
                output_dir=settings.download_dir,
                task_id=task_id, cookies_file=cookies_file,
            )
            if not result:
                raise HTTPException(
                    status_code=500,
                    detail=_build_download_error(500, "MP3 download failed. The audio could not be extracted."),
                )
            final_result = result
            fmt = result.format
        else:
            result = await download_video(
                data.url, data.format_id, settings.download_dir,
                task_id=task_id, cookies_file=cookies_file,
            )
            if not result:
                raise HTTPException(
                    status_code=500,
                    detail=_build_download_error(
                        500, "Download failed. The media could not be downloaded. "
                        "The content may be private, deleted, or geo-restricted.",
                        platform=platform,
                    ),
                )

            # Validate downloaded file
            validation = validate_media_file(result.file_path)
            if validation.get("issues") and not validation.get("has_audio") and not validation.get("has_video"):
                repaired = repair_media_file(result.file_path, settings.download_dir)
                if repaired:
                    result.file_path = repaired
                    result.file_size = os.path.getsize(repaired)
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=_build_download_error(500, "Downloaded file is corrupt and could not be repaired."),
                    )

            final_result = result
            fmt = result.format

    except HTTPException:
        raise
    except Exception as e:
        logger.error("download_failed", extra={
            "url": data.url, "download_id": download_id, "task_id": task_id, "error": str(e),
        }, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=_build_download_error(500, f"An unexpected error occurred: {str(e)[:200]}"),
        )

    # Verify file exists and is readable
    if not os.path.exists(final_result.file_path):
        logger.error("download_file_missing", extra={"download_id": download_id, "path": final_result.file_path})
        raise HTTPException(status_code=500, detail="Downloaded file vanished. Please try again.")
    if not os.access(final_result.file_path, os.R_OK):
        logger.error("download_file_not_readable", extra={"download_id": download_id})
        raise HTTPException(status_code=500, detail="Downloaded file is not readable. Please try again.")

    ip_address = request.client.host if request.client else None
    file_name_with_ext = f"{final_result.file_name}.{final_result.format}"

    # Save download history
    try:
        download_record = DownloadHistory(
            user_id=user.id if user else None,
            url=data.url,
            title=final_result.title or info.title,
            thumbnail_url=final_result.thumbnail or info.thumbnail,
            platform=platform,
            format=fmt,
            status="completed",
            file_size=final_result.file_size,
            ip_address=ip_address,
        )
        db.add(download_record)
        if user:
            user.total_downloads = (user.total_downloads or 0) + 1
            user.downloads_today = (user.downloads_today or 0) + 1
            if user.download_credits > 0:
                user.download_credits -= 1
        await db.commit()
    except Exception as e:
        logger.warning("download_history_save_failed", extra={"url": data.url, "download_id": download_id, "error": str(e)})
        try:
            await db.rollback()
        except Exception:
            pass

    # Store for anonymous access
    if not user:
        download_key = f"{ip_address}:{os.path.basename(final_result.file_path)}"
        RECENT_DOWNLOADS[download_key] = {"time": time.time(), "download_id": download_id}
        _trim_recent_downloads()

    audit_logger.download(
        user_id=str(user.id) if user else None,
        url=data.url,
        platform=platform,
        ip_address=ip_address,
        status="success",
    )

    logger.info("download_completed", extra={
        "download_id": download_id,
        "url": data.url,
        "platform": platform,
        "format": fmt,
        "file_size": final_result.file_size,
        "resolution": final_result.resolution,
        "codec": final_result.codec,
        "duration_s": final_result.duration,
    })

    safe_name = os.path.basename(final_result.file_path)
    response_data = {
        "download_id": download_id,
        "task_id": task_id,
        "file_name": final_result.file_name,
        "file_size": final_result.file_size,
        "format": fmt,
        "download_url": f"/download/file/{quote(safe_name)}?id={download_id}",
        "title": final_result.title or info.title,
        "thumbnail": final_result.thumbnail or info.thumbnail,
        "duration": final_result.duration or info.duration,
        "resolution": final_result.resolution,
        "codec": final_result.codec,
        "bitrate": final_result.bitrate,
    }

    if not user:
        response_data["expires_in"] = 3600

    return response_data


@router.post("/cancel")
async def cancel_download_endpoint(data: CancelRequest):
    """Cancel an in-progress download."""
    cancelled = cancel_download(data.task_id)
    if cancelled:
        return {"status": "cancelled", "task_id": data.task_id}
    raise HTTPException(status_code=404, detail="Download task not found or already completed")


@router.post("/batch")
async def batch_download(
    request: Request,
    data: BatchDownloadRequest,
    db: AsyncSession = Depends(get_db),
):
    """Download multiple videos in a single batch."""
    user = await get_user_from_request(request, db)
    cookies_file = _resolve_cookies_file(request)
    batch_limit = 20
    urls_to_process = data.urls[:batch_limit]
    results = []

    for url in urls_to_process:
        try:
            info = await extract_video_info(url)
            if not info:
                results.append({"url": url, "status": "error", "detail": "Could not extract info"})
                continue

            result = await download_video(
                url, data.format_id, settings.download_dir,
                cookies_file=cookies_file,
            )
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
                    "format": result.format,
                    "download_url": f"/download/file/{quote(os.path.basename(result.file_path))}",
                })
            else:
                results.append({"url": url, "status": "error", "detail": "Download failed"})
        except HTTPException as e:
            results.append({"url": url, "status": "error", "detail": e.detail})
        except Exception as e:
            logger.error("batch_item_error", extra={"url": url, "error": str(e)})
            results.append({"url": url, "status": "error", "detail": str(e)[:200]})

    try:
        await db.commit()
    except Exception as e:
        logger.warning("batch_history_save_failed", extra={"error": str(e)})
        try:
            await db.rollback()
        except Exception:
            pass

    return {
        "results": results,
        "total": len(results),
        "successful": sum(1 for r in results if r["status"] == "completed"),
    }


@router.post("/playlist")
async def get_playlist_info(data: PlaylistRequest):
    """Extract playlist entries."""
    entries = await extract_playlist(data.url)
    if not entries:
        raise HTTPException(status_code=400, detail="Could not extract playlist or URL is not a playlist")
    return {"entries": entries, "total": len(entries)}


@router.get("/file/{filename}")
async def serve_file(
    filename: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Serve a downloaded file with proper MIME types and security checks."""
    user = await get_user_from_request(request, db)
    ip_address = request.client.host if request.client else "unknown"

    safe_name = os.path.basename(filename)
    resolved_path = os.path.realpath(os.path.join(settings.download_dir, safe_name))

    if not resolved_path.startswith(os.path.realpath(settings.download_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(resolved_path):
        raise HTTPException(status_code=404, detail="File not found or expired")

    # Check anonymous access
    if not user:
        download_key = f"{ip_address}:{safe_name}"
        if download_key not in RECENT_DOWNLOADS:
            raise HTTPException(status_code=401, detail="Authentication required to download this file")
        stored = RECENT_DOWNLOADS.get(download_key, {})
        if time.time() - stored.get("time", 0) > 3600:
            del RECENT_DOWNLOADS[download_key]
            raise HTTPException(status_code=401, detail="Download link expired")

    media_type = _get_media_type(safe_name)

    return FileResponse(
        path=resolved_path,
        filename=safe_name,
        media_type=media_type,
    )


@router.get("/history")
async def get_history(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get download history for authenticated user."""
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
    """Get recent completed downloads (public feed)."""
    result = await db.execute(
        select(DownloadHistory)
        .where(DownloadHistory.status == "completed")
        .order_by(DownloadHistory.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "platform": r.platform,
            "format": r.format,
            "file_size": r.file_size,
            "title": r.title,
            "thumbnail_url": r.thumbnail_url,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.post("/subtitles")
async def get_subtitles(data: InfoRequest):
    """Extract available subtitles for a video."""
    subs = await extract_subtitles(data.url)
    if not subs:
        raise HTTPException(status_code=404, detail="No subtitles found for this content")
    return {"subtitles": subs, "count": len(subs)}


@router.post("/thumbnail")
async def get_thumbnail(data: InfoRequest):
    """Get thumbnail URL for a video."""
    info = await extract_video_info(data.url)
    if not info or not info.thumbnail:
        raise HTTPException(status_code=404, detail="No thumbnail available")
    return {"thumbnail_url": info.thumbnail, "thumbnails": info.thumbnails}


@router.get("/search")
async def search_downloads(
    q: str = Query(min_length=1, max_length=200),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """Search through user's download history."""
    user = await get_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    safe_q = re.sub(r'[\\%_"]', '', q)[:200]
    result = await db.execute(
        select(DownloadHistory)
        .where(
            DownloadHistory.user_id == user.id,
            DownloadHistory.title.ilike(f"%{safe_q}%") | DownloadHistory.url.ilike(f"%{safe_q}%"),
        )
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


# ─── Cookie/Auth Management ──────────────────────────────────────────

@router.post("/cookies/import")
async def import_cookies(
    request: Request,
    browser: str = Form(default="chrome"),
    domain: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    """
    Import cookies from browser for authentication on platforms that require login.
    Supported browsers: chrome, firefox, edge, opera, brave, safari.
    """
    import uuid
    from yt_dlp.cookies import SUPPORTED_BROWSERS

    user = await get_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    browser = browser.lower().strip()
    allowed_browsers = list(SUPPORTED_BROWSERS)
    if browser not in allowed_browsers:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported browser: {browser}. Supported: {', '.join(allowed_browsers)}",
        )

    cookie_id = str(uuid.uuid4())[:12]
    output_path = os.path.join(_COOKIES_DIR, f"{cookie_id}.txt")

    try:
        import yt_dlp
        yt_dlp.cookies.extract_cookies_from_browser(browser, output_path)
        if os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
            return {
                "status": "success",
                "cookie_id": cookie_id,
                "browser": browser,
                "message": f"Cookies imported from {browser}. Use cookie_id for downloads.",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to extract cookies. Browser may be locked or empty.")
    except Exception as e:
        logger.error("cookie_import_failed", extra={"browser": browser, "error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import cookies from {browser}: {str(e)}",
        )


@router.post("/cookies/upload")
async def upload_cookies_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a cookies.txt file (Netscape format) for authentication."""
    import uuid

    user = await get_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Please upload a .txt file in Netscape cookies format")

    content = await file.read()
    if len(content) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="Cookies file too large (max 1MB)")

    cookie_id = str(uuid.uuid4())[:12]
    output_path = os.path.join(_COOKIES_DIR, f"{cookie_id}.txt")

    with open(output_path, "wb") as f:
        f.write(content)

    line_count = len(content.splitlines())
    return {
        "status": "success",
        "cookie_id": cookie_id,
        "lines": line_count,
        "message": f"Cookies uploaded ({line_count} lines). Use cookie_id for downloads.",
    }


@router.get("/cookies/status")
async def cookie_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if cookies are available for the current session."""
    user = await get_user_from_request(request, db)
    cookies_file = _resolve_cookies_file(request)
    return {
        "authenticated": user is not None,
        "cookies_active": cookies_file is not None,
        "cookie_id": request.cookies.get("gotot_cookie_id"),
        "supported_browsers": ["chrome", "firefox", "edge", "opera", "brave", "safari"],
    }


@router.post("/queue")
async def queue_download(
    request: Request,
    data: QueueRequest,
    db: AsyncSession = Depends(get_db),
):
    """Queue a download for async processing with WebSocket progress updates."""
    from celery_app.tasks import process_download
    user = await get_user_from_request(request, db)
    task_id = generate_task_id()

    process_download.delay(data.url, data.format_id, task_id, settings.download_dir)

    download_record = DownloadHistory(
        user_id=user.id if user else None,
        url=data.url,
        platform=detect_platform(data.url) or "unknown",
        format="queued",
        status="queued",
        ip_address=request.client.host if request.client else None,
    )
    db.add(download_record)
    await db.commit()

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Download queued successfully",
        "ws_url": f"/ws/progress/{task_id}",
    }


@router.get("/queue/{task_id}")
async def get_queue_status_endpoint(task_id: str):
    """Get status of a queued download task."""
    from celery_app.tasks import get_queue_status
    status = get_queue_status(task_id)
    if not status:
        return {"task_id": task_id, "status": "pending", "progress": 0, "message": "Task not started yet"}
    return status


@router.get("/platforms")
async def list_platforms():
    """List all supported platforms and their capabilities."""
    from app.providers import provider_registry
    platforms = []
    for name, provider in provider_registry.get_all().items():
        platforms.append({
            "name": name,
            "display_name": provider.display_name,
            "color": provider.color,
            "supports_playlist": provider.supports_playlist(),
            "supports_subtitles": provider.supports_subtitles(),
            "supports_audio": provider.supports_audio_extraction(),
            "supports_images": provider.supports_images(),
            "requires_auth": provider.requires_auth(),
            "auth_hint": provider.get_auth_hint(),
        })
    return {"platforms": platforms, "total": len(platforms)}


@router.post("/validate")
async def validate_download(data: InfoRequest):
    """Validate a URL and return platform info without extracting formats."""
    platform = detect_platform(data.url)
    if not platform:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    from app.providers import provider_registry
    provider = provider_registry.get(platform)
    return {
        "valid": True,
        "platform": platform,
        "display_name": provider.display_name if provider else platform,
        "requires_auth": provider.requires_auth() if provider else False,
        "auth_hint": provider.get_auth_hint() if provider else None,
        "ffmpeg_available": check_ffmpeg(),
    }
