import re
import uuid
from datetime import datetime, timezone
from typing import Optional

PLATFORM_PATTERNS = {
    "youtube": [
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/.+",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?youtu\.be\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/[\w-]+",
    ],
    "tiktok": [
        r"(?:https?:\/\/)?(?:www\.)?tiktok\.com\/@[\w.-]+\/video\/\d+",
        r"(?:https?:\/\/)?vm\.tiktok\.com\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?tiktok\.com\/t\/[\w-]+",
    ],
    "instagram": [
        r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv|stories)\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/stories\/[\w.-]+\/\d+",
    ],
    "twitter": [
        r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/\w+\/status\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/\w+\/status\/\d+\?s=\d+",
    ],
    "facebook": [
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/.+\/videos\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/watch\/?(\?v=\d+)?",
        r"(?:https?:\/\/)?(?:www\.)?fb\.watch\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/share\/v\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/reel\/\d+",
    ],
    "reddit": [
        r"(?:https?:\/\/)?(?:www\.)?reddit\.com\/r\/[\w-]+\/comments\/[\w-]+\/.+",
        r"(?:https?:\/\/)?(?:www\.)?reddit\.com\/r\/[\w-]+\/comments\/[\w-]+",
        r"(?:https?:\/\/)?v\.redd\.it\/[\w]+",
    ],
    "vimeo": [
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/manage\/\d+",
        r"(?:https?:\/\/)?player\.vimeo\.com\/video\/\d+",
    ],
    "dailymotion": [
        r"(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/video\/[\w]+",
        r"(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/embed\/video\/[\w]+",
        r"(?:https?:\/\/)?dai\.ly\/[\w]+",
    ],
    "twitch": [
        r"(?:https?:\/\/)?(?:www\.)?twitch\.tv\/videos\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?twitch\.tv\/\w+\/clip\/\w+",
        r"(?:https?:\/\/)?(?:www\.)?clips\.twitch\.tv\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?twitch\.tv\/\w+\/v\/\d+",
    ],
    "linkedin": [
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/.*\/video\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/feed\/update\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/posts\/[\w-]+-\d+",
    ],
    "pinterest": [
        r"(?:https?:\/\/)?(?:www\.)?pinterest\.com\/pin\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?pinterest\.\w+\/[\w/-]+\/[\w-]+",
        r"(?:https?:\/\/)?pin\.it\/[\w-]+",
    ],
}

PLATFORM_DISPLAY_NAMES = {
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "instagram": "Instagram",
    "twitter": "Twitter / X",
    "facebook": "Facebook",
    "reddit": "Reddit",
    "vimeo": "Vimeo",
    "dailymotion": "Dailymotion",
    "twitch": "Twitch",
    "linkedin": "LinkedIn",
    "pinterest": "Pinterest",
}

PLATFORM_COLORS = {
    "youtube": "#FF0000",
    "tiktok": "#000000",
    "instagram": "#E4405F",
    "twitter": "#1DA1F2",
    "facebook": "#1877F2",
    "reddit": "#FF4500",
    "vimeo": "#1AB7EA",
    "dailymotion": "#0066DC",
    "twitch": "#9146FF",
    "linkedin": "#0A66C2",
    "pinterest": "#BD081C",
}


def detect_platform(url: str) -> Optional[str]:
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return platform
    return None


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")[:200]


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(regex.match(url))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_task_id() -> str:
    return str(uuid.uuid4())
