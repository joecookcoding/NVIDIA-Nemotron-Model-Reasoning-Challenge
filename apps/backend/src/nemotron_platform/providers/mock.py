from __future__ import annotations

import hashlib
import time

from ..models import ProviderUsage, RunCandidate
from .base import ProviderRequest, ProviderResponse


class MockModelProvider:
    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        started = time.perf_counter()
        prompt = request.prompt.lower()

        if "2 + 2" in prompt or "2+2" in prompt:
            answers = ["4"]
        elif "capital of france" in prompt:
            answers = ["Paris"]
        elif "after c" in prompt:
            answers = ["D"]
        else:
            digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
            answers = [f"mock-{digest}"]

        candidates = [
            RunCandidate(
                text=answer,
                finish_reason="stop",
                metadata={"provider": "mock"},
            )
            for answer in answers[: max(1, request.sample_count)]
        ]

        latency_ms = int((time.perf_counter() - started) * 1000)
        usage = ProviderUsage(
            prompt_tokens=max(1, len(request.prompt.split())),
            completion_tokens=sum(max(1, len(candidate.text.split())) for candidate in candidates),
            total_tokens=max(1, len(request.prompt.split()))
            + sum(max(1, len(candidate.text.split())) for candidate in candidates),
        )

        return ProviderResponse(
            candidates=candidates,
            usage=usage,
            latency_ms=latency_ms,
            raw_response={
                "provider": "mock",
                "request": request.model_dump(mode="json"),
                "answers": [candidate.text for candidate in candidates],
            },
        )

