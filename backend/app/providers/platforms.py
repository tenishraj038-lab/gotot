from typing import Optional
from app.providers.base import BaseProvider
from app.providers.mixins import StandardExtractor


class TikTokProvider(StandardExtractor, BaseProvider):
    name = "tiktok"
    display_name = "TikTok"
    color = "#000000"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?tiktok\.com\/@[\w.-]+\/video\/\d+",
        r"(?:https?:\/\/)?vm\.tiktok\.com\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?tiktok\.com\/t\/[\w-]+",
    ]


class InstagramProvider(StandardExtractor, BaseProvider):
    name = "instagram"
    display_name = "Instagram"
    color = "#E4405F"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv|stories)\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/stories\/[\w.-]+\/\d+",
    ]

    def supports_images(self) -> bool:
        return True

    def requires_auth(self) -> bool:
        return True

    def get_auth_hint(self) -> Optional[str]:
        return "Instagram often requires login credentials. Use cookies to access private content."


class TwitterProvider(StandardExtractor, BaseProvider):
    name = "twitter"
    display_name = "Twitter / X"
    color = "#1DA1F2"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/\w+\/status\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/\w+\/status\/\d+\?s=\d+",
        r"(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/\w+\/status\/\d+\/video\/\d+",
    ]

    def requires_auth(self) -> bool:
        return True

    def get_auth_hint(self) -> Optional[str]:
        return "X/Twitter may require authentication. Import browser cookies for best results."


class FacebookProvider(StandardExtractor, BaseProvider):
    name = "facebook"
    display_name = "Facebook"
    color = "#1877F2"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/.+\/videos\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/watch\/?(\?v=\d+)?",
        r"(?:https?:\/\/)?(?:www\.)?fb\.watch\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/share\/v\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?facebook\.com\/reel\/\d+",
    ]

    def requires_auth(self) -> bool:
        return True

    def get_auth_hint(self) -> Optional[str]:
        return "Facebook often requires authentication. Import browser cookies for best results."


class RedditProvider(StandardExtractor, BaseProvider):
    name = "reddit"
    display_name = "Reddit"
    color = "#FF4500"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?reddit\.com\/r\/[\w-]+\/comments\/[\w-]+\/.+",
        r"(?:https?:\/\/)?(?:www\.)?reddit\.com\/r\/[\w-]+\/comments\/[\w-]+",
        r"(?:https?:\/\/)?v\.redd\.it\/[\w]+",
    ]


class VimeoProvider(StandardExtractor, BaseProvider):
    name = "vimeo"
    display_name = "Vimeo"
    color = "#1AB7EA"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/manage\/\d+",
        r"(?:https?:\/\/)?player\.vimeo\.com\/video\/\d+",
    ]

    def supports_playlist(self) -> bool:
        return False


class DailymotionProvider(StandardExtractor, BaseProvider):
    name = "dailymotion"
    display_name = "Dailymotion"
    color = "#0066DC"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/video\/[\w]+",
        r"(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/embed\/video\/[\w]+",
        r"(?:https?:\/\/)?dai\.ly\/[\w]+",
    ]


class TwitchProvider(StandardExtractor, BaseProvider):
    name = "twitch"
    display_name = "Twitch"
    color = "#9146FF"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?twitch\.tv\/videos\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?twitch\.tv\/\w+\/clip\/\w+",
        r"(?:https?:\/\/)?(?:www\.)?clips\.twitch\.tv\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?twitch\.tv\/\w+\/v\/\d+",
    ]


class LinkedInProvider(StandardExtractor, BaseProvider):
    name = "linkedin"
    display_name = "LinkedIn"
    color = "#0A66C2"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/.*\/video\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/feed\/update\/\d+",
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/posts\/[\w-]+-\d+",
    ]

    def requires_auth(self) -> bool:
        return True

    def get_auth_hint(self) -> Optional[str]:
        return "LinkedIn requires authentication for most content. Use browser cookies."


class PinterestProvider(StandardExtractor, BaseProvider):
    name = "pinterest"
    display_name = "Pinterest"
    color = "#BD081C"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?pinterest\.com\/pin\/[\w-]+",
        r"(?:https?:\/\/)?(?:www\.)?pinterest\.\w+\/[\w/-]+\/[\w-]+",
        r"(?:https?:\/\/)?pin\.it\/[\w-]+",
    ]

    def supports_images(self) -> bool:
        return True


class SnapchatProvider(StandardExtractor, BaseProvider):
    name = "snapchat"
    display_name = "Snapchat"
    color = "#FFFC00"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?snapchat\.com\/spotlight\/[\w-]+",
        r"(?:https?:\/\/)?story\.snapchat\.com\/[\w@\/-]+",
    ]


class BilibiliProvider(StandardExtractor, BaseProvider):
    name = "bilibili"
    display_name = "Bilibili"
    color = "#00A1D6"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?bilibili\.com\/video\/[\w]+",
        r"(?:https?:\/\/)?(?:www\.)?b23\.tv\/[\w]+",
    ]


class SoundCloudProvider(StandardExtractor, BaseProvider):
    name = "soundcloud"
    display_name = "SoundCloud"
    color = "#FF5500"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?soundcloud\.com\/[\w-]+\/[\w-]+",
        r"(?:https?:\/\/)?soundcloud\.app\.goo\.gl\/[\w]+",
    ]

    def supports_subtitles(self) -> bool:
        return False


class RumbleProvider(StandardExtractor, BaseProvider):
    name = "rumble"
    display_name = "Rumble"
    color = "#85C742"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?rumble\.com\/[\w-]+",
    ]


class OdyseeProvider(StandardExtractor, BaseProvider):
    name = "odysee"
    display_name = "Odysee"
    color = "#E50914"
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?odysee\.com\/[\w@\/\.-]+",
    ]
