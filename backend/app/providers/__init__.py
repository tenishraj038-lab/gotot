from app.providers.registry import ProviderRegistry
from app.providers.base import BaseProvider
from app.providers.platforms import (
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
    SnapchatProvider,
    BilibiliProvider,
    SoundCloudProvider,
    RumbleProvider,
    OdyseeProvider,
)


def register_all_providers():
    registry = ProviderRegistry()
    for provider_cls in [
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
        SnapchatProvider,
        BilibiliProvider,
        SoundCloudProvider,
        RumbleProvider,
        OdyseeProvider,
    ]:
        registry.register(provider_cls())
    return registry


provider_registry = register_all_providers()
