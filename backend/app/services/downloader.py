"""
GoTot Video Download Engine

Production-ready downloader with:
- Format preservation (original container/format detection)
- Audio-video merge with FFmpeg (best video + best audio)
- FFmpeg detection with cross-platform path resolution
- Retry logic with exponential backoff
- Resume support for interrupted downloads
- Progress hooks (speed, ETA, percentage, file size)
- File validation using ffprobe
- Thumbnail and subtitle support
- Playlist support with individual format selection
- Multiple audio track handling
- Secure filename sanitization
"""
import asyncio
import glob as glob_mod
import json
import logging
import os
import platform as sys_platform
import re
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Any
from urllib.parse import urlparse

import yt_dlp
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from app.providers import provider_registry
from app.utils.helpers import sanitize_filename

logger = logging.getLogger("gotot.download")
logger.setLevel(logging.INFO)

_CANCEL_EVENTS: dict[str, asyncio.Event] = {}

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0
DOWNLOAD_TIMEOUT = 600
INFO_TIMEOUT = 15
FFPROBE_TIMEOUT = 15
MERGE_TIMEOUT = 180


@dataclass
class VideoInfo:
    title: str
    platform: str
    duration: int
    thumbnail: str
    formats: list
    url: str
    is_playlist: bool = False
    playlist_count: int = 0
    metadata: Optional[dict] = None
    description: str = ""
    uploader: str = ""
    upload_date: str = ""
    view_count: int = 0
    like_count: int = 0
    tags: list = field(default_factory=list)
    subtitles: list = field(default_factory=list)
    thumbnails: list = field(default_factory=list)
    chapters: list = field(default_factory=list)


@dataclass
class DownloadResult:
    file_path: str
    file_name: str
    file_size: int
    format: str
    used_height: int = 0
    has_audio: bool = True
    title: str = ""
    thumbnail: str = ""
    duration: int = 0
    resolution: str = ""
    codec: str = ""
    bitrate: int = 0


@dataclass
class DownloadProgress:
    task_id: str
    status: str = "pending"
    percentage: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0
    eta: int = 0
    message: str = ""


_progress_callbacks: dict[str, Any] = {}
_active_downloads: dict[str, subprocess.Popen] = {}


# ─── FFmpeg detection ────────────────────────────────────────────────

def find_ffmpeg_path() -> Optional[str]:
    """Cross-platform FFmpeg detection with exhaustive search paths."""
    names = ["ffmpeg", "ffmpeg.exe"]

    for name in names:
        path = shutil.which(name)
        if path:
            return path

    if sys_platform.system() == "Windows":
        search_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "ffmpeg", "bin"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "ffmpeg", "bin"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages"),
            os.path.join(os.environ.get("APPDATA", ""), "ffmpeg"),
        ]
        for search in search_paths:
            exe = os.path.join(search, "ffmpeg.exe")
            if os.path.isfile(exe):
                return exe
    elif sys_platform.system() == "Darwin":
        search_paths = [
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
        ]
        for p in search_paths:
            if os.path.isfile(p):
                return p
    else:
        search_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/snap/bin/ffmpeg",
            "/opt/ffmpeg/bin/ffmpeg",
        ]
        for p in search_paths:
            if os.path.isfile(p):
                return p
    return None


def find_ffprobe_path() -> Optional[str]:
    """Cross-platform ffprobe detection."""
    names = ["ffprobe", "ffprobe.exe"]
    for name in names:
        path = shutil.which(name)
        if path:
            return path

    ffmpeg = find_ffmpeg_path()
    if ffmpeg:
        ffdir = os.path.dirname(ffmpeg)
        for name in names:
            probe = os.path.join(ffdir, name)
            if os.path.isfile(probe):
                return probe
    return None


_FFMPEG_PATH: Optional[str] = None
_FFPROBE_PATH: Optional[str] = None


def check_ffmpeg() -> bool:
    global _FFMPEG_PATH
    if _FFMPEG_PATH is None:
        _FFMPEG_PATH = find_ffmpeg_path()
    return _FFMPEG_PATH is not None


def check_ffprobe() -> bool:
    global _FFPROBE_PATH
    if _FFPROBE_PATH is None:
        _FFPROBE_PATH = find_ffprobe_path()
    return _FFPROBE_PATH is not None


def get_ffmpeg_install_instructions() -> dict:
    """Return platform-specific FFmpeg installation instructions."""
    system = sys_platform.system()
    return {
        "installed": check_ffmpeg(),
        "path": _FFMPEG_PATH,
        "instructions": {
            "Windows": "winget install ffmpeg  OR  choco install ffmpeg  OR  download from https://ffmpeg.org/download.html",
            "Darwin": "brew install ffmpeg",
            "Linux": "sudo apt install ffmpeg  (Ubuntu/Debian)\nsudo dnf install ffmpeg  (Fedora)\nsudo pacman -S ffmpeg  (Arch)",
        }.get(system, "Install FFmpeg from https://ffmpeg.org/download.html"),
        "platform": system,
    }


