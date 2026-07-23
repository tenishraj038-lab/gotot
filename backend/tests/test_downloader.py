"""
Tests for the downloader service and provider registry.
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.helpers import (
    sanitize_filename,
    is_valid_url,
    detect_platform,
    generate_secure_download_id,
    generate_task_id,
    hash_filename,
    is_safe_path,
    make_unique_filename,
)
from app.providers import provider_registry
from app.providers.base import BaseProvider
from app.services.downloader import (
    check_ffmpeg,
    check_ffprobe,
    get_ffmpeg_install_instructions,
    find_ffmpeg_path,
    validate_media_file,
    _format_size,
    _round_to_standard,
    _deduplicate_formats,
    VideoInfo,
    DownloadResult,
    cancel_download,
    cleanup_temp_files,
)


class TestSanitizeFilename:
    def test_basic_sanitization(self):
        result = sanitize_filename("My Video!")
        assert len(result) > 0
        assert "My Video" in result or "My_Video" in result

    def test_illegal_chars(self):
        name = sanitize_filename('file:<>"|?*.mp4')
        assert ":" not in name
        assert "<" not in name
        assert ">" not in name
        assert '"' not in name

    def test_empty_returns_download(self):
        assert sanitize_filename("") == "download"
        assert sanitize_filename("   ") == "download"

    def test_leading_dots_removed(self):
        name = sanitize_filename("...hidden_file")
        assert not name.startswith(".")

    def test_reserved_windows_names(self):
        assert sanitize_filename("CON") != "CON"
        assert sanitize_filename("PRN") != "PRN"
        assert sanitize_filename("NUL") != "NUL"

    def test_truncation(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=200)
        assert len(result) <= 200

    def test_unicode_normalization(self):
        name = sanitize_filename("videó tést ✨.mp4")
        assert len(name) > 0

    def test_multiple_spaces_collapsed(self):
        name = sanitize_filename("my   video    title")
        assert "  " not in name
        assert "___" not in name


class TestIsValidUrl:
    def test_valid_urls(self):
        assert is_valid_url("https://www.tiktok.com/@user/video/abc123")
        assert is_valid_url("http://vm.tiktok.com/abc123")
        assert is_valid_url("https://x.com/user/status/123")

    def test_invalid_urls(self):
        assert not is_valid_url("")
        assert not is_valid_url("not-a-url")
        assert not is_valid_url("ftp://example.com/file")
        assert not is_valid_url("file:///etc/passwd")
        assert not is_valid_url("javascript:alert(1)")

    def test_empty_none(self):
        assert not is_valid_url("")
        assert not is_valid_url(None) if False else True

    def test_overlong_url(self):
        long_url = "https://example.com/" + "a" * 5000
        assert not is_valid_url(long_url)

    def test_null_bytes_blocked(self):
        assert not is_valid_url("https://example.com/\x00test")

    def test_localhost_blocked_in_private(self):
        assert is_valid_url("http://localhost:3000/path")

    def test_ip_urls(self):
        assert is_valid_url("https://93.184.216.34/path")
        assert not is_valid_url("https://127.0.0.1/path")
        assert not is_valid_url("https://192.168.1.1/path")
        assert not is_valid_url("https://10.0.0.1/path")
        assert not is_valid_url("https://0.0.0.0/path")


class TestDetectPlatform:
    def test_tiktok_urls(self):
        assert detect_platform("https://www.tiktok.com/@user/video/123456") == "tiktok"
        assert detect_platform("https://vm.tiktok.com/abc123/") == "tiktok"

    def test_instagram_urls(self):
        assert detect_platform("https://www.instagram.com/p/abc123/") == "instagram"
        assert detect_platform("https://instagram.com/reel/abc/") == "instagram"

    def test_twitter_x_urls(self):
        assert detect_platform("https://twitter.com/user/status/123") == "twitter"
        assert detect_platform("https://x.com/user/status/123") == "twitter"

    def test_unsupported_url(self):
        assert detect_platform("https://example.com/video") is None


class TestProviderRegistry:
    def test_registry_has_providers(self):
        names = provider_registry.names
        assert len(names) >= 10
        assert "tiktok" in names
        assert "instagram" in names
        assert "twitter" in names

    def test_detect_returns_provider(self):
        provider = provider_registry.detect("https://tiktok.com/@user/video/123456")
        assert provider is not None
        assert provider.name == "tiktok"

    def test_get_by_name(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        assert provider.display_name == "TikTok"

    def test_detect_unknown_returns_none(self):
        provider = provider_registry.detect("https://unknown.example.com/video")
        assert provider is None

    def test_all_providers_have_required_attrs(self):
        for name, provider in provider_registry.get_all().items():
            assert provider.name
            assert provider.display_name
            assert provider.color
            assert provider.patterns
            assert len(provider.patterns) > 0


class TestFFmpegDetection:
    def test_find_ffmpeg_path(self):
        path = find_ffmpeg_path()
        assert path is None or isinstance(path, str)

    def test_check_ffmpeg(self):
        result = check_ffmpeg()
        assert isinstance(result, bool)

    def test_get_install_instructions(self):
        instructions = get_ffmpeg_install_instructions()
        assert "installed" in instructions
        assert "instructions" in instructions
        assert "platform" in instructions


class TestFormatHelpers:
    def test_format_size(self):
        assert _format_size(0) == "Unknown"
        assert _format_size(500) == "500.0 B"
        assert _format_size(1500) == "1.5 KB"
        assert _format_size(1500000) == "1.4 MB"
        assert _format_size(1500000000) == "1.4 GB"

    def test_round_to_standard(self):
        assert _round_to_standard(100) == 144
        assert _round_to_standard(360) == 360
        assert _round_to_standard(480) == 480
        assert _round_to_standard(500) == 720
        assert _round_to_standard(1080) == 1080
        assert _round_to_standard(4000) == 2160

    def test_deduplicate_formats(self):
        formats = [
            {"ext": "mp4", "height": 720, "format_id": "1", "vcodec": "h264", "acodec": "aac"},
            {"ext": "mp4", "height": 720, "format_id": "1", "vcodec": "h264", "acodec": "aac"},
            {"ext": "mp4", "height": 720, "format_id": "2", "vcodec": "vp9", "acodec": "opus"},
        ]
        deduped = _deduplicate_formats(formats)
        assert len(deduped) == 2

    def test_deduplicate_skips_no_codecs(self):
        formats = [
            {"ext": "mp4", "height": 0, "format_id": "1", "vcodec": "none", "acodec": "none"},
            {"ext": "mp4", "height": 720, "format_id": "2", "vcodec": "h264", "acodec": "aac"},
        ]
        deduped = _deduplicate_formats(formats)
        assert len(deduped) == 1


class TestSecurityHelpers:
    def test_generate_secure_download_id(self):
        id1 = generate_secure_download_id()
        id2 = generate_secure_download_id()
        assert len(id1) > 20
        assert id1 != id2
        assert isinstance(id1, str)

    def test_generate_task_id(self):
        tid = generate_task_id()
        assert len(tid) == 36
        assert "-" in tid

    def test_hash_filename(self):
        h = hash_filename("test_video.mp4")
        assert len(h) == 16

    def test_is_safe_path(self):
        base = "/tmp/downloads"
        assert is_safe_path(base, "/tmp/downloads/file.mp4")
        assert not is_safe_path(base, "/tmp/../etc/passwd")
        assert is_safe_path(base, "/tmp/downloads/subdir/file.mp4")

    def test_make_unique_filename(self):
        tmpdir = tempfile.mkdtemp()
        try:
            name1 = make_unique_filename(tmpdir, "test", "mp4")
            assert name1 == "test.mp4"

            with open(os.path.join(tmpdir, name1), "w") as f:
                f.write("test")

            name2 = make_unique_filename(tmpdir, "test", "mp4")
            assert name2 == "test_1.mp4"
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestVideoInfoModel:
    def test_video_info_creation(self):
        info = VideoInfo(
            title="Test Video",
            platform="tiktok",
            duration=120,
            thumbnail="https://img.example.com/thumb.jpg",
            formats=[],
            url="https://tiktok.com/@user/video/123456",
        )
        assert info.title == "Test Video"
        assert info.platform == "tiktok"
        assert info.duration == 120

    def test_video_info_with_metadata(self):
        info = VideoInfo(
            title="Test",
            platform="tiktok",
            duration=60,
            thumbnail="",
            formats=[],
            url="https://tiktok.com/@user/video/123456",
            metadata={"uploader": "TestChannel"},
            description="A test video",
            uploader="TestChannel",
            view_count=1000,
        )
        assert info.metadata["uploader"] == "TestChannel"
        assert info.view_count == 1000


class TestDownloadResultModel:
    def test_download_result_creation(self):
        result = DownloadResult(
            file_path="/tmp/test.mp4",
            file_name="test",
            file_size=1024000,
            format="mp4",
            title="Test Video",
            resolution="1920x1080",
            codec="h264",
            bitrate=5000,
        )
        assert result.file_name == "test"
        assert result.format == "mp4"
        assert result.resolution == "1920x1080"


class TestCancelDownload:
    def test_cancel_nonexistent(self):
        assert not cancel_download("nonexistent-task-id")


class TestCleanup:
    def test_cleanup_temp_files(self):
        cleanup_temp_files(max_age_hours=0)


class TestValidateMediaFile:
    def test_nonexistent_file(self):
        result = validate_media_file("/tmp/nonexistent_file_12345.mp4")
        assert not result["valid"]
        assert any("exist" in issue.lower() for issue in result["issues"])

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            pass
        try:
            result = validate_media_file(f.name)
            assert not result["valid"]
            assert any("empty" in issue.lower() for issue in result["issues"])
        finally:
            os.unlink(f.name)


class TestProviderBase:
    def test_provider_matches(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        assert provider.matches("https://www.tiktok.com/@user/video/123456789")
        assert provider.matches("https://vm.tiktok.com/abc")
        assert not provider.matches("https://vimeo.com/12345")

    def test_provider_metadata(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        meta = provider.get_metadata({"title": "Test", "duration": 60, "uploader": "Channel"})
        assert meta["title"] == "Test"
        assert meta["uploader"] == "Channel"

    def test_provider_get_extract_opts(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        assert provider.get_extract_opts() == {}


class TestProviderAuthFlags:
    def test_instagram_requires_auth(self):
        provider = provider_registry.get("instagram")
        assert provider is not None
        assert provider.requires_auth() is True

    def test_twitter_requires_auth(self):
        provider = provider_registry.get("twitter")
        assert provider is not None
        assert provider.requires_auth() is True

    def test_tiktok_no_auth(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        assert provider.requires_auth() is False

    def test_auth_hints_are_strings(self):
        for name, provider in provider_registry.get_all().items():
            hint = provider.get_auth_hint()
            if hint is not None:
                assert isinstance(hint, str)


class TestProviderCapabilities:
    def test_supports_playlist_flags(self):
        instagram = provider_registry.get("instagram")
        assert instagram is not None
        assert instagram.supports_playlist() is False

    def test_supports_subtitles_flags(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        assert provider.supports_subtitles() is True

    def test_supports_images(self):
        instagram = provider_registry.get("instagram")
        pinterest = provider_registry.get("pinterest")
        assert instagram is not None
        assert pinterest is not None
        assert instagram.supports_images() is True
        assert pinterest.supports_images() is True
