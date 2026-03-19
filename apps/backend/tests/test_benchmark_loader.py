from __future__ import annotations

from pathlib import Path
import unittest

from nemotron_platform.benchmarks import BenchmarkLoader


class BenchmarkLoaderTests(unittest.TestCase):
    def test_load_sample_benchmark(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        loader = BenchmarkLoader(repo_root / "experiments" / "benchmarks")
        tasks = loader.load("sample_reasoning")

        self.assertGreaterEqual(len(tasks), 3)
        self.assertEqual(tasks[0].task_id, "sample-1")


if __name__ == "__main__":
    unittest.main()
