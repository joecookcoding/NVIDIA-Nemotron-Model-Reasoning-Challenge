from __future__ import annotations

import json
from pathlib import Path

from .models import BenchmarkTask


class BenchmarkLoader:
    def __init__(self, root: Path):
        self.root = root

    def list_available(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.jsonl"))

    def load(self, benchmark_name: str, limit: int | None = None) -> list[BenchmarkTask]:
        benchmark_path = self.root / f"{benchmark_name}.jsonl"
        if not benchmark_path.exists():
            available = ", ".join(self.list_available()) or "none"
            raise FileNotFoundError(
                f"Benchmark '{benchmark_name}' was not found. Available: {available}"
            )

        tasks: list[BenchmarkTask] = []
        with benchmark_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                tasks.append(BenchmarkTask.model_validate(json.loads(line)))
                if limit is not None and len(tasks) >= limit:
                    break
        return tasks