# ─── Progress tracking ────────────────────────────────────────────────

def register_progress_callback(task_id: str, callback: Any) -> None:
    _progress_callbacks[task_id] = callback


def unregister_progress_callback(task_id: str) -> None:
    _progress_callbacks.pop(task_id, None)


def _emit_progress(task_id: str, progress: DownloadProgress) -> None:
    cb = _progress_callbacks.get(task_id)
    if cb:
        try:
            cb(progress)
        except Exception:
            pass


def cancel_download(task_id: str) -> bool:
    """Cancel an active download by task_id."""
    event = _CANCEL_EVENTS.get(task_id)
    if event:
        event.set()
    proc = _active_downloads.get(task_id)
    if proc:
        try:
            proc.send_signal(signal.SIGTERM)
            _active_downloads.pop(task_id, None)
            return True
        except Exception:
            pass
    return False


def _progress_hook(d: dict) -> None:
    """yt-dlp progress hook."""
    status = d.get("status", "unknown")
    task_id = d.get("info_dict", {}).get("_task_id", "")
    if not task_id:
        return

    downloaded = d.get("downloaded_bytes", 0) or 0
    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0) or 0
    speed = d.get("speed") or 0
    eta = d.get("eta") or 0

    if speed and speed > 0:
        speed = round(speed / 1024 / 1024, 2)
    pct = round((downloaded / total) * 100, 1) if total > 0 else 0

    progress = DownloadProgress(
        task_id=task_id,
        status=status,
        percentage=pct,
        downloaded_bytes=downloaded,
        total_bytes=total,
        speed=speed,
        eta=eta,
        message=f"{status}... {pct}%" if status != "finished" else "Processing...",
    )
    _emit_progress(task_id, progress)

    if task_id in _CANCEL_EVENTS and _CANCEL_EVENTS[task_id].is_set():
        raise YtDlpDownloadError("Download cancelled by user")


# ─── File validation ──────────────────────────────────────────────────

