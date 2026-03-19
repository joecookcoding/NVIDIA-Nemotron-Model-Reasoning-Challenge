from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    repo_root: Path
    database_path: Path
    artifacts_root: Path
    benchmarks_root: Path
    competition_docs_root: Path
    openai_base_url: str
    openai_api_key: str | None
    openai_model: str
    default_provider: str
    allow_mock_provider: bool
    orchestrator_mode: str
    temporal_address: str
    temporal_namespace: str
    temporal_task_queue: str
    request_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        repo_root = Path(__file__).resolve().parents[4]
        database_path = repo_root / "artifacts" / "nemotron_platform.sqlite3"
        artifacts_root = repo_root / "artifacts"
        benchmarks_root = repo_root / "experiments" / "benchmarks"
        competition_docs_root = repo_root / "docs" / "competition"

        return cls(
            repo_root=repo_root,
            database_path=Path(os.getenv("DATABASE_PATH", database_path)),
            artifacts_root=Path(os.getenv("ARTIFACTS_ROOT", artifacts_root)),
            benchmarks_root=Path(os.getenv("BENCHMARKS_ROOT", benchmarks_root)),
            competition_docs_root=Path(
                os.getenv("COMPETITION_DOCS_ROOT", competition_docs_root)
            ),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv(
                "OPENAI_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
            ),
            default_provider=os.getenv("DEFAULT_PROVIDER", "openai-compatible"),
            allow_mock_provider=_env_flag("ALLOW_MOCK_PROVIDER", True),
            orchestrator_mode=os.getenv("ORCHESTRATOR_MODE", "inline"),
            temporal_address=os.getenv("TEMPORAL_ADDRESS", "localhost:7233"),
            temporal_namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
            temporal_task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "nemotron-evals"),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "90")),
        )


def get_settings() -> Settings:
    return Settings.from_env()
