from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import BenchmarkTask


class BenchmarkLoader:
    def __init__(self, root: Path, competition_docs_root: Path | None = None):
        self.root = root
        self.competition_docs_root = competition_docs_root

    def list_available(self) -> list[str]:
        names = {path.stem for path in self.root.glob("*.jsonl")}
        names.update(self._competition_csv_benchmarks().keys())
        return sorted(names)

    def load(self, benchmark_name: str, limit: int | None = None) -> list[BenchmarkTask]:
        competition_csvs = self._competition_csv_benchmarks()
        if benchmark_name in competition_csvs:
            return self._load_competition_csv(
                benchmark_name,
                competition_csvs[benchmark_name],
                limit=limit,
            )

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

    def _competition_csv_benchmarks(self) -> dict[str, Path]:
        if self.competition_docs_root is None:
            return {}

        mapping: dict[str, Path] = {}
        train_path = self.competition_docs_root / "train.csv"
        test_path = self.competition_docs_root / "test.csv"
        if train_path.exists():
            mapping["competition_train"] = train_path
        if test_path.exists():
            mapping["competition_test"] = test_path
        return mapping

    def _load_competition_csv(
        self, benchmark_name: str, csv_path: Path, limit: int | None = None
    ) -> list[BenchmarkTask]:
        tasks: list[BenchmarkTask] = []
        split = "train" if benchmark_name == "competition_train" else "test"
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                task_id = str(row.get("id", "")).strip()
                prompt = str(row.get("prompt", "")).strip()
                answer = row.get("answer")
                reference_answer = str(answer).strip() if answer is not None else None
                if not task_id or not prompt:
                    continue
                tasks.append(
                    BenchmarkTask(
                        task_id=task_id,
                        prompt=prompt,
                        reference_answer=reference_answer if reference_answer else None,
                        metadata={
                            "source": "competition_csv",
                            "split": split,
                            "path": str(csv_path),
                        },
                    )
                )
                if limit is not None and len(tasks) >= limit:
                    break
        return tasks
