import pytest
from app.utils.helpers import detect_platform, sanitize_filename


class TestDetectPlatform:
    def test_youtube(self):
        assert detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
        assert detect_platform("https://youtu.be/dQw4w9WgXcQ") == "youtube"

    def test_tiktok(self):
        assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"

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

    def test_vimeo(self):
        assert detect_platform("https://vimeo.com/123456") == "vimeo"

    def test_dailymotion(self):
        assert detect_platform("https://www.dailymotion.com/video/x7tst") == "dailymotion"

    def test_twitch(self):
        assert detect_platform("https://www.twitch.tv/videos/12345") == "twitch"

    def test_linkedin(self):
        assert detect_platform("https://www.linkedin.com/posts/user-123") == "linkedin"

    def test_pinterest(self):
        assert detect_platform("https://www.pinterest.com/pin/123456/") == "pinterest"

    def test_unknown(self):
        assert detect_platform("https://example.com/video") is None


class TestSanitizeFilename:
    def test_normal(self):
        assert sanitize_filename("My Video.mp4") == "My_Video.mp4"

    def test_special_chars(self):
        assert sanitize_filename("Vid: <test> | ok.mp4") == "Vid_test_ok.mp4"

    def test_long_name(self):
        name = "a" * 300 + ".mp4"
        result = sanitize_filename(name)
        assert len(result) <= 200
