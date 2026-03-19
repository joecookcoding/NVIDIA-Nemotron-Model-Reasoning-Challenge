from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..artifacts import ArtifactStore
from ..config import Settings
from ..models import (
    SubmissionBuildRequest,
    SubmissionBundle,
    SubmissionStatus,
    SubmissionValidateRequest,
    SubmissionValidation,
)
from ..repository import SQLiteRepository


class SubmissionService:
    def __init__(
        self,
        settings: Settings,
        repository: SQLiteRepository,
        artifact_store: ArtifactStore,
    ):
        self.settings = settings
        self.repository = repository
        self.artifact_store = artifact_store

    def validate_submission(self, request: SubmissionValidateRequest) -> SubmissionValidation:
        records = self._load_records(request)
        expected_columns = ["id", "answer"]
        issues: list[str] = []
        warnings: list[str] = []

        if not self._competition_rules_frozen():
            warnings.append(
                "Competition rules are not frozen yet; validation is using the default id/answer schema."
            )

        if not records:
            issues.append("Submission contains no records.")
            return SubmissionValidation(
                valid=False,
                issues=issues,
                warnings=warnings,
                inferred_columns=expected_columns,
            )

        record_ids: set[str] = set()
        for index, record in enumerate(records, start=1):
            missing = [column for column in expected_columns if column not in record]
            if missing:
                issues.append(f"Row {index} is missing required columns: {', '.join(missing)}.")
                continue
            record_id = str(record["id"])
            if record_id in record_ids:
                issues.append(f"Duplicate record id '{record_id}'.")
            record_ids.add(record_id)

        return SubmissionValidation(
            valid=not issues,
            issues=issues,
            warnings=warnings,
            inferred_columns=expected_columns,
        )

    def build_submission(self, request: SubmissionBuildRequest) -> SubmissionBundle:
        experiment = self.repository.get_experiment(request.experiment_id)
        if experiment is None:
            raise ValueError(f"Experiment '{request.experiment_id}' was not found.")

        run_id = request.run_id or experiment.latest_run_id
        if not run_id:
            raise ValueError("No run is available to build a submission from.")
        run = self.repository.get_run(run_id)
        if run is None:
            raise ValueError(f"Run '{run_id}' was not found.")

        records = [
            {
                "id": task.task_id,
                "answer": task.selected_candidate.text if task.selected_candidate else "",
            }
            for task in run.task_results
        ]
        validation = self.validate_submission(SubmissionValidateRequest(records=records))

        bundle = SubmissionBundle(
            experiment_id=experiment.id,
            run_id=run.id,
            version=request.version,
            file_path="",
            metadata={
                "experiment_name": experiment.name,
                "benchmark": experiment.benchmark,
                "record_count": len(records),
            },
            status=SubmissionStatus.VALID if validation.valid else SubmissionStatus.INVALID,
            validation=validation,
        )

        target_dir = self.settings.artifacts_root / "submissions" / bundle.id
        target_dir.mkdir(parents=True, exist_ok=True)
        csv_path = target_dir / "submission.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "answer"])
            writer.writeheader()
            writer.writerows(records)

        bundle.file_path = str(csv_path.relative_to(self.settings.repo_root))
        self.repository.save_submission(bundle)
        return bundle

    def _load_records(self, request: SubmissionValidateRequest) -> list[dict[str, Any]]:
        if request.records:
            return request.records

        if request.run_id:
            run = self.repository.get_run(request.run_id)
            if run is None:
                raise ValueError(f"Run '{request.run_id}' was not found.")
            return [
                {
                    "id": task.task_id,
                    "answer": task.selected_candidate.text if task.selected_candidate else "",
                }
                for task in run.task_results
            ]

        if request.submission_path:
            path = self.settings.repo_root / request.submission_path
            with path.open("r", encoding="utf-8", newline="") as handle:
                return list(csv.DictReader(handle))

        return []

    def _competition_rules_frozen(self) -> bool:
        return (self.settings.competition_docs_root / "rules_frozen.md").exists()

