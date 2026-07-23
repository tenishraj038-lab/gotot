import pytest
from app.providers import provider_registry


class TestProviderRegistry:
    def test_all_platforms_registered(self):
        names = provider_registry.names
        expected = ["tiktok", "instagram", "twitter", "facebook",
                    "reddit", "vimeo", "dailymotion", "twitch", "linkedin", "pinterest"]
        for name in expected:
            assert name in names, f"{name} not registered"

    def test_detect_tiktok(self):
        provider = provider_registry.detect("https://www.tiktok.com/@user/video/123")
        assert provider is not None
        assert provider.name == "tiktok"

    def test_detect_tiktok_vm(self):
        provider = provider_registry.detect("https://vm.tiktok.com/abc123/")
        assert provider is not None
        assert provider.name == "tiktok"

    def test_detect_instagram_reel(self):
        provider = provider_registry.detect("https://www.instagram.com/reel/ABC123/")
        assert provider is not None
        assert provider.name == "instagram"

    def test_detect_instagram_post(self):
        provider = provider_registry.detect("https://www.instagram.com/p/ABC123/")
        assert provider is not None
        assert provider.name == "instagram"

    def test_detect_twitter(self):
        provider = provider_registry.detect("https://twitter.com/user/status/123")
        assert provider is not None
        assert provider.name == "twitter"

    def test_detect_x(self):
        provider = provider_registry.detect("https://x.com/user/status/123")
        assert provider is not None
        assert provider.name == "twitter"

    def test_detect_facebook_watch(self):
        provider = provider_registry.detect("https://www.facebook.com/watch?v=123")
        assert provider is not None
        assert provider.name == "facebook"

    def test_detect_fb_watch(self):
        provider = provider_registry.detect("https://fb.watch/abc/")
        assert provider is not None
        assert provider.name == "facebook"

    def test_detect_reddit(self):
        provider = provider_registry.detect("https://www.reddit.com/r/sub/comments/abc/video.mp4")
        assert provider is not None
        assert provider.name == "reddit"

    def test_detect_vimeo(self):
        provider = provider_registry.detect("https://vimeo.com/123456")
        assert provider is not None
        assert provider.name == "vimeo"

    def test_detect_dailymotion(self):
        provider = provider_registry.detect("https://www.dailymotion.com/video/x7tst")
        assert provider is not None
        assert provider.name == "dailymotion"

    def test_detect_twitch(self):
        provider = provider_registry.detect("https://www.twitch.tv/videos/12345")
        assert provider is not None
        assert provider.name == "twitch"

    def test_detect_linkedin(self):
        provider = provider_registry.detect("https://www.linkedin.com/posts/user-123")
        assert provider is not None
        assert provider.name == "linkedin"

    def test_detect_pinterest(self):
        provider = provider_registry.detect("https://www.pinterest.com/pin/123456/")
        assert provider is not None
        assert provider.name == "pinterest"

    def test_detect_unknown(self):
        provider = provider_registry.detect("https://example.com/video")
        assert provider is None

    def test_playlist_support(self):
        provider = provider_registry.get("tiktok")
        assert provider is not None
        assert provider.supports_playlist() is False

    def test_provider_names_and_colors(self):
        names = provider_registry.display_names
        colors = provider_registry.colors
        assert names["tiktok"] == "TikTok"
        assert colors["tiktok"] == "#000000"
        assert names["twitter"] == "Twitter / X"
        assert colors["twitter"] == "#1DA1F2"

    def test_all_patterns_present(self):
        patterns = provider_registry.all_patterns()
        assert len(patterns) >= 10
        for name in provider_registry.names:
            assert name in patterns
            assert len(patterns[name]) > 0
