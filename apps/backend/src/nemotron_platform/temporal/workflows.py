from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import generate_synthetic_dataset_activity, run_evaluation_activity


@workflow.defn
class BaselineEvalWorkflow:
    @workflow.run
    async def run(self, run_id: str) -> dict:
        return await workflow.execute_activity(
            run_evaluation_activity,
            run_id,
            start_to_close_timeout=timedelta(minutes=20),
        )


@workflow.defn
class PromptSweepWorkflow:
    @workflow.run
    async def run(self, run_id: str) -> dict:
        return await workflow.execute_activity(
            run_evaluation_activity,
            run_id,
            start_to_close_timeout=timedelta(minutes=45),
        )


@workflow.defn
class RerankWorkflow:
    @workflow.run
    async def run(self, run_id: str) -> dict:
        return await workflow.execute_activity(
            run_evaluation_activity,
            run_id,
            start_to_close_timeout=timedelta(minutes=20),
        )


@workflow.defn
class SyntheticDataWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        return await workflow.execute_activity(
            generate_synthetic_dataset_activity,
            payload,
            start_to_close_timeout=timedelta(minutes=20),
        )


@workflow.defn
class ContinuousSearchWorkflow:
    @workflow.run
    async def run(self, run_id: str) -> dict:
        return await workflow.execute_activity(
            run_evaluation_activity,
            run_id,
            start_to_close_timeout=timedelta(minutes=60),
        )

