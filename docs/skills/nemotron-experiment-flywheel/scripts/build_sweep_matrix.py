#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_sweep_matrix.py <config.json>")
        return 1

    config_path = Path(sys.argv[1]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_template = config.get("prompt_template", "{{prompt}}")
    modes = config.get("reasoning_modes", ["auto"])
    budgets = config.get("thinking_budgets", [None])

    variants = []
    for mode in modes:
        for budget in budgets:
            suffix = "default" if budget is None else f"budget-{budget}"
            variants.append(
                {
                    "id": f"{mode}-{suffix}",
                    "name": f"{mode} / {suffix}",
                    "system_prompt": "/think" if mode == "think" else "/no_think" if mode == "no_think" else None,
                    "prompt_template": base_template,
                    "tags": [mode, suffix],
                    "thinking_budget_tokens": budget,
                }
            )

    print(json.dumps(variants, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

