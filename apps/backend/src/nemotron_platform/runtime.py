from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .artifacts import ArtifactStore
from .benchmarks import BenchmarkLoader
from .config import Settings, get_settings
from .repository import SQLiteRepository
from .services.evaluation import EvaluationService
from .services.submissions import SubmissionService
from .services.synthetic import SyntheticDataService


@dataclass(slots=True)
class RuntimeServices:
    settings: Settings
    repository: SQLiteRepository
    artifact_store: ArtifactStore
    benchmark_loader: BenchmarkLoader
    evaluation: EvaluationService
    synthetic: SyntheticDataService
    submissions: SubmissionService


@lru_cache(maxsize=1)
def get_runtime() -> RuntimeServices:
    settings = get_settings()
    repository = SQLiteRepository(settings.database_path)
    repository.initialize()
    artifact_store = ArtifactStore(settings.artifacts_root)
    artifact_store.ensure_root()
    benchmark_loader = BenchmarkLoader(settings.benchmarks_root)
    evaluation = EvaluationService(settings, repository, artifact_store, benchmark_loader)
    synthetic = SyntheticDataService(repository, artifact_store, benchmark_loader)
    submissions = SubmissionService(settings, repository, artifact_store)
    return RuntimeServices(
        settings=settings,
        repository=repository,
        artifact_store=artifact_store,
        benchmark_loader=benchmark_loader,
        evaluation=evaluation,
        synthetic=synthetic,
        submissions=submissions,
    )

