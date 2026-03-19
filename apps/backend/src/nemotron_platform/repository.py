from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import (
    ExperimentRecord,
    LeaderboardEntry,
    RunRecord,
    RunStatus,
    SubmissionBundle,
    SyntheticDatasetManifest,
)


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, default=str)


class SQLiteRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    latest_run_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    workflow_kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    aggregate_score REAL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS synthetic_datasets (
                    id TEXT PRIMARY KEY,
                    source_benchmark TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_experiment(self, experiment: ExperimentRecord) -> ExperimentRecord:
        payload = experiment.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO experiments (id, name, payload, latest_run_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    payload=excluded.payload,
                    latest_run_id=excluded.latest_run_id,
                    updated_at=excluded.updated_at
                """,
                (
                    experiment.id,
                    experiment.name,
                    _json_dump(payload),
                    experiment.latest_run_id,
                    experiment.created_at.isoformat(),
                    experiment.updated_at.isoformat(),
                ),
            )
        return experiment

    def get_experiment(self, experiment_id: str) -> ExperimentRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM experiments WHERE id = ?", (experiment_id,)
            ).fetchone()
        if row is None:
            return None
        return ExperimentRecord.model_validate_json(row["payload"])

    def list_experiments(self, limit: int = 50) -> list[ExperimentRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM experiments ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [ExperimentRecord.model_validate_json(row["payload"]) for row in rows]

    def save_run(self, run: RunRecord) -> RunRecord:
        payload = run.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (id, experiment_id, workflow_kind, status, aggregate_score, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    aggregate_score=excluded.aggregate_score,
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (
                    run.id,
                    run.experiment_id,
                    run.workflow_kind.value,
                    run.status.value,
                    run.aggregate_score,
                    _json_dump(payload),
                    run.created_at.isoformat(),
                    run.updated_at.isoformat(),
                ),
            )
        return run

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return RunRecord.model_validate_json(row["payload"])

    def list_runs(self, limit: int = 100) -> list[RunRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM runs ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [RunRecord.model_validate_json(row["payload"]) for row in rows]

    def list_leaderboard(self, limit: int = 20) -> list[LeaderboardEntry]:
        runs = [run for run in self.list_runs(limit=250) if run.status == RunStatus.SUCCEEDED]
        experiments = {experiment.id: experiment for experiment in self.list_experiments(limit=250)}
        ordered = sorted(
            runs,
            key=lambda run: (
                run.aggregate_score if run.aggregate_score is not None else float("-inf"),
                run.updated_at,
            ),
            reverse=True,
        )[:limit]

        entries: list[LeaderboardEntry] = []
        for index, run in enumerate(ordered, start=1):
            experiment = experiments.get(run.experiment_id)
            if experiment is None:
                continue
            entries.append(
                LeaderboardEntry(
                    rank=index,
                    experiment_id=experiment.id,
                    experiment_name=experiment.name,
                    run_id=run.id,
                    workflow_kind=run.workflow_kind,
                    aggregate_score=run.aggregate_score,
                    benchmark=experiment.benchmark,
                    provider=experiment.provider,
                    model=experiment.model,
                    tags=experiment.tags,
                    updated_at=run.updated_at,
                )
            )
        return entries

    def save_submission(self, bundle: SubmissionBundle) -> SubmissionBundle:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO submissions (id, experiment_id, run_id, status, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    payload=excluded.payload
                """,
                (
                    bundle.id,
                    bundle.experiment_id,
                    bundle.run_id,
                    bundle.status.value,
                    _json_dump(bundle.model_dump(mode="json")),
                    bundle.created_at.isoformat(),
                ),
            )
        return bundle

    def list_submissions(self, limit: int = 20) -> list[SubmissionBundle]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM submissions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [SubmissionBundle.model_validate_json(row["payload"]) for row in rows]

    def save_dataset_manifest(
        self, manifest: SyntheticDatasetManifest
    ) -> SyntheticDatasetManifest:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO synthetic_datasets (id, source_benchmark, payload, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload=excluded.payload
                """,
                (
                    manifest.id,
                    manifest.source_benchmark,
                    _json_dump(manifest.model_dump(mode="json")),
                    manifest.created_at.isoformat(),
                ),
            )
        return manifest

    def list_dataset_manifests(self, limit: int = 20) -> list[SyntheticDatasetManifest]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM synthetic_datasets ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [SyntheticDatasetManifest.model_validate_json(row["payload"]) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

