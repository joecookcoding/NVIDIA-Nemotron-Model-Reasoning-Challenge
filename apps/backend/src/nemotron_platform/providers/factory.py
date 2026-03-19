from __future__ import annotations

from ..config import Settings
from .base import ModelProvider
from .mock import MockModelProvider
from .openai_compatible import OpenAICompatibleProvider


class ProviderFactory:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create(self, provider_name: str) -> ModelProvider:
        normalized = provider_name.strip().lower()
        if normalized == "mock":
            return MockModelProvider()
        if normalized in {"openai-compatible", "openai_compatible", "openai"}:
            return OpenAICompatibleProvider(self.settings)
        raise ValueError(f"Unsupported provider '{provider_name}'.")

