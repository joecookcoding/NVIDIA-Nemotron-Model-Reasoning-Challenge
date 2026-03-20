from __future__ import annotations

from pathlib import Path
import unittest

from nemotron_platform.benchmarks import BenchmarkLoader


class BenchmarkLoaderTests(unittest.TestCase):
    def test_load_sample_benchmark(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        loader = BenchmarkLoader(
            repo_root / "experiments" / "benchmarks",
            competition_docs_root=repo_root / "docs",
        )
        tasks = loader.load("sample_reasoning")

        self.assertGreaterEqual(len(tasks), 3)
        self.assertEqual(tasks[0].task_id, "sample-1")

    def test_load_competition_train_csv(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        loader = BenchmarkLoader(
            repo_root / "experiments" / "benchmarks",
            competition_docs_root=repo_root / "docs",
        )
        tasks = loader.load("competition_train", limit=2)

        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].task_id, "00066667")
        self.assertEqual(tasks[0].reference_answer, "10010111")
        self.assertEqual(tasks[0].metadata["split"], "train")

    def test_lists_competition_csv_benchmarks_when_present(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        loader = BenchmarkLoader(
            repo_root / "experiments" / "benchmarks",
            competition_docs_root=repo_root / "docs",
        )

        available = loader.list_available()

        self.assertIn("competition_train", available)
        self.assertIn("competition_test", available)


if __name__ == "__main__":
    unittest.main()
