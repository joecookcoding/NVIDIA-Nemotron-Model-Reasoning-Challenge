from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import Settings
from ..models import ProviderUsage, ReasoningMode, RunCandidate
from .base import ProviderRequest, ProviderResponse


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        use_chat_template_thinking = bool(
            request.provider_options.get("use_chat_template_thinking", False)
        )
        system_prompt = (request.system_prompt or "").strip()
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "n": request.sample_count,
            "temperature": request.provider_options.get("temperature", 0.2),
            "max_tokens": request.provider_options.get("max_tokens", 1024),
        }

        if use_chat_template_thinking and request.reasoning_mode != ReasoningMode.AUTO:
            payload["chat_template_kwargs"] = {
                "enable_thinking": request.reasoning_mode == ReasoningMode.THINK
            }

        reasoning_payload = dict(request.provider_options.get("reasoning", {}))
        if request.thinking_budget_tokens is not None:
            reasoning_payload.setdefault("max_tokens", request.thinking_budget_tokens)
        if reasoning_payload:
            payload["reasoning"] = reasoning_payload
        if (
            request.thinking_budget_tokens is not None
            and request.provider_options.get("use_reasoning_budget_param", False)
        ):
            payload["reasoning_budget"] = request.thinking_budget_tokens

        extra_payload = request.provider_options.get("request_overrides", {})
        payload.update(extra_payload)

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        started = time.perf_counter()
        async with httpx.AsyncClient(
            base_url=self.settings.openai_base_url.rstrip("/"),
            timeout=self.settings.request_timeout_seconds,
        ) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        latency_ms = int((time.perf_counter() - started) * 1000)

        choices = data.get("choices", [])
        candidates: list[RunCandidate] = []
        for choice in choices:
            message = choice.get("message", {})
            candidates.append(
                RunCandidate(
                    text=_extract_text(message.get("content", "")),
                    finish_reason=choice.get("finish_reason"),
                    metadata={
                        "index": choice.get("index"),
                        "reasoning_mode": request.reasoning_mode.value,
                    },
                )
            )

        usage = data.get("usage", {})
        usage_model = ProviderUsage(
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            total_tokens=int(usage.get("total_tokens", 0) or 0),
        )

        return ProviderResponse(
            candidates=candidates,
            usage=usage_model,
            latency_ms=latency_ms,
            raw_response=data,
        )
