from typing import Optional
from app.providers.base import BaseProvider


class VimeoProvider(BaseProvider):
    name = "vimeo"
    display_name = "Vimeo"
    color = "#1AB7EA"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/manage\/\d+",
        r"(?:https?:\/\/)?player\.vimeo\.com\/video\/\d+",
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
