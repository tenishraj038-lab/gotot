import pytest
from app.utils.helpers import generate_task_id, is_valid_url, detect_platform


class TestQueueHelpers:
    def test_generate_task_id(self):
        task_id = generate_task_id()
        assert task_id is not None
        assert len(task_id) > 0
        # UUID format
        parts = str(task_id).split("-")
        assert len(parts) == 5

    def test_unique_task_ids(self):
        ids = {generate_task_id() for _ in range(100)}
        assert len(ids) == 100

    def test_is_valid_url_https(self):
        assert is_valid_url("https://www.tiktok.com/@user/video/abc123") is True

    def test_is_valid_url_http(self):
        assert is_valid_url("http://example.com/video") is True

    def test_is_valid_url_invalid(self):
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("") is False
        assert is_valid_url("ftp://example.com") is False

    def test_detect_platform_returns_string(self):
        result = detect_platform("https://www.tiktok.com/@user/video/123456")
        assert result == "tiktok"
        assert isinstance(result, str)

    def test_detect_platform_returns_none(self):
        assert detect_platform("https://example.com") is None
