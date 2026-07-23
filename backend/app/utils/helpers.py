"""
Utility helpers for URL validation, filename sanitization, and platform detection.
"""

import hashlib
import os
import re
import secrets
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from app.providers import provider_registry

logger = logging.getLogger("gotot.helpers")

# Block suspicious patterns to prevent SSRF and command injection
_BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "javascript", "vbscript"}
_BLOCKED_HOSTS = {"127.0.0.1", "0.0.0.0", "::1", "[::1]"}
_BLOCKED_HOST_PATTERNS = [r"^0+\.0+\.0+\.0+$", r"^169\.254\..*", r"^10\..*", r"^172\.(1[6-9]|2[0-9]|3[0-1])\..*", r"^192\.168\..*"]

# Overlong threshold
_MAX_URL_LENGTH = 4096

# Characters that aren't allowed in filenames across OSes
_ILLEGAL_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
# Reserved Windows filenames
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL",
                   "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                   "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}


def detect_platform(url: str) -> Optional[str]:
    """Detect platform from URL using provider registry."""
    provider = provider_registry.detect(url)
    if provider:
        return provider.name
    return None


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Cross-platform filename sanitization.
    - Replaces illegal characters with underscore
    - Strips leading/trailing dots and spaces
    - Handles reserved Windows names
    - Truncates to max_length
    """
    if not name or not name.strip():
        return "download"

    # Normalize unicode
    try:
        name = name.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        name = "download"

    # Replace illegal characters
    name = re.sub(_ILLEGAL_FILENAME_CHARS, "_", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name)
    # Collapse underscores
    name = re.sub(r"_+", "_", name)
    # Strip leading/trailing dots, spaces, and underscores
    name = name.strip("._ ")
    # Remove leading dots
    name = re.sub(r'^\.+', '', name)
    # Truncate
    name = name[:max_length]
    # Strip again after truncation
    name = name.strip("._ ")

    # Check reserved Windows names
    upper = name.upper()
    for reserved in _RESERVED_NAMES:
        if upper == reserved or upper.startswith(reserved + "."):
            name = f"_{name}"

    if not name:
        name = "download"
    return name


def is_valid_url(url: str) -> bool:
    """
    Validate URL format and prevent SSRF/command injection vectors.
    """
    if not url or not isinstance(url, str):
        return False
    if len(url) > _MAX_URL_LENGTH:
        return False

    # Block null bytes and control characters
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', url):
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Must be http or https
    if parsed.scheme.lower() not in ("http", "https"):
        return False

    hostname = parsed.hostname or ""
    if not hostname:
        return False

    # Block local/private IPs
    host_lower = hostname.lower()
    if host_lower in _BLOCKED_HOSTS:
        return False

    for pattern in _BLOCKED_HOST_PATTERNS:
        if re.match(pattern, host_lower):
            return False

    # Standard URL regex validation
    regex = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d{1,5})?"
        r"(?:/?|[/?]\S*)$",
        re.IGNORECASE,
    )
    return bool(regex.match(url))


def is_domain_allowed(url: str, allowed_domains: str = "*") -> bool:
    """Check if a URL's domain is in the allowlist."""
    if allowed_domains.strip() == "*":
        return True
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return False
    if not hostname:
        return False
    allowed = [d.strip().lower() for d in allowed_domains.split(",") if d.strip()]
    if not allowed:
        return True
    for domain in allowed:
        if hostname == domain or hostname.endswith("." + domain):
            return True
    return False


def generate_secure_download_id() -> str:
    """Generate a cryptographically secure download identifier."""
    return secrets.token_urlsafe(32)


def generate_task_id() -> str:
    """Generate a unique task identifier for queued downloads."""
    return str(uuid.uuid4())


def hash_filename(filename: str) -> str:
    """Create a short hash for deduplication."""
    return hashlib.sha256(filename.encode("utf-8")).hexdigest()[:16]


def utcnow() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


def is_safe_path(base_dir: str, file_path: str) -> bool:
    """Ensure a file path is within the base directory (prevent path traversal)."""
    base = os.path.realpath(os.path.abspath(base_dir))
    target = os.path.realpath(os.path.abspath(file_path))
    return target.startswith(base)


def make_unique_filename(directory: str, filename: str, ext: str = "") -> str:
    """Ensure a filename is unique by appending a counter if needed."""
    base_name = sanitize_filename(filename)
    full_ext = f".{ext.lstrip('.')}" if ext else ""
    candidate = f"{base_name}{full_ext}"
    full_path = os.path.join(directory, candidate)
    if not os.path.exists(full_path):
        return candidate

    cnt = 1
    while True:
        candidate = f"{base_name}_{cnt}{full_ext}"
        full_path = os.path.join(directory, candidate)
        if not os.path.exists(full_path):
            return candidate
        cnt += 1
        if cnt > 1000:
            # fallback: use timestamp
            ts = int(datetime.now(timezone.utc).timestamp())
            return f"{base_name}_{ts}{full_ext}"
