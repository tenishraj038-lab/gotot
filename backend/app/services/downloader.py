import asyncio
import os
import subprocess
import tempfile
from typing import Optional
import yt_dlp
from app.utils.helpers import detect_platform, sanitize_filename


class VideoInfo:
    def __init__(self, title: str, platform: str, duration: int, thumbnail: str,
                 formats: list, url: str, is_playlist: bool = False, playlist_count: int = 0):
        self.title = title
        self.platform = platform
        self.duration = duration
        self.thumbnail = thumbnail
        self.formats = formats
        self.url = url
        self.is_playlist = is_playlist
        self.playlist_count = playlist_count


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


async def extract_video_info(url: str) -> Optional[VideoInfo]:
    platform = detect_platform(url)
    if not platform:
        return None

    loop = asyncio.get_running_loop()

    def _extract():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                is_playlist = info.get("_type") == "playlist" or "entries" in info
                playlist_count = 0
                if is_playlist and "entries" in info:
                    playlist_count = len(info["entries"])
                    title = info.get("title", "playlist")
                    thumbnail = info.get("thumbnail", "")
                    duration = 0
                    formats = []
                    return VideoInfo(
                        title=title, platform=platform, duration=duration,
                        thumbnail=thumbnail, formats=formats, url=url,
                        is_playlist=True, playlist_count=playlist_count,
                    )

                formats = []
                seen = set()
                for f in info.get("formats", []):
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

                    quality_label = _get_quality_label(f)
                    filesize = f.get("filesize") or f.get("filesize_approx", 0)

                    formats.append({
                        "format_id": f.get("format_id"),
                        "ext": ext,
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

                return VideoInfo(
                    title=info.get("title", "video"),
                    platform=platform,
                    duration=info.get("duration", 0),
                    thumbnail=info.get("thumbnail", ""),
                    formats=formats,
                    url=url,
                )
            except Exception as e:
                return None

    return await loop.run_in_executor(None, _extract)


async def download_video(url: str, format_id: str, output_dir: Optional[str] = None) -> Optional[DownloadResult]:
    platform = detect_platform(url)
    if not platform:
        return None

    if not output_dir:
        output_dir = tempfile.mkdtemp()

    loop = asyncio.get_running_loop()

    def _download():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": format_id,
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
            "noplaylist": True,
        }
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
            subprocess.run(
                cmd,
                capture_output=True, check=True,
            )
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            return DownloadResult(
                file_path=output_path,
                file_name=sanitize_filename(os.path.basename(base)),
                file_size=file_size,
                format="mp3",
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return None

    return await loop.run_in_executor(None, _convert)


async def extract_playlist(url: str) -> Optional[list]:
    platform = detect_platform(url)
    if not platform:
        return None

    loop = asyncio.get_running_loop()

    def _extract():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "force_generic_extractor": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if "entries" not in info:
                    return None
                entries = []
                for entry in info["entries"]:
                    if entry:
                        entry_url = entry.get("url") or entry.get("webpage_url") or entry.get("ie_key", "")
                        if not entry_url and entry.get("id"):
                            entry_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        entries.append({
                            "url": entry_url,
                            "title": entry.get("title", "unknown"),
                            "duration": entry.get("duration", 0),
                            "thumbnail": entry.get("thumbnail", ""),
                            "id": entry.get("id", ""),
                        })
                return entries
            except Exception:
                return None

    return await loop.run_in_executor(None, _extract)


async def extract_subtitles(url: str) -> Optional[list]:
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
