import pytest
import pytest_asyncio
import os
import time
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

from app.utils.helpers import is_valid_url, detect_platform, is_domain_allowed


class TestDownloadInfoEndpoint:
    @pytest.mark.asyncio
    async def test_valid_download_info(self, client):
        with patch("app.routes.download.extract_video_info", new_callable=AsyncMock) as mock_extract:
            mock_video_info = MagicMock()
            mock_video_info.title = "Test Video"
            mock_video_info.platform = "tiktok"
            mock_video_info.duration = 120
            mock_video_info.thumbnail = "https://img.tiktok.com/thumb.jpg"
            mock_video_info.formats = [{"format_id": "22", "ext": "mp4", "height": 720}]
            mock_video_info.is_playlist = False
            mock_video_info.playlist_count = 0
            mock_extract.return_value = mock_video_info

            with patch("app.routes.download.get_cached_video_info", new_callable=AsyncMock) as mock_cache:
                mock_cache.return_value = None
                with patch("app.routes.download.set_cached_video_info", new_callable=AsyncMock) as mock_set:
                    response = await client.post("/download/info", json={"url": "https://www.tiktok.com/@user/video/123456789"})
                    assert response.status_code == 200
                    data = response.json()
                    assert data["title"] == "Test Video"
                    assert data["platform"] == "tiktok"
                    assert data["is_playlist"] is False

    @pytest.mark.asyncio
    async def test_invalid_url_format(self, client):
        response = await client.post("/download/info", json={"url": "not-a-valid-url"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_url_no_http(self, client):
        response = await client.post("/download/info", json={"url": "ftp://example.com/video"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_url(self, client):
        response = await client.post("/download/info", json={"url": ""})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsupported_domain(self, client):
        response = await client.post("/download/info", json={"url": "https://unsupported-site.com/video"})
        assert response.status_code in (400, 422)
        detail = response.json().get("detail", "")
        if isinstance(detail, list):
            detail = " ".join(str(d) for d in detail)
        assert "unsupported" in str(detail).lower() or "Unsupported" in str(detail)

    @pytest.mark.asyncio
    async def test_domain_not_allowed(self, client):
        with patch("app.utils.helpers.is_valid_url", return_value=False):
            response = await client.post("/download/info", json={"url": "https://malicious.com/video"})
            assert response.status_code == 422


class TestDownloadStartEndpoint:
    @pytest.mark.asyncio
    async def test_start_download_success(self, client):
        with patch("app.routes.download.extract_video_info", new_callable=AsyncMock) as mock_extract, \
             patch("app.routes.download.download_video", new_callable=AsyncMock) as mock_dl:

            mock_video_info = MagicMock()
            mock_video_info.title = "Test Video"
            mock_video_info.platform = "tiktok"
            mock_video_info.thumbnail = "https://img.tiktok.com/thumb.jpg"
            mock_extract.return_value = mock_video_info

            mock_result = MagicMock()
            mock_result.file_path = "/tmp/test_downloads/test_video.mp4"
            mock_result.file_name = "test_video"
            mock_result.file_size = 1048576
            mock_result.format = "mp4"
            mock_result.title = "Test Video"
            mock_result.thumbnail = ""
            mock_result.duration = 0
            mock_result.resolution = ""
            mock_result.codec = ""
            mock_result.bitrate = 0
            mock_result.has_audio = True
            mock_dl.return_value = mock_result

            with patch("os.path.exists", return_value=True), \
                 patch("os.access", return_value=True), \
                 patch("app.routes.download.validate_media_file", return_value={"valid": True, "has_video": True, "has_audio": True, "issues": []}), \
                 patch("app.routes.download.check_ffmpeg", return_value=True), \
                 patch("app.routes.download.get_cached_video_info", new_callable=AsyncMock, return_value=None), \
                 patch("app.routes.download.set_cached_video_info", new_callable=AsyncMock):

                response = await client.post("/download/start", json={
                    "url": "https://www.tiktok.com/@user/video/123456789",
                    "format_id": "22",
                })
                assert response.status_code == 200
                data = response.json()
                assert "download_id" in data
                assert data["format"] == "mp4"
                assert "download_url" in data

    @pytest.mark.asyncio
    async def test_start_download_failed(self, client):
        with patch("app.routes.download.extract_video_info", new_callable=AsyncMock) as mock_extract, \
             patch("app.routes.download.download_video", new_callable=AsyncMock) as mock_dl:

            mock_video_info = MagicMock()
            mock_video_info.title = "Test Video"
            mock_video_info.platform = "tiktok"
            mock_video_info.thumbnail = ""
            mock_extract.return_value = mock_video_info
            mock_dl.return_value = None

            response = await client.post("/download/start", json={
                "url": "https://www.tiktok.com/@user/video/123456789",
                "format_id": "22",
            })
            assert response.status_code == 500
            resp = response.json()
            if isinstance(resp["detail"], dict):
                assert "failed" in str(resp["detail"]).lower() or "download" in str(resp["detail"]).lower()
            else:
                assert "failed" in resp["detail"].lower()

    @pytest.mark.asyncio
    async def test_invalid_mp3_bitrate(self, client):
        response = await client.post("/download/start", json={
            "url": "https://www.tiktok.com/@user/video/123456789",
            "format_id": "22",
            "as_mp3": True,
            "mp3_bitrate": "999",
        })
        assert response.status_code == 422


class TestFileServeEndpoint:
    @pytest.mark.asyncio
    async def test_serve_file_not_found(self, client):
        with patch("os.path.exists", return_value=False):
            response = await client.get("/download/file/nonexistent.mp4")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_serve_file_path_traversal(self, client):
        response = await client.get("/download/file/../../../etc/passwd")
        assert response.status_code in (400, 403, 404)
        resp_json = response.json()
        assert "detail" in resp_json


class TestQueueEndpoint:
    @pytest.mark.asyncio
    async def test_queue_download(self, client):
        from app.models.database import get_db

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        async def _override_get_db():
            yield mock_session

        from app.main import app
        app.dependency_overrides[get_db] = _override_get_db

        try:
            with patch("celery_app.tasks.process_download.delay") as mock_delay:
                mock_delay.return_value = None
                response = await client.post("/download/queue", json={
                    "url": "https://www.tiktok.com/@user/video/123456789",
                    "format_id": "22",
                })
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"
                assert "task_id" in data
                assert "ws_url" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_queue_invalid_url(self, client):
        response = await client.post("/download/queue", json={
            "url": "not-a-url",
            "format_id": "22",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_queue_status(self, client):
        with patch("celery_app.tasks.get_queue_status", return_value=None):
            response = await client.get("/download/queue/test-task-id")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "version" in data
        assert "uptime_seconds" in data
        assert "ffmpeg" in data

    @pytest.mark.asyncio
    async def test_readiness(self, client):
        response = await client.get("/health/readiness")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]


class TestMetadataEndpoint:
    @pytest.mark.asyncio
    async def test_meta(self, client):
        response = await client.get("/meta")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GoTot API"
        assert "supported_platforms" in data
        assert "terms_url" in data
        assert "privacy_url" in data
        assert "dmca_url" in data


class TestContactEndpoint:
    @pytest.mark.asyncio
    async def test_contact_missing_fields(self, client):
        response = await client.post("/contact", json={})
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_contact_invalid_email(self, client):
        response = await client.post("/contact", json={
            "name": "Test",
            "email": "not-an-email",
            "subject": "Hello",
            "message": "Test message"
        })
        assert response.status_code in (400, 422)


class TestHelpers:
    def test_is_valid_url(self):
        assert is_valid_url("https://www.tiktok.com/@user/video/abc") is True
        assert is_valid_url("") is False
        assert is_valid_url("javascript:alert(1)") is False
        assert is_valid_url("file:///etc/passwd") is False

    def test_is_domain_allowed(self):
        assert is_domain_allowed("https://tiktok.com/@user/video/123", "*") is True
        assert is_domain_allowed("https://tiktok.com/@user/video/123", "tiktok.com,instagram.com") is True
        assert is_domain_allowed("https://malicious.com", "tiktok.com,instagram.com") is False


class TestFFmpegStatusEndpoint:
    @pytest.mark.asyncio
    async def test_ffmpeg_status(self, client):
        response = await client.get("/download/ffmpeg-status")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "installation_instructions" in data


class TestPlatformsEndpoint:
    @pytest.mark.asyncio
    async def test_platforms_list(self, client):
        response = await client.get("/download/platforms")
        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        assert data["total"] >= 10
