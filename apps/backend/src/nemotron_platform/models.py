from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.utcnow()


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ReasoningMode(str, Enum):
    AUTO = "auto"
    THINK = "think"
    NO_THINK = "no_think"


class WorkflowKind(str, Enum):
    BASELINE_EVAL = "baseline_eval"
    PROMPT_SWEEP = "prompt_sweep"
    RERANK = "rerank"
    SYNTHETIC_DATA = "synthetic_data"
    CONTINUOUS_SEARCH = "continuous_search"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    VALID = "valid"
    INVALID = "invalid"


class ProviderUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class PromptVariant(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    name: str
    system_prompt: str | None = None
    prompt_template: str = "{{prompt}}"
    tags: list[str] = Field(default_factory=list)


class BenchmarkTask(BaseModel):
    task_id: str
    prompt: str
    reference_answer: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    text: str
    score: float | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    task_id: str
    prompt: str
    reference_answer: str | None = None
    selected_candidate: RunCandidate | None = None
    candidates: list[RunCandidate] = Field(default_factory=list)
    selected_score: float | None = None
    decision_notes: str = ""
    latency_ms: int = 0
    token_usage: ProviderUsage = Field(default_factory=ProviderUsage)
    raw_response_artifact: str | None = None


class VariantResult(BaseModel):
    variant_id: str
    variant_name: str
    aggregate_score: float | None = None
    task_results: list[TaskResult] = Field(default_factory=list)
    decision_notes: str = ""


class ExperimentRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    benchmark: str = "sample_reasoning"
    provider: str = "mock"
    model: str = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
    prompt_template: str = "{{prompt}}"
    system_prompt: str | None = None
    reasoning_mode: ReasoningMode = ReasoningMode.AUTO
    thinking_budget_tokens: int | None = None
    reranker_policy: str = "reference-aware"
    sample_count: int = 1
    seed: int = 7
    tags: list[str] = Field(default_factory=list)
    provider_options: dict[str, Any] = Field(default_factory=dict)
    prompt_variants: list[PromptVariant] = Field(default_factory=list)
    task_limit: int | None = None
    status: RunStatus = RunStatus.QUEUED
    latest_run_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ExperimentCreateRequest(BaseModel):
    name: str
    benchmark: str = "sample_reasoning"
    provider: str | None = None
    model: str | None = None
    prompt_template: str = "{{prompt}}"
    system_prompt: str | None = None
    reasoning_mode: ReasoningMode = ReasoningMode.AUTO
    thinking_budget_tokens: int | None = None
    reranker_policy: str = "reference-aware"
    sample_count: int = 1
    seed: int = 7
    tags: list[str] = Field(default_factory=list)
    provider_options: dict[str, Any] = Field(default_factory=dict)
    prompt_variants: list[PromptVariant] = Field(default_factory=list)
    task_limit: int | None = None
    workflow_kind: WorkflowKind = WorkflowKind.BASELINE_EVAL
    auto_start: bool = True


class ExperimentCreateResponse(BaseModel):
    experiment: ExperimentRecord
    run: "RunRecord"


class RunRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    experiment_id: str
    workflow_kind: WorkflowKind
    status: RunStatus = RunStatus.QUEUED
    aggregate_score: float | None = None
    total_task_count: int = 0
    completed_task_count: int = 0
    latency_ms: int = 0
    token_usage: ProviderUsage = Field(default_factory=ProviderUsage)
    cost_usd: float = 0.0
    task_results: list[TaskResult] = Field(default_factory=list)
    variant_results: list[VariantResult] = Field(default_factory=list)
    selected_variant_id: str | None = None
    decision_notes: str = ""
    error_message: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    experiment_id: str
    experiment_name: str
    run_id: str
    workflow_kind: WorkflowKind
    aggregate_score: float | None
    benchmark: str
    provider: str
    model: str
    tags: list[str] = Field(default_factory=list)
    updated_at: datetime


class SyntheticDatasetRequest(BaseModel):
    source_benchmark: str = "sample_reasoning"
    provider: str = "mock"
    model: str = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
    prompts_per_task: int = 2
    limit: int = 10
    include_reference_answers: bool = True
    tags: list[str] = Field(default_factory=list)


class SyntheticDatasetManifest(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    source_benchmark: str
    provider: str
    model: str
    record_count: int
    deduped_record_count: int
    output_path: str
    manifest_path: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class SubmissionValidateRequest(BaseModel):
    run_id: str | None = None
    submission_path: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)


class SubmissionValidation(BaseModel):
    valid: bool
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    inferred_columns: list[str] = Field(default_factory=list)


class SubmissionBuildRequest(BaseModel):
    experiment_id: str
    run_id: str | None = None
    version: str = "v1"


class SubmissionBundle(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    experiment_id: str
    run_id: str
    version: str
    status: SubmissionStatus = SubmissionStatus.DRAFT
    file_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    validation: SubmissionValidation
    created_at: datetime = Field(default_factory=utc_now)


class HealthResponse(BaseModel):
    status: str
    database_path: str
    artifacts_root: str
    orchestrator_mode: str
