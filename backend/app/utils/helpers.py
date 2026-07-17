import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.providers import provider_registry

PLATFORM_PATTERNS = provider_registry.all_patterns()
PLATFORM_DISPLAY_NAMES = provider_registry.display_names
PLATFORM_COLORS = provider_registry.colors


def detect_platform(url: str) -> Optional[str]:
    provider = provider_registry.detect(url)
    if provider:
        return provider.name
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