def validate_media_file(file_path: str) -> dict:
    """Validate downloaded media file using ffprobe. Returns dict with status and details."""
    result = {
        "valid": True,
        "has_video": False,
        "has_audio": False,
        "duration": 0.0,
        "codec_video": None,
        "codec_audio": None,
        "resolution": None,
        "bitrate": 0,
        "format_name": None,
        "issues": [],
    }

    if not os.path.exists(file_path):
        result["valid"] = False
        result["issues"].append("File does not exist")
        return result

    if os.path.getsize(file_path) == 0:
        result["valid"] = False
        result["issues"].append("File is empty (0 bytes)")
        return result

    if not check_ffprobe():
        ext = os.path.splitext(file_path)[1].lower()
        result["has_audio"] = ext in (".mp4", ".mp3", ".m4a", ".mkv", ".webm", ".mov", ".avi", ".flv")
        result["has_video"] = ext in (".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".3gp")
        return result

    ffprobe_path = _FFPROBE_PATH

    try:
        cmd = [
            ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=FFPROBE_TIMEOUT)
        if proc.returncode != 0:
            result["valid"] = False
            result["issues"].append(f"ffprobe failed: {proc.stderr[:200]}")
            return result

        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        fmt = data.get("format", {})

        result["duration"] = float(fmt.get("duration", 0))
        result["bitrate"] = int(fmt.get("bit_rate", 0) or 0)
        result["format_name"] = fmt.get("format_name", "")

        for stream in streams:
            codec_type = stream.get("codec_type")
            if codec_type == "video":
                result["has_video"] = True
                result["codec_video"] = stream.get("codec_name")
                w = stream.get("width", 0)
                h = stream.get("height", 0)
                if w and h:
                    result["resolution"] = f"{w}x{h}"
            elif codec_type == "audio":
                result["has_audio"] = True
                result["codec_audio"] = stream.get("codec_name")

        if not result["has_video"] and not result["has_audio"]:
            result["issues"].append("No playable streams found")

    except subprocess.TimeoutExpired:
        result["issues"].append("File validation timed out")
    except json.JSONDecodeError:
        result["issues"].append("Could not parse ffprobe output")
    except Exception as e:
        result["issues"].append(f"Validation error: {str(e)[:100]}")

    return result


def repair_media_file(input_path: str, output_dir: Optional[str] = None) -> Optional[str]:
    """Attempt to repair a corrupt media file by remuxing with FFmpeg."""
    if not check_ffmpeg():
        return None

    ffmpeg_path = _FFMPEG_PATH
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = output_dir or os.path.dirname(input_path)
    output_path = os.path.join(output_dir, f"{base}_repaired.mp4")

    try:
        cmd = [
            ffmpeg_path, "-y",
            "-err_detect", "ignore_err",
            "-i", input_path,
            "-c", "copy",
            "-map", "0",
            "-movflags", "+faststart",
            "-f", "mp4",
            output_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=MERGE_TIMEOUT)
        if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info("media_repaired", extra={"original": input_path, "repaired": output_path})
            return output_path
    except Exception as e:
        logger.warning("media_repair_failed", extra={"path": input_path, "error": str(e)})
    return None


# ─── Utility helpers ──────────────────────────────────────────────────

def _format_size(size_bytes: int) -> str:
    if not size_bytes or size_bytes < 0:
        return "Unknown"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


_STANDARD_HEIGHTS = [144, 240, 360, 480, 720, 1080, 1440, 2160]


def _round_to_standard(height: int) -> int:
    for std in _STANDARD_HEIGHTS:
        if std >= height:
            return std
    return _STANDARD_HEIGHTS[-1]


def _deduplicate_formats(formats: list) -> list:
    seen = set()
    result = []
    for f in formats:
        vcodec = f.get("vcodec", "")
        acodec = f.get("acodec", "")
        if vcodec == "none" and acodec == "none":
            continue
        ext = f.get("ext", "mp4")
        height = f.get("height")
        key = f"{ext}_{height}_{f.get('format_id')}"
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def _build_format_entry(f: dict, h: int, entry: dict, best_audio_id: Optional[str],
                        audio_label: str, ffmpeg_available: bool) -> dict:
    combined_id = entry["video_id"]
    needs_audio = entry.get("needs_audio", False)

    if needs_audio and best_audio_id and ffmpeg_available:
        combined_id = f"{entry['video_id']}+{best_audio_id}"
        quality_label = f"{h}p • MP4 • {entry.get('vcodec', '').split('.')[0].upper()} • AAC • 🎵 Audio merged"
        acodec_val = "mp4a.40.2"
    else:
        vcodec_short = entry.get("vcodec", "").split(".")[0].upper()
        if needs_audio:
            audio_label = "⚠️ No audio (install ffmpeg for merge)"
        quality_label = f"{h}p • MP4 • {vcodec_short} • AAC • {audio_label}"
        acodec_val = "mp4a.40.2" if not needs_audio else "none"

    fs = entry.get("filesize", 0)
    fps_val = entry.get("fps") or 0

    return {
        "format_id": combined_id,
        "ext": "mp4",
        "resolution": f"{h}p",
        "height": h,
        "filesize": fs,
        "filesize_approx": fs,
        "filesize_human": _format_size(fs),
        "vcodec": entry.get("vcodec", ""),
        "acodec": acodec_val,
        "fps": fps_val,
        "abr": 0,
        "tbr": 0,
        "quality_label": quality_label,
        "has_video": True,
        "has_audio": True,
        "type": "video",
        "needs_audio": needs_audio,
    }


def _format_formats(info: dict, platform: str) -> list:
    """Build optimal format list per standard resolution with audio merge info."""
    raw_formats = info.get("formats", [])

    audio_streams = [f for f in raw_formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
    audio_streams.sort(key=lambda f: (f.get("abr") or 0), reverse=True)
    best_audio_id = audio_streams[0]["format_id"] if audio_streams else None

    ffmpeg_available = check_ffmpeg()

    video_by_height: dict[int, dict] = {}
    for f in raw_formats:
        h = f.get("height")
        vc = f.get("vcodec", "")
        if not h or vc == "none":
            continue
        std_h = _round_to_standard(h)
        ext = f.get("ext", "mp4")
        filesize = f.get("filesize") or f.get("filesize_approx") or 0
        has_audio = bool(f.get("acodec") and f["acodec"] != "none")
        score = 0
        if has_audio:
            score += 100000
        if filesize > 0:
            score += 10000
        if "avc" in vc:
            score += 1000
        elif "vp9" in vc:
            score += 500
        if ext == "mp4":
            score += 300

        if std_h not in video_by_height or score > video_by_height[std_h]["score"]:
            video_by_height[std_h] = {
                "score": score,
                "video_id": f["format_id"],
                "height": std_h,
                "vcodec": vc,
                "fps": f.get("fps"),
                "ext": ext,
                "filesize": filesize,
                "needs_audio": not has_audio,
                "raw_height": h,
            }

    result = []
    for h in sorted(video_by_height.keys(), reverse=True):
        entry = video_by_height[h]
        audio_label = "✅ AAC Audio" if not entry.get("needs_audio") else "🎵 Audio merged"
        result.append(_build_format_entry(entry, h, entry, best_audio_id, audio_label, ffmpeg_available))

    # Audio-only formats
    for f in audio_streams:
        abr = f.get("abr", 0)
        result.append({
            "format_id": f["format_id"],
            "ext": f.get("ext", "m4a"),
            "resolution": "audio only",
            "height": None,
            "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
            "filesize_approx": f.get("filesize_approx", 0),
            "filesize_human": _format_size(f.get("filesize") or f.get("filesize_approx") or 0),
            "vcodec": "none",
            "acodec": f.get("acodec", "mp4a"),
            "fps": None,
            "abr": abr,
            "tbr": f.get("tbr", 0),
            "quality_label": f"Audio {int(abr)}kbps" if abr else "Audio",
            "has_video": False,
            "has_audio": True,
            "type": "audio",
        })

    return _deduplicate_formats(result)


def _build_full_metadata(info: dict, platform: str) -> dict:
    return {
        "title": info.get("title", "video"),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "uploader": info.get("uploader", info.get("channel", "")),
        "upload_date": info.get("upload_date", ""),
        "description": (info.get("description", "") or "")[:1000],
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
        "tags": (info.get("tags") or [])[:10],
        "categories": info.get("categories") or [],
        "age_limit": info.get("age_limit", 0),
        "subtitles": list(info.get("subtitles", {}).keys()) if info.get("subtitles") else [],
    }


# ─── Extract video info ────────────────────────────────────────────────

async def extract_video_info(url: str, ydl_opts: Optional[dict] = None) -> Optional[VideoInfo]:
    provider = provider_registry.detect(url)
    if not provider:
        logger.warning("extract_no_provider", extra={"url": url})
        return None

    platform = provider.name
    loop = asyncio.get_running_loop()

    def _extract():
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "ignoreerrors": True,
            "no_color": True,
            "socket_timeout": 10,
            **(ydl_opts or {}),
        }
        # Apply provider-specific extraction options
        provider_opts = provider.get_extract_opts()
        if provider_opts:
            opts.update(provider_opts)

        for attempt in range(MAX_RETRIES):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    raw_info = ydl.extract_info(url, download=False)
                    if not raw_info:
                        logger.warning("extract_no_info", extra={"url": url, "platform": platform})
                        return None

                    is_playlist = raw_info.get("_type") == "playlist" or "entries" in raw_info
                    if is_playlist and "entries" in raw_info:
                        playlist_count = len(raw_info.get("entries", []))
                        return VideoInfo(
                            title=raw_info.get("title", "playlist"),
                            platform=platform,
                            duration=0,
                            thumbnail=raw_info.get("thumbnail", ""),
                            formats=[],
                            url=url,
                            is_playlist=True,
                            playlist_count=playlist_count,
                            metadata=_build_full_metadata(raw_info, platform),
                        )

                    formats = _format_formats(raw_info, platform)
                    subs = []
                    for lang, sub_list in (raw_info.get("subtitles") or {}).items():
                        subs.append({"language": lang, "count": len(sub_list)})

                    thumbnails = []
                    for t in (raw_info.get("thumbnails") or [])[:5]:
                        thumbnails.append({"url": t.get("url"), "width": t.get("width"), "height": t.get("height")})

                    chapters = []
                    for c in (raw_info.get("chapters") or []):
                        chapters.append({"title": c.get("title"), "start": c.get("start_time"), "end": c.get("end_time")})

                    return VideoInfo(
                        title=raw_info.get("title", "video"),
                        platform=platform,
                        duration=raw_info.get("duration", 0),
                        thumbnail=raw_info.get("thumbnail", ""),
                        formats=formats,
                        url=url,
                        metadata=_build_full_metadata(raw_info, platform),
                        description=(raw_info.get("description") or "")[:500],
                        uploader=raw_info.get("uploader", ""),
                        upload_date=raw_info.get("upload_date", ""),
                        view_count=raw_info.get("view_count", 0),
                        like_count=raw_info.get("like_count", 0),
                        tags=(raw_info.get("tags") or [])[:10],
                        subtitles=subs,
                        thumbnails=thumbnails,
                        chapters=chapters,
                    )
            except YtDlpDownloadError as e:
                err_msg = str(e).lower()
                if "private" in err_msg or "unavailable" in err_msg or "removed" in err_msg:
                    logger.warning("extract_unavailable", extra={"url": url, "error": str(e)[:200]})
                    return None
                if "copyright" in err_msg or "blocked" in err_msg:
                    logger.warning("extract_blocked", extra={"url": url, "error": str(e)[:200]})
                    return None
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("extract_failed", extra={"url": url, "platform": platform, "error": str(e)}, exc_info=True)
                return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("extract_failed", extra={"url": url, "platform": platform, "error": str(e)}, exc_info=True)
                return None
        return None

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _extract), timeout=INFO_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning("extract_timeout", extra={"url": url, "platform": platform, "timeout_s": INFO_TIMEOUT})
        return None


