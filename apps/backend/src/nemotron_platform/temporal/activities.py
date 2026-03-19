from __future__ import annotations

from temporalio import activity

from ..models import RunRecord, SyntheticDatasetManifest, SyntheticDatasetRequest
from ..runtime import get_runtime


@activity.defn
async def run_evaluation_activity(run_id: str) -> dict:
    runtime = get_runtime()
    result = await runtime.evaluation.execute_run(run_id)
    return result.model_dump(mode="json")


@activity.defn
def generate_synthetic_dataset_activity(payload: dict) -> dict:
    runtime = get_runtime()
    request = SyntheticDatasetRequest.model_validate(payload)
    manifest = runtime.synthetic.generate_dataset(request)
    return manifest.model_dump(mode="json")

