#!/usr/bin/env python3
from __future__ import annotations


def main() -> int:
    keys = [
        "ORCHESTRATOR_MODE",
        "TEMPORAL_ADDRESS",
        "TEMPORAL_NAMESPACE",
        "TEMPORAL_TASK_QUEUE",
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
    ]
    for key in keys:
        print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