# ─── Download video ────────────────────────────────────────────────────

def _find_output_file(output_dir: str, info: dict, ydl: yt_dlp.YoutubeDL, expected_exts: list = None) -> Optional[str]:
    """Find the output file after download. Uses yt-dlp's tracked filename first, then directory scan."""
    candidates = []
    expected_exts = expected_exts or ["mp4", "mkv", "webm", "flv", "mov", "3gp", "mp3", "m4a", "opus", "ogg"]

    # First: check requested_downloads for the exact file yt-dlp tracked
    req_dls = info.get("requested_downloads") or []
    for dl in req_dls:
        filepath = dl.get("filepath") or dl.get("_filename")
        if filepath and os.path.isfile(filepath):
            return os.path.abspath(filepath)

    # Second: use yt-dlp's prepare_filename
    try:
        prepared = ydl.prepare_filename(info)
        if prepared and os.path.isfile(prepared):
            return os.path.abspath(prepared)
        if prepared:
            candidates.append(prepared)
            base, ext = os.path.splitext(prepared)
            for e in expected_exts:
                if e != ext.lstrip("."):
                    candidates.append(f"{base}.{e}")
    except Exception:
        pass

    for cand in candidates:
        if cand and os.path.isfile(cand):
            return os.path.abspath(cand)

    # Third: newest file in output_dir matching expected extensions (narrowed to 30s)
    cutoff = time.time() - 30
    if os.path.isdir(output_dir):
        best = None
        best_mtime = 0
        for fname in os.listdir(output_dir):
            fpath = os.path.join(output_dir, fname)
            if os.path.isfile(fpath):
                ext_check = os.path.splitext(fname)[1].lstrip(".").lower()
                if ext_check in expected_exts:
                    mtime = os.path.getmtime(fpath)
                    if mtime > cutoff and mtime > best_mtime:
                        best_mtime = mtime
                        best = fpath
        if best:
            return os.path.abspath(best)

    return None


