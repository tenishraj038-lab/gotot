import re
from typing import Optional
from app.providers.base import BaseProvider


class YouTubeProvider(BaseProvider):
    name = "youtube"
    display_name = "YouTube"
    color = "#FF0000"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/.+",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?youtu\.be\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=[\w-]+",
    ]

    def extract_info(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[dict]:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "extract_flat": False, **(ydl_opts or {})}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception:
                return None

    def extract_playlist(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[list]:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "force_generic_extractor": False, **(ydl_opts or {})}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if "entries" not in info:
                    return None
                entries = []
                for entry in info["entries"]:
                    if entry:
                        entry_url = entry.get("url") or entry.get("webpage_url", "")
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
