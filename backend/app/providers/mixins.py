"""
Generic extractor mixin for standard yt-dlp providers.
Reduces boilerplate across all platform providers.
"""

from typing import Optional


class StandardExtractor:
    """Mixin providing default extract_info using yt-dlp with optional auth support."""

    def extract_info(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[dict]:
        import yt_dlp
        import logging
        opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
        extract_opts = self.get_extract_opts()  # noqa: F821 - provided by BaseProvider
        if extract_opts:
            opts.update(extract_opts)
        if ydl_opts:
            opts.update(ydl_opts)
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception as e:
                logging.getLogger("gotot.download").error(
                    "extraction_failed",
                    extra={"url": url, "platform": self.name, "error": str(e)},  # noqa: F821
                    exc_info=True,
                )
                return None

    def extract_playlist(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[list]:
        return None

    def supports_playlist(self) -> bool:
        return False
