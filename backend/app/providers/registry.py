from typing import Optional, Type
from app.providers.base import BaseProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        if not provider.name:
            raise ValueError(f"Provider {type(provider).__name__} has no name")
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name)

    def detect(self, url: str) -> Optional[BaseProvider]:
        for provider in self._providers.values():
            if provider.matches(url):
                return provider
        return None

    def get_all(self) -> dict[str, BaseProvider]:
        return dict(self._providers)

    @property
    def names(self) -> list[str]:
        return list(self._providers.keys())

    @property
    def display_names(self) -> dict[str, str]:
        return {name: p.display_name for name, p in self._providers.items()}

    @property
    def colors(self) -> dict[str, str]:
        return {name: p.color for name, p in self._providers.items()}

    def all_patterns(self) -> dict[str, list[str]]:
        return {name: p.patterns for name, p in self._providers.items()}