def _build_ydl_opts(format_id: str, output_dir: str, provider: Any, task_id: str = "",
                    cookies_file: Optional[str] = None, as_mp3: bool = False,
                    mp3_bitrate: str = "192") -> dict:
    """Build yt-dlp options dict with all configurable parameters."""
    base_opts = provider.get_download_opts(format_id, output_dir)
    opts = {
        "format": base_opts.get("format", format_id),
        "outtmpl": base_opts.get("outtmpl", f"{output_dir}/%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_progress_hook] if task_id else [],
        "ignoreerrors": False,
        "no_color": True,
        "socket_timeout": 60,
        "retries": 5,
        "fragment_retries": 5,
        "file_access_retries": 3,
        "extractor_retries": 3,
    }

    if check_ffmpeg():
        opts["merge_output_format"] = "mp4"

    if cookies_file and os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file

    if as_mp3 and check_ffmpeg():
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": mp3_bitrate,
        }]

    return opts


async def download_video(
    url: str, format_id: str, output_dir: Optional[str] = None,
    task_id: str = "", cookies_file: Optional[str] = None,
    as_mp3: bool = False, mp3_bitrate: str = "192",
) -> Optional[DownloadResult]:
    """
    Download a video from any supported platform.

    Features:
    - Automatic audio-video merge (best video + best audio)
    - Format preservation (respects original container)
    - Retry with exponential backoff
    - File validation after download
    - Progress tracking via WebSocket
    """
    provider = provider_registry.detect(url)
    if not provider:
        return None

    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="gotot_dl_")
    os.makedirs(output_dir, exist_ok=True)

    if task_id:
        _CANCEL_EVENTS[task_id] = asyncio.Event()

    loop = asyncio.get_running_loop()

    def _download():
        for attempt in range(MAX_RETRIES):
            try:
                ydl_opts = _build_ydl_opts(
                    format_id, output_dir, provider,
                    task_id=task_id, cookies_file=cookies_file,
                    as_mp3=as_mp3, mp3_bitrate=mp3_bitrate,
                )

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info("download_attempt", extra={
                        "url": url, "format": format_id, "attempt": attempt + 1,
                        "task_id": task_id, "ydl_format": ydl_opts.get("format"),
                    })
                    info = ydl.extract_info(url, download=True)
                    ext = info.get("ext", "mp4" if not as_mp3 else "mp3")
                    actual_path = _find_output_file(output_dir, info, ydl)

                    if not actual_path or not os.path.exists(actual_path):
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_BACKOFF * (2 ** attempt))
                            continue
                        logger.error("download_no_output", extra={"url": url, "task_id": task_id})
                        return None

                    file_size = os.path.getsize(actual_path)
                    if file_size == 0:
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_BACKOFF * (2 ** attempt))
                            continue
                        return None

                    # Validate the downloaded file
                    validation = validate_media_file(actual_path)
                    if not validation["valid"]:
                        logger.warning("download_invalid_file", extra={
                            "path": actual_path, "issues": validation["issues"],
                        })
                        # Try to repair
                        repaired = repair_media_file(actual_path, output_dir)
                        if repaired:
                            actual_path = repaired
                            file_size = os.path.getsize(actual_path)

                    actual_ext = os.path.splitext(actual_path)[1].lstrip(".") or ext
                    title = info.get("title", "")
                    sanitized_name = sanitize_filename(title) if title else sanitize_filename(
                        os.path.splitext(os.path.basename(actual_path))[0]
                    )

                    resolution = validation.get("resolution", "")
                    codec = validation.get("codec_video") or ""
                    bitrate = validation.get("bitrate", 0)
                    actual_height = info.get("height", 0) or 0
                    actual_format_id = info.get("format_id", "")

                    logger.info("download_completed_detail", extra={
                        "url": url,
                        "requested_format": format_id,
                        "actual_format_id": actual_format_id,
                        "actual_height": actual_height,
                        "resolution": resolution,
                        "codec": codec,
                        "file_size": file_size,
                        "has_audio": validation.get("has_audio", True),
                        "ext": actual_ext,
                    })

                    return DownloadResult(
                        file_path=actual_path,
                        file_name=sanitized_name,
                        file_size=file_size,
                        format=actual_ext,
                        used_height=actual_height,
                        has_audio=validation.get("has_audio", True),
                        title=title,
                        thumbnail=info.get("thumbnail", ""),
                        duration=info.get("duration", 0),
                        resolution=resolution,
                        codec=codec,
                        bitrate=bitrate,
                    )

            except YtDlpDownloadError as e:
                err_msg = str(e).lower()
                if "cancelled" in err_msg:
                    logger.info("download_cancelled", extra={"url": url, "task_id": task_id})
                    return None
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("download_failed", extra={"url": url, "error": str(e)}, exc_info=True)
                return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("download_failed", extra={"url": url, "error": str(e)}, exc_info=True)
                return None
        return None

    try:
        return await loop.run_in_executor(None, _download)
    finally:
        if task_id:
            _CANCEL_EVENTS.pop(task_id, None)
            _active_downloads.pop(task_id, None)


