from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from ..runtime import get_runtime
from .activities import generate_synthetic_dataset_activity, run_evaluation_activity
from .workflows import (
    BaselineEvalWorkflow,
    ContinuousSearchWorkflow,
    PromptSweepWorkflow,
    RerankWorkflow,
    SyntheticDataWorkflow,
)


async def main() -> None:
    runtime = get_runtime()
    client = await Client.connect(
        runtime.settings.temporal_address,
        namespace=runtime.settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=runtime.settings.temporal_task_queue,
        workflows=[
            BaselineEvalWorkflow,
            PromptSweepWorkflow,
            RerankWorkflow,
            SyntheticDataWorkflow,
            ContinuousSearchWorkflow,
        ],
        activities=[run_evaluation_activity, generate_synthetic_dataset_activity],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

