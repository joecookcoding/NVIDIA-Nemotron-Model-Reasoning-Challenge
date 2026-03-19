from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..artifacts import ArtifactStore
from ..benchmarks import BenchmarkLoader
from ..config import Settings
from ..models import (
    ExperimentCreateRequest,
    ExperimentRecord,
    PromptVariant,
    ProviderUsage,
    RunCandidate,
    RunRecord,
    RunStatus,
    TaskResult,
    VariantResult,
    WorkflowKind,
    utc_now,
)
from ..providers import ProviderFactory
from ..providers.base import ProviderRequest, ProviderResponse
from ..repository import SQLiteRepository


class EvaluationService:
    def __init__(
        self,
        settings: Settings,
        repository: SQLiteRepository,
        artifact_store: ArtifactStore,
        benchmark_loader: BenchmarkLoader,
    ):
        self.settings = settings
        self.repository = repository
        self.artifact_store = artifact_store
        self.benchmark_loader = benchmark_loader
        self.provider_factory = ProviderFactory(settings)

    def create_experiment(self, request: ExperimentCreateRequest) -> ExperimentRecord:
        experiment = ExperimentRecord(
            name=request.name,
            benchmark=request.benchmark,
            provider=request.provider or self.settings.default_provider,
            model=request.model or self.settings.openai_model,
            prompt_template=request.prompt_template,
            system_prompt=request.system_prompt,
            reasoning_mode=request.reasoning_mode,
            thinking_budget_tokens=request.thinking_budget_tokens,
            reranker_policy=request.reranker_policy,
            sample_count=request.sample_count,
            seed=request.seed,
            tags=request.tags,
            provider_options=request.provider_options,
            prompt_variants=request.prompt_variants,
            task_limit=request.task_limit,
            status=RunStatus.QUEUED,
        )
        self.repository.save_experiment(experiment)
        return experiment

    def create_run_stub(
        self,
        experiment_id: str,
        workflow_kind: WorkflowKind,
        provenance: dict[str, Any] | None = None,
    ) -> RunRecord:
        run = RunRecord(
            experiment_id=experiment_id,
            workflow_kind=workflow_kind,
            status=RunStatus.QUEUED,
            provenance=provenance or {},
        )
        experiment = self.repository.get_experiment(experiment_id)
        if experiment is not None:
            experiment.latest_run_id = run.id
            experiment.updated_at = utc_now()
            self.repository.save_experiment(experiment)
        self.repository.save_run(run)
        return run

    async def execute_run(self, run_id: str) -> RunRecord:
        run = self._require_run(run_id)
        experiment = self._require_experiment(run.experiment_id)

        run.status = RunStatus.RUNNING
        run.started_at = utc_now()
        run.updated_at = utc_now()
        self.repository.save_run(run)

        try:
            if run.workflow_kind == WorkflowKind.BASELINE_EVAL:
                run = await self._execute_baseline(experiment, run)
            elif run.workflow_kind == WorkflowKind.PROMPT_SWEEP:
                run = await self._execute_prompt_sweep(experiment, run)
            elif run.workflow_kind == WorkflowKind.RERANK:
                run = self._execute_rerank(experiment, run)
            elif run.workflow_kind == WorkflowKind.CONTINUOUS_SEARCH:
                run = await self._execute_continuous_search(experiment, run)
            else:
                raise ValueError(
                    f"Workflow kind '{run.workflow_kind.value}' is not handled by EvaluationService."
                )

            run.status = RunStatus.SUCCEEDED
        except Exception as exc:  # pragma: no cover - kept broad for orchestration safety
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
        finally:
            run.completed_at = utc_now()
            run.updated_at = utc_now()
            self.repository.save_run(run)

            experiment.status = run.status
            experiment.latest_run_id = run.id
            experiment.updated_at = utc_now()
            self.repository.save_experiment(experiment)

        return run

    async def _execute_baseline(
        self, experiment: ExperimentRecord, run: RunRecord
    ) -> RunRecord:
        variant = self._default_variant(experiment)
        evaluation = await self._evaluate_variant(experiment, run.id, variant)
        run.task_results = evaluation.task_results
        run.aggregate_score = evaluation.aggregate_score
        run.total_task_count = len(evaluation.task_results)
        run.completed_task_count = len(evaluation.task_results)
        run.latency_ms = sum(task.latency_ms for task in evaluation.task_results)
        run.token_usage = self._sum_usage(task.token_usage for task in evaluation.task_results)
        run.decision_notes = evaluation.decision_notes
        run.selected_variant_id = variant.id
        run.artifacts["summary"] = self.artifact_store.write_json(
            "runs",
            run.id,
            "summary.json",
            run.model_dump(mode="json"),
        )
        return run

    async def _execute_prompt_sweep(
        self, experiment: ExperimentRecord, run: RunRecord
    ) -> RunRecord:
        variants = experiment.prompt_variants or [self._default_variant(experiment)]
        variant_results: list[VariantResult] = []
        for variant in variants:
            result = await self._evaluate_variant(experiment, run.id, variant)
            variant_results.append(result)

        winner = max(
            variant_results,
            key=lambda item: item.aggregate_score if item.aggregate_score is not None else float("-inf"),
        )
        run.variant_results = variant_results
        run.task_results = winner.task_results
        run.aggregate_score = winner.aggregate_score
        run.selected_variant_id = winner.variant_id
        run.total_task_count = sum(len(result.task_results) for result in variant_results)
        run.completed_task_count = run.total_task_count
        run.latency_ms = sum(
            sum(task.latency_ms for task in result.task_results) for result in variant_results
        )
        run.token_usage = self._sum_usage(
            task.token_usage
            for result in variant_results
            for task in result.task_results
        )
        run.decision_notes = (
            f"Prompt sweep selected variant '{winner.variant_name}' with aggregate score "
            f"{winner.aggregate_score}."
        )
        run.artifacts["summary"] = self.artifact_store.write_json(
            "runs",
            run.id,
            "prompt_sweep_summary.json",
            run.model_dump(mode="json"),
        )
        return run

    def _execute_rerank(self, experiment: ExperimentRecord, run: RunRecord) -> RunRecord:
        source_run_id = str(run.provenance.get("source_run_id", "")).strip()
        if not source_run_id:
            raise ValueError("Rerank runs require provenance.source_run_id.")
        source_run = self._require_run(source_run_id)

        reranked_tasks: list[TaskResult] = []
        for task in source_run.task_results:
            selected_candidate, decision_notes = self._select_candidate(
                task.candidates,
                task.reference_answer,
                experiment.reranker_policy,
            )
            reranked_tasks.append(
                task.model_copy(
                    update={
                        "selected_candidate": selected_candidate,
                        "selected_score": selected_candidate.score if selected_candidate else None,
                        "decision_notes": f"Reranked from source run {source_run_id}. {decision_notes}",
                    }
                )
            )

        run.task_results = reranked_tasks
        run.aggregate_score = self._aggregate_scores(reranked_tasks)
        run.total_task_count = len(reranked_tasks)
        run.completed_task_count = len(reranked_tasks)
        run.latency_ms = source_run.latency_ms
        run.token_usage = source_run.token_usage
        run.decision_notes = f"Reranked source run '{source_run_id}'."
        run.artifacts["summary"] = self.artifact_store.write_json(
            "runs",
            run.id,
            "rerank_summary.json",
            run.model_dump(mode="json"),
        )
        return run

    async def _execute_continuous_search(
        self, experiment: ExperimentRecord, run: RunRecord
    ) -> RunRecord:
        delegate_kind = (
            WorkflowKind.PROMPT_SWEEP
            if experiment.prompt_variants
            else WorkflowKind.BASELINE_EVAL
        )
        delegated = run.model_copy(update={"workflow_kind": delegate_kind})
        delegated = (
            await self._execute_prompt_sweep(experiment, delegated)
            if delegate_kind == WorkflowKind.PROMPT_SWEEP
            else await self._execute_baseline(experiment, delegated)
        )
        run.task_results = delegated.task_results
        run.variant_results = delegated.variant_results
        run.aggregate_score = delegated.aggregate_score
        run.total_task_count = delegated.total_task_count
        run.completed_task_count = delegated.completed_task_count
        run.latency_ms = delegated.latency_ms
        run.token_usage = delegated.token_usage
        run.selected_variant_id = delegated.selected_variant_id
        run.decision_notes = (
            "Continuous search v1 delegates to the current experiment configuration "
            f"using workflow '{delegate_kind.value}'."
        )
        run.artifacts = delegated.artifacts
        return run

    async def _evaluate_variant(
        self,
        experiment: ExperimentRecord,
        run_id: str,
        variant: PromptVariant,
    ) -> VariantResult:
        tasks = self.benchmark_loader.load(experiment.benchmark, experiment.task_limit)
        provider = self.provider_factory.create(experiment.provider)

        task_results: list[TaskResult] = []
        for task in tasks:
            prompt = self._render_prompt(variant.prompt_template, task.prompt)
            response = await provider.generate(
                ProviderRequest(
                    task_id=task.task_id,
                    prompt=prompt,
                    model=experiment.model,
                    system_prompt=variant.system_prompt or experiment.system_prompt,
                    sample_count=experiment.sample_count,
                    reasoning_mode=experiment.reasoning_mode,
                    thinking_budget_tokens=experiment.thinking_budget_tokens,
                    provider_options=experiment.provider_options,
                    metadata={"benchmark": experiment.benchmark, "variant_id": variant.id},
                )
            )
            task_results.append(
                self._task_result_from_response(
                    run_id=run_id,
                    task_id=task.task_id,
                    prompt=prompt,
                    reference_answer=task.reference_answer,
                    response=response,
                    reranker_policy=experiment.reranker_policy,
                )
            )

        aggregate_score = self._aggregate_scores(task_results)
        return VariantResult(
            variant_id=variant.id,
            variant_name=variant.name,
            aggregate_score=aggregate_score,
            task_results=task_results,
            decision_notes=f"Evaluated {len(task_results)} tasks with variant '{variant.name}'.",
        )

    def _task_result_from_response(
        self,
        run_id: str,
        task_id: str,
        prompt: str,
        reference_answer: str | None,
        response: ProviderResponse,
        reranker_policy: str,
    ) -> TaskResult:
        scored_candidates = [
            candidate.model_copy(
                update={"score": self._score_candidate(candidate.text, reference_answer)}
            )
            for candidate in response.candidates
        ]
        selected_candidate, decision_notes = self._select_candidate(
            scored_candidates, reference_answer, reranker_policy
        )
        artifact_path = self.artifact_store.write_json(
            "runs",
            run_id,
            f"task_{task_id}_raw.json",
            response.raw_response,
        )

        return TaskResult(
            task_id=task_id,
            prompt=prompt,
            reference_answer=reference_answer,
            selected_candidate=selected_candidate,
            candidates=scored_candidates,
            selected_score=selected_candidate.score if selected_candidate else None,
            decision_notes=decision_notes,
            latency_ms=response.latency_ms,
            token_usage=response.usage,
            raw_response_artifact=artifact_path,
        )

    def _default_variant(self, experiment: ExperimentRecord) -> PromptVariant:
        return PromptVariant(
            id="default",
            name="Default Prompt",
            system_prompt=experiment.system_prompt,
            prompt_template=experiment.prompt_template,
            tags=["default"],
        )

    def _render_prompt(self, template: str, prompt: str) -> str:
        if "{{prompt}}" in template:
            return template.replace("{{prompt}}", prompt)
        if "{{question}}" in template:
            return template.replace("{{question}}", prompt)
        return f"{template.rstrip()}\n\n{prompt}"

    def _score_candidate(self, candidate_text: str, reference_answer: str | None) -> float | None:
        if reference_answer is None:
            return None
        normalized_candidate = candidate_text.strip().casefold()
        normalized_reference = reference_answer.strip().casefold()
        return 1.0 if normalized_candidate == normalized_reference else 0.0

    def _select_candidate(
        self,
        candidates: list[RunCandidate],
        reference_answer: str | None,
        reranker_policy: str,
    ) -> tuple[RunCandidate | None, str]:
        if not candidates:
            return None, "No candidates returned by provider."

        if reference_answer is not None and reranker_policy == "reference-aware":
            winner = max(
                candidates,
                key=lambda candidate: candidate.score if candidate.score is not None else float("-inf"),
            )
            return winner, "Selected highest-scoring candidate against local reference answer."

        if reranker_policy == "longest-answer":
            winner = max(candidates, key=lambda candidate: len(candidate.text.strip()))
            return winner, "Selected longest non-empty answer."

        return candidates[0], "Selected first candidate."

    def _aggregate_scores(self, task_results: list[TaskResult]) -> float | None:
        scores = [task.selected_score for task in task_results if task.selected_score is not None]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 4)

    def _sum_usage(self, usages: Any) -> ProviderUsage:
        total = ProviderUsage()
        for usage in usages:
            total.prompt_tokens += usage.prompt_tokens
            total.completion_tokens += usage.completion_tokens
            total.total_tokens += usage.total_tokens
        return total

    def _require_experiment(self, experiment_id: str) -> ExperimentRecord:
        experiment = self.repository.get_experiment(experiment_id)
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_id}' was not found.")
        return experiment

    def _require_run(self, run_id: str) -> RunRecord:
        run = self.repository.get_run(run_id)
        if run is None:
            raise ValueError(f"Run '{run_id}' was not found.")
        return run