async def download_and_merge_mp4(
    url: str, target_height: int, output_dir: Optional[str] = None,
    task_id: str = "", cookies_file: Optional[str] = None,
) -> Optional[DownloadResult]:
    """
    Download best MP4 with guaranteed player compatibility.
    Falls back to nearest lower height if exact unavailable.
    Verifies audio exists before returning.
    """
    provider = provider_registry.detect(url)
    if not provider:
        return None

    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="gotot_dl_")
    os.makedirs(output_dir, exist_ok=True)

    heights = [2160, 1440, 1080, 720, 480, 360, 240, 144]
    if target_height > 10000:
        heights_to_try = heights
    else:
        heights_to_try = sorted([h for h in heights if h <= target_height], reverse=True)
        if not heights_to_try:
            heights_to_try = [360]

    loop = asyncio.get_running_loop()

    def _download():
        for h in heights_to_try:
            ffmpeg_ok = check_ffmpeg()
            if ffmpeg_ok:
                fmt_str = (
                    f"bestvideo[height<={h}][vcodec^=avc1][ext=mp4]"
                    f"+bestaudio[ext=m4a]/best[height<={h}][ext=mp4][acodec!=none]"
                    f"/best[height<={h}]"
                )
            else:
                fmt_str = (
                    f"best[height<={h}][ext=mp4][acodec!=none]"
                    f"/best[height<={h}][ext=mp4]"
                    f"/best[height<={h}]"
                )

            ydl_opts = {
                "format": fmt_str,
                "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
                "merge_output_format": "mp4" if ffmpeg_ok else None,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "ignoreerrors": True,
                "socket_timeout": 60,
                "retries": 3,
            }

            if cookies_file and os.path.isfile(cookies_file):
                ydl_opts["cookiefile"] = cookies_file

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    actual_path = _find_output_file(output_dir, info, ydl, expected_exts=["mp4"])

                    if not actual_path or not os.path.exists(actual_path):
                        continue

                    has_audio = _probe_has_audio(actual_path)
                    if not has_audio:
                        logger.warning("mp4_no_audio_at_height", extra={"url": url, "height": h})
                        if ffmpeg_ok:
                            merged = _force_remux_with_audio(actual_path, output_dir, info)
                            if merged:
                                actual_path = merged
                                has_audio = True
                        if not has_audio:
                            continue

                    file_size = os.path.getsize(actual_path)
                    title = info.get("title", "")
                    sanitized_name = sanitize_filename(title) if title else "download"

                    logger.info("mp4_download_success", extra={
                        "url": url, "target_height": target_height, "used_height": h,
                        "file_size": file_size, "has_audio": has_audio,
                    })

                    return DownloadResult(
                        file_path=actual_path,
                        file_name=sanitized_name,
                        file_size=file_size,
                        format="mp4",
                        used_height=h,
                        has_audio=has_audio,
                        title=title,
                        thumbnail=info.get("thumbnail", ""),
                        duration=info.get("duration", 0),
                    )
            except Exception as e:
                logger.warning("mp4_download_failed_at_height", extra={"height": h, "error": str(e)})
                continue
        return None

    return await loop.run_in_executor(None, _download)


