from __future__ import annotations

import asyncio
from typing import Protocol

from temporalio.client import Client

from ..config import Settings
from ..models import WorkflowKind
from .evaluation import EvaluationService


class WorkflowLauncher(Protocol):
    async def launch(self, workflow_kind: WorkflowKind, run_id: str) -> str:
        raise NotImplementedError


class InlineWorkflowLauncher:
    def __init__(self, evaluation_service: EvaluationService):
        self.evaluation_service = evaluation_service

    async def launch(self, workflow_kind: WorkflowKind, run_id: str) -> str:
        del workflow_kind
        asyncio.create_task(self.evaluation_service.execute_run(run_id))
        return run_id


class TemporalWorkflowLauncher:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def launch(self, workflow_kind: WorkflowKind, run_id: str) -> str:
        from ..temporal.workflows import (
            BaselineEvalWorkflow,
            ContinuousSearchWorkflow,
            PromptSweepWorkflow,
            RerankWorkflow,
            SyntheticDataWorkflow,
        )

        workflow_map = {
            WorkflowKind.BASELINE_EVAL: BaselineEvalWorkflow.run,
            WorkflowKind.PROMPT_SWEEP: PromptSweepWorkflow.run,
            WorkflowKind.RERANK: RerankWorkflow.run,
            WorkflowKind.SYNTHETIC_DATA: SyntheticDataWorkflow.run,
            WorkflowKind.CONTINUOUS_SEARCH: ContinuousSearchWorkflow.run,
        }
        workflow_fn = workflow_map[workflow_kind]

        client = await Client.connect(
            self.settings.temporal_address,
            namespace=self.settings.temporal_namespace,
        )
        handle = await client.start_workflow(
            workflow_fn,
            run_id,
            id=f"{workflow_kind.value}-{run_id}",
            task_queue=self.settings.temporal_task_queue,
        )
        return handle.id


def build_workflow_launcher(
    settings: Settings, evaluation_service: EvaluationService
) -> WorkflowLauncher:
    if settings.orchestrator_mode == "temporal":
        return TemporalWorkflowLauncher(settings)
    return InlineWorkflowLauncher(evaluation_service)

