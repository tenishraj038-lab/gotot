import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.utils.helpers import (
    detect_platform, sanitize_filename, is_valid_url,
    is_domain_allowed, generate_secure_download_id, generate_task_id,
    hash_filename, utcnow,
)


class TestDetectPlatform:
    def test_tiktok(self):
        assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"
        assert detect_platform("https://vm.tiktok.com/abc123/") == "tiktok"

    def test_instagram(self):
        assert detect_platform("https://www.instagram.com/reel/ABC123/") == "instagram"
        assert detect_platform("https://www.instagram.com/p/ABC123/") == "instagram"

    def test_twitter(self):
        assert detect_platform("https://twitter.com/user/status/123") == "twitter"
        assert detect_platform("https://x.com/user/status/123") == "twitter"

    def test_facebook(self):
        assert detect_platform("https://www.facebook.com/watch?v=123") == "facebook"
        assert detect_platform("https://fb.watch/abc/") == "facebook"

    def test_reddit(self):
        assert detect_platform("https://www.reddit.com/r/sub/comments/abc/video.mp4") == "reddit"
        assert detect_platform("https://v.redd.it/abc123") == "reddit"

    def test_vimeo(self):
        assert detect_platform("https://vimeo.com/123456") == "vimeo"

    def test_dailymotion(self):
        assert detect_platform("https://www.dailymotion.com/video/x7tst") == "dailymotion"
        assert detect_platform("https://dai.ly/x7tst") == "dailymotion"

    def test_twitch(self):
        assert detect_platform("https://www.twitch.tv/videos/12345") == "twitch"
        assert detect_platform("https://clips.twitch.tv/FunnyClip") == "twitch"

    def test_linkedin(self):
        assert detect_platform("https://www.linkedin.com/posts/user-123") == "linkedin"

    def test_pinterest(self):
        assert detect_platform("https://www.pinterest.com/pin/123456/") == "pinterest"
        assert detect_platform("https://pin.it/abc123") == "pinterest"

    def test_unknown(self):
        assert detect_platform("https://example.com/video") is None
        assert detect_platform("https://some-random-site.net/watch") is None

    def test_empty_url(self):
        assert detect_platform("") is None
        assert detect_platform("not-a-url") is None


class TestIsValidUrl:
    def test_valid_urls(self):
        assert is_valid_url("https://www.tiktok.com/@user/video/abc") is True
        assert is_valid_url("http://example.com/path") is True
        assert is_valid_url("https://sub.domain.co.uk/path?q=1") is True

    def test_invalid_urls(self):
        assert is_valid_url("") is False
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("ftp://example.com") is False
        assert is_valid_url("https://") is False
        assert is_valid_url("javascript:alert(1)") is False
        assert is_valid_url("file:///etc/passwd") is False

    def test_url_too_long(self):
        url = "https://example.com/" + "a" * 5000
        assert is_valid_url(url) is False


class TestIsDomainAllowed:
    def test_wildcard(self):
        assert is_domain_allowed("https://tiktok.com/@user/video/123", "*") is True
        assert is_domain_allowed("https://any-random-site.com", "*") is True

    def test_specific_domains(self):
        domains = "tiktok.com,instagram.com"
        assert is_domain_allowed("https://tiktok.com/@user/video/123", domains) is True

    def test_blocked_domains(self):
        domains = "tiktok.com"
        assert is_domain_allowed("https://malicious-site.com", domains) is False
        assert is_domain_allowed("https://instagram.com/p/abc", domains) is False

    def test_empty_allowed_list(self):
        assert is_domain_allowed("https://tiktok.com", "") is True

    def test_invalid_url(self):
        assert is_domain_allowed("not-a-url", "tiktok.com") is False


class TestSanitizeFilename:
    def test_normal(self):
        result = sanitize_filename("My Video.mp4")
        assert "My_Video.mp4" in result or "My Video.mp4" in result

    def test_special_chars(self):
        result1 = sanitize_filename('Vid: <test> | ok.mp4')
        assert ":" not in result1
        assert "<" not in result1
        assert ">" not in result1
        assert "|" not in result1
        result2 = sanitize_filename('file"name.mp4')
        assert '"' not in result2

    def test_path_traversal(self):
        result1 = sanitize_filename("../../../etc/passwd")
        assert ".." not in result1
        result2 = sanitize_filename("/root/.ssh/id_rsa")
        assert "/" not in result2
        assert ".." not in sanitize_filename("../secret")

    def test_long_name(self):
        name = "a" * 300 + ".mp4"
        result = sanitize_filename(name)
        assert len(result) <= 200

    def test_empty_name(self):
        result = sanitize_filename("")
        assert result == "download"
        result = sanitize_filename("   ")
        assert result == "download"

    def test_dots_only(self):
        assert sanitize_filename("...") == "download"


class TestGenerateSecureDownloadId:
    def test_length_and_uniqueness(self):
        id1 = generate_secure_download_id()
        id2 = generate_secure_download_id()
        assert len(id1) == 43
        assert id1 != id2

    def test_url_safe(self):
        for _ in range(100):
            did = generate_secure_download_id()
            assert "+" not in did
            assert "/" not in did.replace("_", "")


class TestGenerateTaskId:
    def test_is_uuid(self):
        import uuid
        tid = generate_task_id()
        uuid.UUID(tid)
        assert len(tid) == 36

    def test_unique(self):
        ids = {generate_task_id() for _ in range(100)}
        assert len(ids) == 100


class TestHashFilename:
    def test_consistent(self):
        h1 = hash_filename("test.mp4")
        h2 = hash_filename("test.mp4")
        assert h1 == h2
        assert len(h1) == 16

    def test_different(self):
        h1 = hash_filename("test1.mp4")
        h2 = hash_filename("test2.mp4")
        assert h1 != h2


class TestUtcnow:
    def test_returns_datetime(self):
        from datetime import datetime
        result = utcnow()
        assert isinstance(result, datetime)
        assert result.tzinfo is not None
