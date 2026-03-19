from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from ..models import ProviderUsage, ReasoningMode, RunCandidate


class ProviderRequest(BaseModel):
    task_id: str
    prompt: str
    model: str
    system_prompt: str | None = None
    sample_count: int = 1
    reasoning_mode: ReasoningMode = ReasoningMode.AUTO
    thinking_budget_tokens: int | None = None
    provider_options: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    candidates: list[RunCandidate] = Field(default_factory=list)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    latency_ms: int = 0
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ModelProvider(Protocol):
    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

