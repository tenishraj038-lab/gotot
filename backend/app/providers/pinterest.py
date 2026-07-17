from typing import Optional
from app.providers.base import BaseProvider


class PinterestProvider(BaseProvider):
    name = "pinterest"
    display_name = "Pinterest"
    color = "#BD081C"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?pinterest\.com\/pin\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?pinterest\.\w+\/[\w/-]+\/[\w-]+",
        r"(?:https?:\/\/)?pin\.it\/[\w-]+",
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
        return None

    def supports_playlist(self) -> bool:
        return False
