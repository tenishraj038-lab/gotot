from typing import Optional
from app.providers.base import BaseProvider


class FacebookProvider(BaseProvider):
    name = "facebook"
    display_name = "Facebook"
    color = "#1877F2"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/.+\/videos\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/watch\/?(\?v=\d+)?",
        r"(?:https?:\/\/)?(?:www\.)?fb\.watch\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/share\/v\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/reel\/\d+",
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
