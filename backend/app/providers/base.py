import re
from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseProvider(ABC):
    name: str = ""
    display_name: str = ""
    color: str = "#666666"
    patterns: list[str] = []

    def __init__(self):
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def matches(self, url: str) -> bool:
        for pattern in self._compiled_patterns:
            if pattern.match(url):
                return True
        return False

    @abstractmethod
    def extract_info(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[dict]:
        ...

    @abstractmethod
    def extract_playlist(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[list]:
        ...

    def get_download_opts(self, format_id: str, output_dir: str) -> dict:
        return {
            "format": format_id,
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

    def supports_playlist(self) -> bool:
        return True

    def supports_subtitles(self) -> bool:
        return True

    def supports_audio_extraction(self) -> bool:
        return True

    def get_metadata(self, info: dict) -> dict:
        return {
            "title": info.get("title", "video"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", info.get("channel", "")),
            "upload_date": info.get("upload_date", ""),
            "description": info.get("description", "")[:500],
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "tags": info.get("tags", [])[:10],
        }
