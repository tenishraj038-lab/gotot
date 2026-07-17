from app.providers.registry import ProviderRegistry
from app.providers.base import BaseProvider
from app.providers.youtube import YouTubeProvider
from app.providers.tiktok import TikTokProvider
from app.providers.instagram import InstagramProvider
from app.providers.twitter import TwitterProvider
from app.providers.facebook import FacebookProvider
from app.providers.reddit import RedditProvider
from app.providers.vimeo import VimeoProvider
from app.providers.dailymotion import DailymotionProvider
from app.providers.twitch import TwitchProvider
from app.providers.linkedin import LinkedInProvider
from app.providers.pinterest import PinterestProvider


def register_all_providers():
    registry = ProviderRegistry()
    for provider_cls in [
        YouTubeProvider,
        TikTokProvider,
        InstagramProvider,
        TwitterProvider,
        FacebookProvider,
        RedditProvider,
        VimeoProvider,
        DailymotionProvider,
        TwitchProvider,
        LinkedInProvider,
        PinterestProvider,
    ]:
        registry.register(provider_cls())
    return registry


provider_registry = register_all_providers()
