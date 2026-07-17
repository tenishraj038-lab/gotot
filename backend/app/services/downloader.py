import asyncio
import os
import subprocess
import tempfile
from typing import Optional

import yt_dlp

from app.providers import provider_registry
from app.utils.helpers import sanitize_filename


class VideoInfo:
    def __init__(self, title: str, platform: str, duration: int, thumbnail: str,
                 formats: list, url: str, is_playlist: bool = False, playlist_count: int = 0,
                 metadata: Optional[dict] = None):
        self.title = title
        self.platform = platform
        self.duration = duration
        self.thumbnail = thumbnail
        self.formats = formats
        self.url = url
        self.is_playlist = is_playlist
        self.playlist_count = playlist_count
        self.metadata = metadata or {}


class DownloadResult:
    def __init__(self, file_path: str, file_name: str, file_size: int, format: str):
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.format = format


def _format_size(size_bytes: int) -> str:
    if not size_bytes:
        return "Unknown"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _deduplicate_formats(formats: list) -> list:
    seen = set()
    result = []
    for f in formats:
        vcodec = f.get("vcodec", "")
        acodec = f.get("acodec", "")
        has_video = vcodec != "none"
        has_audio = acodec != "none"
        if not has_video and not has_audio:
            continue
        height = f.get("height")
        ext = f.get("ext", "mp4")
        key = f"{ext}_{height}_{f.get('format_id')}"
        if key in seen:
            continue
        seen.add(key)
        result.append(f)
    return result


def _get_quality_label(f: dict) -> str:
    ext = f.get("ext", "mp4")
    height = f.get("height")
    vcodec = f.get("vcodec", "")
    acodec = f.get("acodec", "")
    abr = f.get("abr", 0)

    if vcodec == "none" or (acodec != "none" and vcodec == "none"):
        bitrate = int(abr) if abr else 0
        return f"M4A {bitrate}kbps" if ext == "m4a" else f"Audio {bitrate}kbps"

    if height:
        label = f"MP4 {height}p"
    elif f.get("format_note"):
        label = f"{ext.upper()} {f['format_note']}"
    else:
        label = f"{ext.upper()} {f.get('resolution', 'HD')}"

    fps = f.get("fps")
    if fps and fps > 30:
        label += f" {fps}fps"

    return label


def _format_formats(info: dict, platform: str) -> list:
    formats = []
    for f in info.get("formats", []):
        vcodec = f.get("vcodec", "")
        acodec = f.get("acodec", "")
        has_video = vcodec != "none"
        has_audio = acodec != "none"
        if not has_video and not has_audio:
            continue

        height = f.get("height")
        quality_label = _get_quality_label(f)
        filesize = f.get("filesize") or f.get("filesize_approx", 0)

        formats.append({
            "format_id": f.get("format_id"),
            "ext": ext if (ext := f.get("ext", "mp4")) else "mp4",
            "resolution": f.get("resolution") or f.get("format_note", ""),
            "height": height,
            "filesize": filesize,
            "filesize_approx": filesize,
            "filesize_human": _format_size(filesize),
            "vcodec": vcodec,
            "acodec": acodec,
            "fps": f.get("fps"),
            "abr": f.get("abr", 0),
            "tbr": f.get("tbr", 0),
            "quality_label": quality_label,
            "has_video": has_video,
            "has_audio": has_audio,
            "type": "video" if has_video and has_audio else ("video_only" if has_video else "audio"),
        })

    formats.sort(key=lambda x: (x.get("height") or 0, x.get("abr") or 0), reverse=True)
    return _deduplicate_formats(formats)


async def extract_video_info(url: str) -> Optional[VideoInfo]:
    provider = provider_registry.detect(url)
    if not provider:
        return None

    platform = provider.name
    loop = asyncio.get_running_loop()

    def _extract():
        try:
            raw_info = provider.extract_info(url)
            if not raw_info:
                return None

            is_playlist = raw_info.get("_type") == "playlist" or "entries" in raw_info
            if is_playlist and "entries" in raw_info:
                playlist_count = len(raw_info["entries"])
                return VideoInfo(
                    title=raw_info.get("title", "playlist"),
                    platform=platform,
                    duration=0,
                    thumbnail=raw_info.get("thumbnail", ""),
                    formats=[],
                    url=url,
                    is_playlist=True,
                    playlist_count=playlist_count,
                    metadata=provider.get_metadata(raw_info),
                )

            formats = _format_formats(raw_info, platform)

            return VideoInfo(
                title=raw_info.get("title", "video"),
                platform=platform,
                duration=raw_info.get("duration", 0),
                thumbnail=raw_info.get("thumbnail", ""),
                formats=formats,
                url=url,
                metadata=provider.get_metadata(raw_info),
            )
        except Exception:
            return None

    return await loop.run_in_executor(None, _extract)


async def download_video(url: str, format_id: str, output_dir: Optional[str] = None) -> Optional[DownloadResult]:
    provider = provider_registry.detect(url)
    if not provider:
        return None

    if not output_dir:
        output_dir = tempfile.mkdtemp()

    loop = asyncio.get_running_loop()

    def _download():
        ydl_opts = provider.get_download_opts(format_id, output_dir)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                ext = info.get("ext", "mp4")
                file_path_with_ext = file_path if os.path.exists(file_path) else f"{os.path.splitext(file_path)[0]}.{ext}"
                file_size = os.path.getsize(file_path_with_ext) if os.path.exists(file_path_with_ext) else 0
                return DownloadResult(
                    file_path=file_path_with_ext,
                    file_name=sanitize_filename(info.get("title", "video")),
                    file_size=file_size,
                    format=ext,
                )
            except Exception:
                return None

    return await loop.run_in_executor(None, _download)


async def convert_to_mp3(input_path: str, bitrate: str = "192") -> Optional[DownloadResult]:
    loop = asyncio.get_running_loop()

    def _convert():
        try:
            base = os.path.splitext(input_path)[0]
            output_path = f"{base}.mp3"
            cmd = [
                "ffmpeg", "-i", input_path,
                "-b:a", f"{bitrate}k",
                "-map", "a",
                "-y", output_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            return DownloadResult(
                file_path=output_path,
                file_name=sanitize_filename(os.path.basename(base)),
                file_size=file_size,
                format="mp3",
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    return await loop.run_in_executor(None, _convert)


async def extract_playlist(url: str) -> Optional[list]:
    provider = provider_registry.detect(url)
    if not provider:
        return None

    loop = asyncio.get_running_loop()

    def _extract():
        try:
            return provider.extract_playlist(url)
        except Exception:
            return None

    return await loop.run_in_executor(None, _extract)


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
            "subtitleslangs": ["en"],
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                subs = info.get("subtitles", {}) or {}
                auto_subs = info.get("automatic_captions", {}) or {}
                result = []
                for lang, sub_data in {**subs, **auto_subs}.items():
                    for fmt in sub_data:
                        if fmt.get("ext") in ("vtt", "srt", "ttml"):
                            result.append({
                                "language": lang,
                                "ext": fmt.get("ext"),
                                "url": fmt.get("url"),
                            })
                            break
                return result if result else None
            except Exception:
                return None

    return await loop.run_in_executor(None, _extract)
