from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nemotron_platform.models import ExperimentRecord, RunRecord, WorkflowKind
from nemotron_platform.repository import SQLiteRepository


class RepositoryTests(unittest.TestCase):
    def test_round_trip_experiment_and_run(self) -> None:
        with TemporaryDirectory() as tmpdir:
            repository = SQLiteRepository(Path(tmpdir) / "test.sqlite3")
            repository.initialize()

            experiment = ExperimentRecord(name="round-trip", provider="mock", model="mock")
            repository.save_experiment(experiment)
            run = RunRecord(experiment_id=experiment.id, workflow_kind=WorkflowKind.BASELINE_EVAL)
            repository.save_run(run)

            loaded_experiment = repository.get_experiment(experiment.id)
            loaded_run = repository.get_run(run.id)

            self.assertIsNotNone(loaded_experiment)
            self.assertIsNotNone(loaded_run)
            self.assertEqual(loaded_experiment.name, "round-trip")
            self.assertEqual(loaded_run.workflow_kind, WorkflowKind.BASELINE_EVAL)


if __name__ == "__main__":
    unittest.main()