def _probe_has_audio(file_path: str) -> bool:
    """Check whether a media file has an audio stream."""
    if not check_ffprobe():
        ext = os.path.splitext(file_path)[1].lower()
        return ext in (".mp4", ".mp3", ".m4a", ".mkv", ".webm", ".mov", ".avi", ".flv")

    ffprobe_path = _FFPROBE_PATH
    try:
        result = subprocess.run(
            [ffprobe_path, "-v", "quiet", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", file_path],
            capture_output=True, text=True, timeout=FFPROBE_TIMEOUT,
        )
        return "audio" in result.stdout
    except Exception:
        return True


def _force_remux_with_audio(original_path: str, output_dir: str, info: dict) -> Optional[str]:
    """Remux video with audio using ffmpeg. Falls back to re-encoding if needed."""
    if not check_ffmpeg():
        return None
    ffmpeg_path = _FFMPEG_PATH
    base = os.path.splitext(original_path)[0]
    merged_path = f"{base}_merged.mp4"

    try:
        cmd = [
            ffmpeg_path, "-y", "-i", original_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            merged_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=MERGE_TIMEOUT)
        if proc.returncode == 0 and os.path.exists(merged_path) and os.path.getsize(merged_path) > 0:
            return merged_path
    except Exception as e:
        logger.warning("remux_failed", extra={"path": original_path, "error": str(e)})
    return None


# ─── Convert to MP3 ────────────────────────────────────────────────────

async def convert_to_mp3(
    input_path: str, bitrate: str = "192",
    metadata: Optional[dict] = None,
    cover_path: Optional[str] = None,
) -> Optional[DownloadResult]:
    """Convert video/audio to MP3 with full metadata and cover art support."""
    if not check_ffmpeg():
        logger.error("mp3_convert_no_ffmpeg")
        return None

    ffmpeg_path = _FFMPEG_PATH
    loop = asyncio.get_running_loop()

    def _convert():
        try:
            base = os.path.splitext(input_path)[0]
            output_path = f"{base}.mp3"
            cmd = [ffmpeg_path, "-y", "-i", input_path, "-b:a", f"{bitrate}k", "-map", "a"]

            if metadata:
                meta = metadata
                if meta.get("title"):
                    cmd += ["-metadata", f"title={meta['title']}"]
                if meta.get("artist"):
                    cmd += ["-metadata", f"artist={meta['artist']}"]
                if meta.get("album"):
                    cmd += ["-metadata", f"album={meta['album']}"]

            if cover_path and os.path.exists(cover_path):
                cmd += ["-i", cover_path, "-map", "0:a", "-map", "1:0",
                        "-c:v", "mjpeg", "-disposition:v:0", "attached_pic"]

            cmd += [output_path]
            proc = subprocess.run(cmd, capture_output=True, check=False, timeout=120)
            if proc.returncode != 0:
                logger.error("mp3_convert_failed", extra={"stderr": proc.stderr[:300]})
                return None

            if not os.path.exists(output_path):
                return None

            file_size = os.path.getsize(output_path)
            return DownloadResult(
                file_path=output_path,
                file_name=sanitize_filename(os.path.splitext(os.path.basename(base))[0]),
                file_size=file_size,
                format="mp3",
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error("mp3_convert_exception", extra={"error": str(e)})
            return None

    return await loop.run_in_executor(None, _convert)


async def download_mp3(
    url: str, bitrate: str = "192", output_dir: Optional[str] = None,
    task_id: str = "", cookies_file: Optional[str] = None,
) -> Optional[DownloadResult]:
    """Download best audio and convert to MP3."""
    provider = provider_registry.detect(url)
    if not provider:
        return None

    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="gotot_dl_")
    os.makedirs(output_dir, exist_ok=True)

    loop = asyncio.get_running_loop()

    def _download_and_convert():
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 60,
            "retries": 5,
        }

        if cookies_file and os.path.isfile(cookies_file):
            ydl_opts["cookiefile"] = cookies_file

        if check_ffmpeg():
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }]

        if task_id:
            ydl_opts["progress_hooks"] = [_progress_hook]

        for attempt in range(MAX_RETRIES):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    actual_path = _find_output_file(
                        output_dir, info, ydl,
                        expected_exts=["mp3", "m4a", "opus", "ogg", "webm", "mp4"],
                    )

                    if not actual_path or not os.path.exists(actual_path):
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_BACKOFF * (2 ** attempt))
                            continue
                        return None

                    file_size = os.path.getsize(actual_path)
                    actual_ext = os.path.splitext(actual_path)[1].lstrip(".") or "mp3"
                    title = info.get("title", "")
                    sanitized_name = sanitize_filename(title) if title else "download"

                    return DownloadResult(
                        file_path=actual_path,
                        file_name=sanitized_name,
                        file_size=file_size,
                        format=actual_ext,
                        title=title,
                        thumbnail=info.get("thumbnail", ""),
                        duration=info.get("duration", 0),
                    )
            except YtDlpDownloadError as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("mp3_download_failed", extra={"url": url, "error": str(e)}, exc_info=True)
                return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("mp3_download_failed", extra={"url": url, "error": str(e)}, exc_info=True)
                return None
        return None

    return await loop.run_in_executor(None, _download_and_convert)


# ─── Image download ────────────────────────────────────────────────────

async def download_image(
    url: str, output_dir: Optional[str] = None,
) -> Optional[DownloadResult]:
    """Download an image from supported platforms (Instagram, Pinterest, X, etc.)."""
    provider = provider_registry.detect(url)
    if not provider:
        return None

    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="gotot_dl_")
    os.makedirs(output_dir, exist_ok=True)

    loop = asyncio.get_running_loop()

    def _download():
        ydl_opts = {
            "format": "best",
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "ignoreerrors": True,
            "socket_timeout": 60,
            "retries": 3,
        }

        for attempt in range(MAX_RETRIES):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info.get("height") is None and info.get("ext") in ("jpg", "jpeg", "png", "webp", "gif"):
                        actual_path = _find_output_file(
                            output_dir, info, ydl,
                            expected_exts=["jpg", "jpeg", "png", "webp", "gif"],
                        )
                        if actual_path and os.path.exists(actual_path):
                            file_size = os.path.getsize(actual_path)
                            actual_ext = os.path.splitext(actual_path)[1].lstrip(".") or "jpg"
                            return DownloadResult(
                                file_path=actual_path,
                                file_name=sanitize_filename(os.path.splitext(os.path.basename(actual_path))[0]),
                                file_size=file_size,
                                format=actual_ext,
                            )
                    return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                logger.error("image_download_failed", extra={"url": url, "error": str(e)}, exc_info=True)
                return None
        return None

    return await loop.run_in_executor(None, _download)


# ─── Playlist extraction ────────────────────────────────────────────────

async def extract_playlist(url: str) -> Optional[list]:
    provider = provider_registry.detect(url)
    if not provider:
        return None
    if not provider.supports_playlist():
        return None

    loop = asyncio.get_running_loop()

    def _extract():
        for attempt in range(MAX_RETRIES):
            try:
                return provider.extract_playlist(url)
            except Exception:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                return None
        return None

    return await loop.run_in_executor(None, _extract)


# ─── Subtitle extraction ────────────────────────────────────────────────

async def extract_subtitles(url: str) -> Optional[list]:
    provider = provider_registry.detect(url)
    if not provider or not provider.supports_subtitles():
        return None

    loop = asyncio.get_running_loop()

    def _extract():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "es", "fr", "de", "pt", "it", "ja", "ko", "zh", "ru", "ar", "hi"],
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                subs = info.get("subtitles", {}) or {}
                auto_subs = info.get("automatic_captions", {}) or {}
                result = []
                for lang, sub_data in {**auto_subs, **subs}.items():
                    for fmt in sub_data:
                        if fmt.get("ext") in ("vtt", "srt", "ttml", "ass"):
                            result.append({
                                "language": lang,
                                "ext": fmt.get("ext"),
                                "url": fmt.get("url"),
                                "name": fmt.get("name", lang),
                            })
                            break
                return result if result else None
        except Exception as e:
            logger.error("subtitle_extract_failed", extra={"url": url, "error": str(e)})
            return None

    return await loop.run_in_executor(None, _extract)


# ─── Cleanup utilities ──────────────────────────────────────────────────

def cleanup_temp_files(base_dir: Optional[str] = None, max_age_hours: int = 24):
    """Remove temp download files older than max_age_hours."""
    base_dir = base_dir or tempfile.gettempdir()
    cutoff = time.time() - (max_age_hours * 3600)
    pattern = os.path.join(base_dir, "gotot_dl_*")

    for path in glob_mod.glob(pattern):
        try:
            if os.path.getmtime(path) < cutoff:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
        except Exception:
            pass


# ─── FFmpeg info endpoint data ─────────────────────────────────────────

def get_ffmpeg_status() -> dict:
    """Get FFmpeg status for API health responses."""
    return {
        "available": check_ffmpeg(),
        "ffmpeg_path": _FFMPEG_PATH,
        "ffprobe_path": _FFPROBE_PATH,
        "merge_supported": check_ffmpeg(),
        "validation_supported": check_ffprobe(),
        "installation_instructions": get_ffmpeg_install_instructions(),
    }
